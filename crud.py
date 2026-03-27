from sqlalchemy.orm import Session
import models

def create_note(db: Session, title: str, subject: str, filename: str):
    note = models.Note(title=title, subject=subject, filename=filename)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def get_notes(db: Session):
    return db.query(models.Note).all()