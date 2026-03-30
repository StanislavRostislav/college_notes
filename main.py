from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil
import os
import uuid

from database import SessionLocal, engine
import models
import crud

app = FastAPI()

# создаём таблицы
models.Base.metadata.create_all(bind=engine)

# папка uploads
if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ------------------ ГЛАВНАЯ ------------------
@app.get("/", response_class=HTMLResponse)
def read_notes(request: Request, search: str = "", subject: str = "Все"):
    db = SessionLocal()
    notes = crud.get_notes(db, search, subject)
    db.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": notes,
        "search": search,
        "subject": subject
    })


# ------------------ СТРАНИЦА ЗАГРУЗКИ ------------------
@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


# ------------------ ЗАГРУЗКА ------------------
@app.post("/upload")
def upload_note(
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):
    db = SessionLocal()

    # уникальное имя файла (чтобы старые не удалялись)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"uploads/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, filename)
    db.close()

    return RedirectResponse("/", status_code=303)


# ------------------ СКАЧАТЬ ------------------
@app.get("/download/{note_id}")
def download(note_id: int):
    db = SessionLocal()
    note = crud.get_note(db, note_id)
    db.close()

    file_path = f"uploads/{note.filename}"
    return FileResponse(path=file_path, filename=note.filename)


# ------------------ ЛАЙК ------------------
@app.post("/like/{note_id}")
def like(note_id: int):
    db = SessionLocal()
    crud.like_note(db, note_id)
    db.close()
    return RedirectResponse("/", status_code=303)


# ------------------ КОММЕНТ ------------------
@app.post("/comment/{note_id}")
def comment(note_id: int, text: str = Form(...)):
    db = SessionLocal()
    crud.add_comment(db, note_id, text)
    db.close()
    return RedirectResponse("/", status_code=303)
