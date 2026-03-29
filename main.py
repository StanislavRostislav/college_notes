from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil
import os

from database import SessionLocal, engine
import models
import crud

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.post("/upload")
def upload_note(
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):
    db = SessionLocal()

    filename = file.filename
    path = f"uploads/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, filename)
    db.close()

    return RedirectResponse("/", status_code=303)


@app.get("/download/{note_id}")
def download(note_id: int):
    db = SessionLocal()
    crud.add_download(db, note_id)
    note = db.query(models.Note).get(note_id)
    db.close()
    return RedirectResponse(f"/uploads/{note.filename}")


@app.post("/like/{note_id}")
def like(note_id: int):
    db = SessionLocal()
    crud.add_like(db, note_id)
    db.close()
    return RedirectResponse("/", status_code=303)


@app.post("/comment/{note_id}")
def comment(note_id: int, text: str = Form(...)):
    db = SessionLocal()
    crud.add_comment(db, note_id, text)
    db.close()
    return RedirectResponse("/", status_code=303)
