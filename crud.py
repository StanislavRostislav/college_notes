from sqlalchemy.orm import Session, joinedload
import models


def create_user(db, username, password):
    user = models.User(username=username, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db, username):
    return db.query(models.User).filter(models.User.username == username).first()


def create_note(db, title, subject, category, filename, user_id):
    note = models.Note(
        title=title,
        subject=subject,
        category=category,
        filename=filename,
        owner_id=user_id,
        status="approved"   # сразу показываем после загрузки
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_notes(db):
    return (
        db.query(models.Note)
        .options(
            joinedload(models.Note.comments),
            joinedload(models.Note.owner)
        )
        .order_by(models.Note.id.desc())
        .all()
    )


def get_all_notes(db):
    return (
        db.query(models.Note)
        .options(joinedload(models.Note.owner))
        .order_by(models.Note.id.desc())
        .all()
    )


def get_note_by_id(db, note_id):
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def approve_note(db, note_id):
    note = db.query(models.Note).get(note_id)
    if note:
        note.status = "approved"
        db.commit()


def like_note(db, note_id):
    note = db.query(models.Note).get(note_id)
    if note:
        note.likes += 1
        db.commit()


def add_comment(db, note_id, text):
    if text.strip():
        comment = models.Comment(text=text.strip(), note_id=note_id)
        db.add(comment)
        db.commit()


def get_stats(db):
    total_notes = db.query(models.Note).count()
    total_users = db.query(models.User).count()
    return total_notes, total_users
