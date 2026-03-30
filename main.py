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

models.Base.metadata.create_all(bind=engine)

if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def read_notes(request: Request):
    db = SessionLocal()
    notes = crud.get_notes(db)

   @app.get("/", response_class=HTMLResponse)
def read_notes(request: Request):
    db = SessionLocal()
    notes = crud.get_notes(db)
    db.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": notes
    })

    db.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": notes
    })


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
def upload_note(
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):
    db = SessionLocal()

    # 🔥 уникальное имя файла
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    path = f"uploads/{unique_name}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, unique_name)
    db.close()

    return RedirectResponse("/", status_code=303)


# ✅ скачать
@app.get("/download/{note_id}")
def download(note_id: int):
    db = SessionLocal()
    note = crud.get_note(db, note_id)
    db.close()

    if note:
        return FileResponse(f"uploads/{note.filename}", filename=note.filename)


# ✅ лайк
@app.post("/like/{note_id}")
def like(note_id: int):
    db = SessionLocal()
    crud.like_note(db, note_id)
    db.close()
    return RedirectResponse("/", status_code=303)


# ✅ комментарий
@app.post("/comment/{note_id}")
def comment(note_id: int, text: str = Form(...)):
    db = SessionLocal()
    crud.add_comment(db, note_id, text)
    db.close()
    return RedirectResponse("/", status_code=303)
