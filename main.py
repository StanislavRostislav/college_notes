from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil
import os

from database import SessionLocal, engine
import models
import crud

# создаём таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_notes(request: Request):
    db = SessionLocal()
    notes = crud.get_notes(db)
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "notes": notes})

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
def upload_note(
    title: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...)
):
    db = SessionLocal()
    try:
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        filename = file.filename
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        crud.create_note(db, title, subject, filename)
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/", status_code=303)
