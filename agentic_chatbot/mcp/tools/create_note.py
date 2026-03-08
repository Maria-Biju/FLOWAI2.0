from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notes.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def save_note(args: dict):
    title = (args.get("title") or "").strip()
    content = (args.get("content") or "").strip()

    if not title or not content:
        return {"status": "error", "message": "Title and content are required"}

    session = SessionLocal()
    try:
        note = Note(title=title, content=content)
        session.add(note)
        session.commit()
        session.refresh(note)

        return {
            "status": "success",
            "message": f"Note saved successfully with id {note.id}",
            "note_id": note.id
        }
    except Exception as e:
        session.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        session.close()


TOOL = {
    "name": "save_note",
    "description": "Save a note with title and content",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the note"},
            "content": {"type": "string", "description": "Content of the note"}
        },
        "required": ["title", "content"]
    },
    "handler": save_note
}