from sqlalchemy.orm import Session, joinedload
import models


def create_user(db: Session, username: str, password_hash: str):
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_note(
    db: Session,
    title: str,
    subject: str,
    category: str,
    filename: str,
    original_filename: str,
    user_id: int,
):
    note = models.Note(
        title=title,
        subject=subject,
        category=category,
        filename=filename,
        original_filename=original_filename,
        owner_id=user_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_notes(db: Session, search: str = "", subject: str = "Все"):
    query = db.query(models.Note).options(
        joinedload(models.Note.owner),
        joinedload(models.Note.comments).joinedload(models.Comment.user),
    )

    if search:
        query = query.filter(models.Note.title.ilike(f"%{search}%"))

    if subject and subject != "Все":
        query = query.filter(models.Note.subject == subject)

    return query.order_by(models.Note.id.desc()).all()


def get_subjects(db: Session):
    rows = db.query(models.Note.subject).distinct().order_by(models.Note.subject.asc()).all()
    return [row[0] for row in rows]


def get_note_by_id(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def like_note(db: Session, note_id: int):
    note = get_note_by_id(db, note_id)
    if note:
        note.likes += 1
        db.commit()
        db.refresh(note)
    return note


def add_comment(db: Session, note_id: int, user_id: int, text: str):
    comment = models.Comment(
        text=text.strip(),
        note_id=note_id,
        user_id=user_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
