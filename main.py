import hashlib
import os
import secrets
import shutil
import uuid

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
import crud


app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-this"),
    same_site="lax",
    https_only=False,
)

models.Base.metadata.create_all(bind=engine)

if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return crud.get_user_by_id(db, user_id)


def require_user(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Сначала войдите в аккаунт")
    return user


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    search: str = "",
    subject: str = "Все",
    db: Session = Depends(get_db),
):
    notes = crud.get_notes(db, search, subject)
    subjects = crud.get_subjects(db)
    user = get_current_user(request, db)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notes": notes,
            "search": search,
            "subject": subject,
            "subjects": subjects,
            "user": user,
        },
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None},
    )


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()

    if len(username) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Логин должен быть минимум 3 символа"},
            status_code=400,
        )

    if len(password) < 4:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароль должен быть минимум 4 символа"},
            status_code=400,
        )

    existing = crud.get_user_by_username(db, username)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Такой логин уже занят"},
            status_code=400,
        )

    user = crud.create_user(db, username, hash_password(password))
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, username.strip())

    if not user or user.password_hash != hash_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=400,
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "user": user},
    )


@app.post("/upload")
def upload(
    request: Request,
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    original_filename = file.filename or "file"
    ext = os.path.splitext(original_filename)[1].lower()
    allowed_exts = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".webp"}

    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Разрешены только PDF, DOC, DOCX и изображения")

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join("uploads", unique_filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(
        db=db,
        title=title.strip(),
        subject=subject.strip(),
        category=category.strip(),
        filename=unique_filename,
        original_filename=original_filename,
        user_id=user.id,
    )
    return RedirectResponse("/", status_code=303)


@app.get("/download/{note_id}")
def download(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Файл не найден")

    path = os.path.join("uploads", note.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл отсутствует на сервере")

    return FileResponse(path=path, filename=note.original_filename)


@app.post("/like/{note_id}")
def like(note_id: int, db: Session = Depends(get_db)):
    note = crud.like_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Конспект не найден")
    return RedirectResponse("/", status_code=303)


@app.post("/comment/{note_id}")
def comment(
    request: Request,
    note_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    if not text.strip():
        return RedirectResponse("/", status_code=303)

    note = crud.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Конспект не найден")

    crud.add_comment(db, note_id, user.id, text)
    return RedirectResponse("/", status_code=303)
