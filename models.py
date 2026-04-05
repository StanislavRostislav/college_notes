from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="student")

    notes = relationship("Note", back_populates="owner")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    subject = Column(String)
    category = Column(String)
    filename = Column(String)
    likes = Column(Integer, default=0)
    status = Column(String, default="pending")

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")

    comments = relationship("Comment", back_populates="note")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    text = Column(String)

    note_id = Column(Integer, ForeignKey("notes.id"))
    note = relationship("Note", back_populates="comments")
