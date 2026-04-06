from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func, desc
from datetime import datetime
import models


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# =========================
# USERS
# =========================
def create_user(db, username, password, role="student"):
    user = models.User(username=username, password=password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db, username):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()


# =========================
# NOTES
# =========================
def create_note(db, title, subject, category, description, filename, original_filename, created_at, user_id, status="pending"):
    note = models.Note(
        title=title,
        subject=subject,
        category=category,
        description=description,
        filename=filename,
        original_filename=original_filename,
        created_at=created_at,
        owner_id=user_id,
        status=status
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_notes(db, search="", subject="", category="", sort="new", viewer=None):
    query = db.query(models.Note).options(
        joinedload(models.Note.comments),
        joinedload(models.Note.owner),
        joinedload(models.Note.favorites),
        joinedload(models.Note.liked_by)
    )

    if viewer:
        if viewer.get("role") == "teacher":
            pass
        else:
            query = query.filter(
                or_(
                    models.Note.status == "approved",
                    models.Note.owner_id == viewer.get("id")
                )
            )
    else:
        query = query.filter(models.Note.status == "approved")

    if search:
        query = query.filter(
            or_(
                models.Note.title.ilike(f"%{search}%"),
                models.Note.subject.ilike(f"%{search}%"),
                models.Note.category.ilike(f"%{search}%"),
                models.Note.description.ilike(f"%{search}%")
            )
        )

    if subject and subject != "all":
        query = query.filter(models.Note.subject == subject)

    if category and category != "all":
        query = query.filter(models.Note.category == category)

    if sort == "popular":
        query = query.order_by(models.Note.likes.desc(), models.Note.id.desc())
    elif sort == "views":
        query = query.order_by(models.Note.views.desc(), models.Note.id.desc())
    elif sort == "downloads":
        query = query.order_by(models.Note.downloads.desc(), models.Note.id.desc())
    else:
        query = query.order_by(models.Note.id.desc())

    return query.all()


def get_all_notes(db):
    return db.query(models.Note).options(
        joinedload(models.Note.owner),
        joinedload(models.Note.comments),
        joinedload(models.Note.favorites),
        joinedload(models.Note.liked_by)
    ).order_by(models.Note.id.desc()).all()


def get_note_by_id(db, note_id):
    return db.query(models.Note).options(
        joinedload(models.Note.comments),
        joinedload(models.Note.owner),
        joinedload(models.Note.favorites),
        joinedload(models.Note.liked_by)
    ).filter(models.Note.id == note_id).first()


def get_user_notes(db, user_id):
    return db.query(models.Note).options(
        joinedload(models.Note.comments),
        joinedload(models.Note.owner),
        joinedload(models.Note.favorites),
        joinedload(models.Note.liked_by)
    ).filter(models.Note.owner_id == user_id).order_by(models.Note.id.desc()).all()


def update_note(db, note_id, title, subject, category, description):
    note = get_note_by_id(db, note_id)
    if note:
        note.title = title
        note.subject = subject
        note.category = category
        note.description = description
        db.commit()
        db.refresh(note)
    return note


def delete_note(db, note_id):
    note = get_note_by_id(db, note_id)
    if note:
        db.delete(note)
        db.commit()


def approve_note(db, note_id):
    note = db.query(models.Note).get(note_id)
    if note:
        note.status = "approved"
        db.commit()
        create_notification(
            db,
            note.owner_id,
            f"✅ Ваш материал «{note.title}» был одобрен преподавателем."
        )


def like_note(db, note_id, user_id):
    existing_like = db.query(models.Like).filter(
        models.Like.note_id == note_id,
        models.Like.user_id == user_id
    ).first()

    if existing_like:
        return False

    note = db.query(models.Note).get(note_id)
    if not note:
        return False

    like = models.Like(user_id=user_id, note_id=note_id)
    db.add(like)
    note.likes += 1
    db.commit()

    if note.owner_id != user_id:
        create_notification(
            db,
            note.owner_id,
            f"❤️ Кто-то поставил лайк вашему материалу «{note.title}»."
        )

    return True


def unlike_note(db, note_id, user_id):
    existing_like = db.query(models.Like).filter(
        models.Like.note_id == note_id,
        models.Like.user_id == user_id
    ).first()

    if not existing_like:
        return False

    note = db.query(models.Note).get(note_id)
    if note and note.likes > 0:
        note.likes -= 1

    db.delete(existing_like)
    db.commit()
    return True


def has_user_liked(db, note_id, user_id):
    return db.query(models.Like).filter(
        models.Like.note_id == note_id,
        models.Like.user_id == user_id
    ).first() is not None


def add_comment(db, note_id, text, author_user_id=None):
    text = text.strip()
    if text:
        comment = models.Comment(text=text, note_id=note_id)
        db.add(comment)
        db.commit()

        note = db.query(models.Note).get(note_id)
        if note and author_user_id and note.owner_id != author_user_id:
            create_notification(
                db,
                note.owner_id,
                f"💬 Новый комментарий к материалу «{note.title}»."
            )


def add_view(db, note_id):
    note = db.query(models.Note).get(note_id)
    if note:
        note.views += 1
        db.commit()


def add_download(db, note_id):
    note = db.query(models.Note).get(note_id)
    if note:
        note.downloads += 1
        db.commit()


def toggle_favorite(db, user_id, note_id):
    fav = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id,
        models.Favorite.note_id == note_id
    ).first()

    note = db.query(models.Note).get(note_id)

    if fav:
        db.delete(fav)
        db.commit()
        return False
    else:
        fav = models.Favorite(user_id=user_id, note_id=note_id)
        db.add(fav)
        db.commit()

        if note and note.owner_id != user_id:
            create_notification(
                db,
                note.owner_id,
                f"⭐ Ваш материал «{note.title}» добавили в избранное."
            )
        return True


