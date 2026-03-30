from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    subject = Column(String)
    category = Column(String)
    filename = Column(String)
    likes = Column(Integer, default=0)

    comments = relationship("Comment", back_populates="note", cascade="all, delete")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    note_id = Column(Integer, ForeignKey("notes.id"))

    note = relationship("Note", back_populates="comments")
