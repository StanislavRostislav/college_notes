from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import SessionLocal, engine
import models, crud
import shutil, os

app = FastAPI()
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


# 🔐 простая "сессия"
current_user = {"id": None}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db=Depends(get_db)):
    notes = crud.get_notes(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": notes,
        "user": current_user
    })


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    crud.create_user(db, username, password)
    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    user = crud.get_user(db, username)
    if user and user.password == password:
        current_user["id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
def upload(
    title: str = Form(...),
    subject: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    filename = file.filename
    path = f"uploads/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    crud.create_note(db, title, subject, category, filename, current_user["id"])
    return RedirectResponse("/", status_code=303)


@app.get("/download/{note_id}")
def download(note_id: int, db=Depends(get_db)):
    note = db.query(models.Note).get(note_id)
    return RedirectResponse(f"/uploads/{note.filename}")


@app.post("/like/{note_id}")
def like(note_id: int, db=Depends(get_db)):
    crud.like_note(db, note_id)
    return RedirectResponse("/", status_code=303)


@app.post("/comment/{note_id}")
def comment(note_id: int, text: str = Form(...), db=Depends(get_db)):
    crud.add_comment(db, note_id, text)
    return RedirectResponse("/", status_code=303)
