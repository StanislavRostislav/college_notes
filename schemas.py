from pydantic import BaseModel

class NoteCreate(BaseModel):
    title: str
    subject: str

class NoteOut(BaseModel):
    id: int
    title: str
    subject: str
    filename: str

    class Config:
        from_attributes = True