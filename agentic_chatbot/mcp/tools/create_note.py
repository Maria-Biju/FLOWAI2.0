# # # mcp/tools/note_tool.py

# # from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
# # from sqlalchemy.orm import declarative_base, sessionmaker
# # from datetime import datetime
# # import os


# # # ---------- Database Setup ----------

# # DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notes.db")

# # engine = create_engine(DATABASE_URL, echo=False)
# # SessionLocal = sessionmaker(bind=engine)
# # Base = declarative_base()


# # # ---------- Model ----------

# # class Note(Base):
# #     __tablename__ = "notes"

# #     id = Column(Integer, primary_key=True)
# #     title = Column(String(200), nullable=False)
# #     content = Column(Text, nullable=False)
# #     created_at = Column(DateTime, default=datetime.utcnow)


# # # Create table automatically
# # Base.metadata.create_all(bind=engine)


# # ---------- Tool Handlers ----------

# def save_note_handler(args: dict):
#     title = args.get("title", "").strip()
#     content = args.get("content", "").strip()

#     if not title or not content:
#         return {"status": "error", "message": "Title and content required"}

#     session = SessionLocal()

#     try:
#         note = Note(title=title, content=content)
#         session.add(note)
#         session.commit()
#         session.refresh(note)

#         return {
#             "status": "success",
#             "note_id": note.id,
#             "title": note.title,
#             "created_at": note.created_at.isoformat()
#         }

#     except Exception as e:
#         session.rollback()
#         return {"status": "error", "message": str(e)}

#     finally:
#         session.close()


# def get_all_notes_handler(args: dict):
#     session = SessionLocal()

#     try:
#         notes = session.query(Note).order_by(Note.created_at.desc()).all()

#         return {
#             "status": "success",
#             "notes": [
#                 {
#                     "id": n.id,
#                     "title": n.title,
#                     "content": n.content,
#                     "created_at": n.created_at.isoformat()
#                 }
#                 for n in notes
#             ]
#         }

#     finally:
#         session.close()


# def get_note_by_title_handler(args: dict):
#     title = args.get("title", "")

#     session = SessionLocal()

#     try:
#         note = session.query(Note).filter(Note.title.ilike(title)).first()

#         if not note:
#             return {"status": "error", "message": "Note not found"}

#         return {
#             "status": "success",
#             "note": {
#                 "id": note.id,
#                 "title": note.title,
#                 "content": note.content,
#                 "created_at": note.created_at.isoformat()
#             }
#         }

#     finally:
#         session.close()


# # ---------- Tool Registration ----------

# TOOL = {
#     "name": "save_note",
#     "description": "Save a note with title and content",
#     "schema": {
#         "type": "object",
#         "properties": {
#             "title": {"type": "string"},
#             "content": {"type": "string"}
#         },
#         "required": ["title", "content"]
#     },
#     "handler": save_note_handler
# }