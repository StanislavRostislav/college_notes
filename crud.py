from sqlalchemy.orm import Session, joinedload
import models


# 📌 Создание заметки
def create_note(db: Session, title, subject, category, filename):
    note = models.Note(
        title=title,
        subject=subject,
        category=category,
        filename=filename,
        likes=0
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# 📌 Получение всех заметок (с поиском и фильтром)
def get_notes(db: Session, search: str = "", subject: str = "Все"):
    query = db.query(models.Note).options(
        joinedload(models.Note.comments)
    )

    # 🔍 Поиск по названию
    if search:
        query = query.filter(models.Note.title.ilike(f"%{search}%"))

    # 📚 Фильтр по предмету
    if subject != "Все":
        query = query.filter(models.Note.subject == subject)

    return query.all()


# ❤️ Лайк
def like_note(db: Session, note_id: int):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if note:
        note.likes += 1
        db.commit()


# 💬 Добавить комментарий
def add_comment(db: Session, note_id: int, text: str):
    comment = models.Comment(
        text=text,
        note_id=note_id
    )
    db.add(comment)
    db.commit()


# 📄 Получить одну заметку
def get_note(db: Session, note_id: int):
    return db.query(models.Note).options(
        joinedload(models.Note.comments)
    ).filter(models.Note.id == note_id).first()


# ⬇️ Скачать файл (по сути просто получить note)
def get_note_file(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()
