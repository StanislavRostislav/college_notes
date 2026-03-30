from sqlalchemy.orm import Session, joinedload
import models

def create_note(db, title, subject, category, filename):
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


def get_notes(db):
    return db.query(models.Note).options(
        joinedload(models.Note.comments)
    ).all()


def like_note(db, note_id):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if note:
        note.likes += 1
        db.commit()


def add_comment(db, note_id, text):
    comment = models.Comment(text=text, note_id=note_id)
    db.add(comment)
    db.commit()


def get_note(db, note_id):
    return db.query(models.Note).filter(models.Note.id == note_id).first()
