# mcp/tools/note_tool.py

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os


# ---------- Database Setup ----------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notes.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ---------- Model ----------

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create table automatically
Base.metadata.create_all(bind=engine)
def get_all_notes_handler(args: dict):
    session = SessionLocal()

    try:
        notes = session.query(Note).order_by(Note.created_at.desc()).all()

        return {
            "status": "success",
            "notes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content,
                    "created_at": n.created_at.isoformat()
                }
                for n in notes
            ]
        }

    finally:
        session.close()

TOOL = {
    "name": "get_all_notes",
    "description": "Retrieve all saved notes",
    "schema": {
        "type": "object",
        "properties": {}
    },
    "handler": get_all_notes_handler
}