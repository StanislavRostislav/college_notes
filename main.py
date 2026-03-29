from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil
import os

from database import SessionLocal, engine
import models
import crud

# ✅ СНАЧАЛА создаём app
app = FastAPI()

# ✅ потом всё остальное
models.Base.metadata.create_all(bind=engine)

if not os.path.exists("uploads"):
    os.makedirs("uploads")

templates = Jinja2Templates(directory="templates")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ✅ ТЕПЕРЬ можно писать роуты

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


# 🔥 ВАЖНО — ЭТОТ РОУТ ДОЛЖЕН БЫТЬ ПОСЛЕ app
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

    filename = file.filename
    path = f"uploads/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, filename)
    db.close()

    return RedirectResponse("/", status_code=303)
