from datetime import datetime
# from models.remainder import Reminder, db

# def set_reminder(args: dict, user_id: int):
#     title = args.get("title", "Reminder")
#     message = args.get("message", "")
#     remind_at = args.get("remind_at")  # expected ISO string

#     # parse datetime safely
#     dt = datetime.fromisoformat(remind_at)

#     r = Reminder(
#         user_id=user_id,
#         title=title,
#         message=message,
#         remind_at=dt,
#         status="pending",
#         channel="windows"
#     )
#     db.session.add(r)
#     db.session.commit()

#   return {"status": "success", "message": "Reminder created", "id": r.id}