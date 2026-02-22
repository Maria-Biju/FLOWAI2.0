from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    remind_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)

db.create_all()

def send_email(args: dict):

    print("📧 Sending email...")
    print("To:", args.get("to"))
    print("Subject:", args.get("subject"))
    print("Body:", args.get("body"))

    return {
        "status": "success",
        "message": "Email sent successfully"
    }

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


def set_reminder(title: str, remind_at: datetime, message: str = "") -> dict:
    try:
        reminder = Reminder(
            title=title.strip(),
            message=message.strip(),
            remind_at=remind_at
        )

        db.session.add(reminder)
        db.session.commit()

        return {
            "status": "success",
            "reminder_id": reminder.id,
            "title": reminder.title,
            "remind_at": reminder.remind_at.isoformat()
        }

    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}
        
