from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="student")  # student / teacher

    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    assignments_created = relationship("Assignment", back_populates="creator", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    subject = Column(String)
    category = Column(String)
    description = Column(String, default="")
    filename = Column(String)
    original_filename = Column(String, default="")
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    status = Column(String, default="pending")
    created_at = Column(String, default="")

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")

    comments = relationship("Comment", back_populates="note", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="note", cascade="all, delete-orphan")
    liked_by = relationship("Like", back_populates="note", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    text = Column(String)

    note_id = Column(Integer, ForeignKey("notes.id"))
    note = relationship("Note", back_populates="comments")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    note_id = Column(Integer, ForeignKey("notes.id"))

    user = relationship("User", back_populates="favorites")
    note = relationship("Note", back_populates="favorites")


class Like(Base):
    __tablename__ = "likes_table"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    note_id = Column(Integer, ForeignKey("notes.id"))

    user = relationship("User", back_populates="likes")
    note = relationship("Note", back_populates="liked_by")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    subject = Column(String)
    description = Column(String, default="")
    deadline = Column(String, default="")
    file_name = Column(String, default="")
    original_file_name = Column(String, default="")
    created_at = Column(String, default="")

    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="assignments_created")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(String, default="")

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="notifications")
