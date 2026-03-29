from sqlalchemy.orm import Session
import models


def create_note(db: Session, title, subject, category, filename):
    note = models.Note(
        title=title,
        subject=subject,
        category=category,
        filename=filename
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_notes(db: Session, search=None, subject=None):
    query = db.query(models.Note)

    if search:
        query = query.filter(models.Note.title.contains(search))

    if subject and subject != "Все":
        query = query.filter(models.Note.subject == subject)

    return query.order_by(models.Note.id.desc()).all()


def add_download(db: Session, note_id):
    note = db.query(models.Note).get(note_id)
    note.downloads += 1
    db.commit()


def add_like(db: Session, note_id):
    note = db.query(models.Note).get(note_id)
    note.likes += 1
    db.commit()


def add_comment(db: Session, note_id, text):
    comment = models.Comment(text=text, note_id=note_id)
    db.add(comment)
    db.commit()


def get_comments(db: Session, note_id):
    return db.query(models.Comment).filter(models.Comment.note_id == note_id).all()
