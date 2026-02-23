from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


#db.create_all()

def save_note(title: str, content: str) -> dict:
        try:
            note = Note(title=title.strip(), content=content.strip())
            db.session.add(note)
            db.session.commit()

            return {
                "status": "success",
                "note_id": note.id,
                "title": note.title,
                "created_at": note.created_at.isoformat()
            }

        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": str(e)}
        
def get_all_notes():
    notes = Note.query.order_by(Note.created_at.desc()).all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "created_at": n.created_at.isoformat()
        }
        for n in notes
    ]
def get_note_by_id(note_id: int):
    note = Note.query.get(note_id)

    if not note:
        return None

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat()
    }

def get_note_by_title(title: str):
    note = Note.query.filter(Note.title.ilike(title)).first()

    if not note:
        return None

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat()
    }

{
  "name": "create_note",
  "description": "Save a note.",
  "input_schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "content": {"type": "string"},
      "tags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["content"]
  }
}