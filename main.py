from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import SessionLocal, engine
import models, crud
import shutil, os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

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


def get_user(request: Request):
    return request.session.get("user")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db=Depends(get_db)):
    notes = crud.get_notes(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": notes,
        "user": get_user(request)
    })


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    crud.create_user(db, username, password)
    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    user = crud.get_user(db, username)
    if user and user.password == password:
        request.session["user"] = {"id": user.id, "role": user.role}
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
def upload(request: Request,
           title: str = Form(...),
           subject: str = Form(...),
           category: str = Form(...),
           file: UploadFile = File(...),
           db=Depends(get_db)):

    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    filename = file.filename
    path = f"uploads/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, filename, user["id"])
    return RedirectResponse("/", status_code=303)


@app.post("/like/{note_id}")
def like(note_id: int, db=Depends(get_db)):
    crud.like_note(db, note_id)
    return RedirectResponse("/", status_code=303)


@app.post("/comment/{note_id}")
def comment(note_id: int, text: str = Form(...), db=Depends(get_db)):
    crud.add_comment(db, note_id, text)
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db=Depends(get_db)):
    notes = crud.get_all_notes(db)
    total_notes, total_users = crud.get_stats(db)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "notes": notes,
        "total_notes": total_notes,
        "total_users": total_users
    })


@app.post("/approve/{note_id}")
def approve(note_id: int, db=Depends(get_db)):
    crud.approve_note(db, note_id)
    return RedirectResponse("/dashboard", status_code=303)
