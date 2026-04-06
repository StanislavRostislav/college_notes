from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import SessionLocal, engine
import models
import crud

import shutil
import os
import uuid
from datetime import datetime

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
def home(
    request: Request,
    search: str = "",
    subject: str = "all",
    category: str = "all",
    sort: str = "new",
    db=Depends(get_db)
):
    user = get_user(request)
    notes = crud.get_notes(db, search, subject, category, sort, user)
    subjects = crud.get_subjects(db)
    categories = crud.get_categories(db)
    top_users = crud.get_top_users(db)[:5]

    liked_note_ids = set()
    favorite_note_ids = set()

    if user:
        for note in notes:
            if crud.has_user_liked(db, note.id, user["id"]):
                liked_note_ids.add(note.id)

        favorites = crud.get_favorites(db, user["id"])
        favorite_note_ids = {fav.note_id for fav in favorites}

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notes": notes,
            "user": user,
            "search": search,
            "subject": subject,
            "category": category,
            "sort": sort,
            "subjects": subjects,
            "categories": categories,
            "top_users": top_users,
            "liked_note_ids": liked_note_ids,
            "favorite_note_ids": favorite_note_ids,
        }
    )


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request, db=Depends(get_db)):
    user = get_user(request)
    users = crud.get_top_users(db)

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": user,
            "users": users
        }
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": ""})


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    db=Depends(get_db)
):
    existing = crud.get_user(db, username)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Такой логин уже существует"}
        )

    if role not in ["student", "teacher"]:
        role = "student"

    crud.create_user(db, username, password, role)
    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    user = crud.get_user(db, username)
    if user and user.password == password:
        request.session["user"] = {
            "id": user.id,
            "role": user.role,
            "username": user.username
        }
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Неверный логин или пароль"}
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("upload.html", {"request": request, "user": user})


@app.post("/upload")
def upload(
    request: Request,
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    original_name = file.filename or "file"
    ext = os.path.splitext(original_name)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join("uploads", unique_name)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    status = "approved" if user["role"] == "teacher" else "pending"

    crud.create_note(
        db,
        title,
        subject,
        category,
        description,
        unique_name,
        original_name,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        user["id"],
        status
    )
    return RedirectResponse("/", status_code=303)


@app.get("/note/{note_id}", response_class=HTMLResponse)
def note_page(note_id: int, request: Request, db=Depends(get_db)):
    note = crud.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Конспект не найден")

    user = get_user(request)
    if note.status != "approved" and (not user or user.get("role") != "teacher"):
        raise HTTPException(status_code=403, detail="Нет доступа")

    crud.add_view(db, note_id)

    liked = False
    favorited = False
    if user:
        liked = crud.has_user_liked(db, note_id, user["id"])
        favorited = crud.is_favorite(db, user["id"], note_id)

    return templates.TemplateResponse(
        "note.html",
        {
            "request": request,
            "note": crud.get_note_by_id(db, note_id),
            "user": user,
            "liked": liked,
            "favorited": favorited,
        }
    )


@app.get("/download/{note_id}")
def download(note_id: int, db=Depends(get_db)):
    note = crud.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Файл не найден")

    file_path = os.path.join("uploads", note.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл отсутствует")

    crud.add_download(db, note_id)

    filename = note.original_filename if note.original_filename else note.filename
    return FileResponse(file_path, filename=filename)


@app.post("/api/toggle-like/{note_id}")
def api_toggle_like(note_id: int, request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user:
        return JSONResponse({"ok": False, "error": "auth_required"}, status_code=401)

    if crud.has_user_liked(db, note_id, user["id"]):
        crud.unlike_note(db, note_id, user["id"])
        liked = False
    else:
        crud.like_note(db, note_id, user["id"])
        liked = True

    note = crud.get_note_by_id(db, note_id)
    return {"ok": True, "liked": liked, "likes": note.likes if note else 0}


@app.post("/api/comment/{note_id}")
def api_comment(
    note_id: int,
    request: Request,
    text: str = Form(...),
    db=Depends(get_db)
):
    user = get_user(request)
    if not user:
        return JSONResponse({"ok": False, "error": "auth_required"}, status_code=401)

    if not text.strip():
        return JSONResponse({"ok": False, "error": "empty_comment"}, status_code=400)

    crud.add_comment(db, note_id, text)
    note = crud.get_note_by_id(db, note_id)

    comments = [{"text": c.text} for c in note.comments] if note else []
    return {"ok": True, "comments": comments}


@app.post("/api/favorite/{note_id}")
def api_favorite(note_id: int, request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user:
        return JSONResponse({"ok": False, "error": "auth_required"}, status_code=401)

    is_now_favorite = crud.toggle_favorite(db, user["id"], note_id)
    note = crud.get_note_by_id(db, note_id)
    favorites_count = len(note.favorites) if note else 0

    return {
        "ok": True,
        "favorited": is_now_favorite,
        "favorites_count": favorites_count,
    }


@app.post("/api/approve/{note_id}")
def api_approve(note_id: int, request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user or user.get("role") != "teacher":
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    crud.approve_note(db, note_id)
    return {"ok": True}


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    notes = crud.get_user_notes(db, user["id"])
    favorites = crud.get_favorites(db, user["id"])

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "notes": notes,
            "favorites": favorites
        }
    )


@app.get("/edit/{note_id}", response_class=HTMLResponse)
def edit_page(note_id: int, request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    note = crud.get_note_by_id(db, note_id)
    if not note or note.owner_id != user["id"]:
        return RedirectResponse("/profile", status_code=303)

    return templates.TemplateResponse(
        "edit_note.html",
        {
            "request": request,
            "note": note,
            "user": user
        }
    )


@app.post("/edit/{note_id}")
def edit_note(
    note_id: int,
    request: Request,
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    db=Depends(get_db)
):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    note = crud.get_note_by_id(db, note_id)
    if not note or note.owner_id != user["id"]:
        return RedirectResponse("/profile", status_code=303)

    crud.update_note(db, note_id, title, subject, category, description)
    return RedirectResponse("/profile", status_code=303)


@app.post("/delete/{note_id}")
def delete_note(note_id: int, request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    note = crud.get_note_by_id(db, note_id)
    if note and note.owner_id == user["id"]:
        file_path = os.path.join("uploads", note.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        crud.delete_note(db, note_id)

    return RedirectResponse("/profile", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db=Depends(get_db)):
    user = get_user(request)
    if not user or user.get("role") != "teacher":
        return RedirectResponse("/", status_code=303)

    notes = crud.get_all_notes(db)
    total_notes, total_users, total_comments, total_favorites = crud.get_stats(db)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "notes": notes,
            "total_notes": total_notes,
            "total_users": total_users,
            "total_comments": total_comments,
            "total_favorites": total_favorites,
            "user": user
        }
    )