def is_favorite(db, user_id, note_id):
    return db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id,
        models.Favorite.note_id == note_id
    ).first() is not None


def get_favorites(db, user_id):
    return db.query(models.Favorite).options(
        joinedload(models.Favorite.note).joinedload(models.Note.owner),
        joinedload(models.Favorite.note).joinedload(models.Note.comments),
        joinedload(models.Favorite.note).joinedload(models.Note.favorites),
        joinedload(models.Favorite.note).joinedload(models.Note.liked_by)
    ).filter(models.Favorite.user_id == user_id).all()


# =========================
# ASSIGNMENTS
# =========================
def create_assignment(db, title, subject, description, deadline, file_name, original_file_name, creator_id):
    assignment = models.Assignment(
        title=title,
        subject=subject,
        description=description,
        deadline=deadline,
        file_name=file_name,
        original_file_name=original_file_name,
        created_at=now_str(),
        creator_id=creator_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    students = db.query(models.User).filter(models.User.role == "student").all()
    for student in students:
        create_notification(
            db,
            student.id,
            f"📚 Новое задание: «{assignment.title}». Дедлайн: {assignment.deadline}"
        )

    return assignment


def get_assignments(db):
    return db.query(models.Assignment).options(
        joinedload(models.Assignment.creator)
    ).order_by(models.Assignment.id.desc()).all()


# =========================
# NOTIFICATIONS
# =========================
def create_notification(db, user_id, text):
    notification = models.Notification(
        user_id=user_id,
        text=text,
        is_read=False,
        created_at=now_str()
    )
    db.add(notification)
    db.commit()
    return notification


def get_notifications(db, user_id):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id
    ).order_by(models.Notification.id.desc()).all()


def get_unread_notifications_count(db, user_id):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()


def mark_all_notifications_read(db, user_id):
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).all()

    for n in notifications:
        n.is_read = True

    db.commit()


# =========================
# STATS / ACHIEVEMENTS
# =========================
def get_stats(db):
    total_notes = db.query(models.Note).count()
    total_users = db.query(models.User).count()
    total_comments = db.query(models.Comment).count()
    total_favorites = db.query(models.Favorite).count()
    total_assignments = db.query(models.Assignment).count()
    return total_notes, total_users, total_comments, total_favorites, total_assignments


def get_subjects(db):
    rows = db.query(models.Note.subject).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


def get_categories(db):
    rows = db.query(models.Note.category).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


def get_top_users(db):
    return (
        db.query(
            models.User.id,
            models.User.username,
            models.User.role,
            func.count(models.Note.id).label("notes_count"),
            func.coalesce(func.sum(models.Note.likes), 0).label("likes_sum"),
            func.coalesce(func.sum(models.Note.views), 0).label("views_sum"),
            func.coalesce(func.sum(models.Note.downloads), 0).label("downloads_sum")
        )
        .outerjoin(models.Note, models.Note.owner_id == models.User.id)
        .group_by(models.User.id)
        .order_by(desc("likes_sum"), desc("downloads_sum"), desc("notes_count"))
        .all()
    )


def get_user_points_and_achievements(db, user_id):
    user_notes = db.query(models.Note).filter(models.Note.owner_id == user_id).all()

    notes_count = len(user_notes)
    likes_sum = sum(n.likes for n in user_notes)
    downloads_sum = sum(n.downloads for n in user_notes)
    views_sum = sum(n.views for n in user_notes)

    points = notes_count * 10 + likes_sum * 3 + downloads_sum * 2 + views_sum

    achievements = []

    if notes_count >= 1:
        achievements.append("🚀 Первый материал")
    if notes_count >= 5:
        achievements.append("📚 Активный автор")
    if likes_sum >= 10:
        achievements.append("❤️ Любимец студентов")
    if downloads_sum >= 10:
        achievements.append("⬇ Полезный материал")
    if points >= 100:
        achievements.append("🏆 Топ-автор")

    if not achievements:
        achievements.append("🙂 Пока без достижений")

    return {
        "points": points,
        "notes_count": notes_count,
        "likes_sum": likes_sum,
        "downloads_sum": downloads_sum,
        "views_sum": views_sum,
        "achievements": achievements
    }


def get_dashboard_chart_data(db):
    top_subjects = (
        db.query(
            models.Note.subject,
            func.count(models.Note.id).label("count")
        )
        .group_by(models.Note.subject)
        .order_by(desc("count"))
        .limit(6)
        .all()
    )

    top_materials = (
        db.query(models.Note)
        .order_by(models.Note.downloads.desc(), models.Note.likes.desc())
        .limit(5)
        .all()
    )

    subjects_labels = [x.subject for x in top_subjects]
    subjects_counts = [x.count for x in top_subjects]

    materials_labels = [x.title for x in top_materials]
    materials_downloads = [x.downloads for x in top_materials]

    return {
        "subjects_labels": subjects_labels,
        "subjects_counts": subjects_counts,
        "materials_labels": materials_labels,
        "materials_downloads": materials_downloads,
    }
