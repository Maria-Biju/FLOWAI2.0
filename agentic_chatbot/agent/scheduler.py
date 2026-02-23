import time
from datetime import datetime
from threading import Thread

from mcp.notify_tool import notify
from models.reminder import Reminder, db

def reminder_loop(app, poll_seconds=5):
    with app.app_context():
        while True:
            now = datetime.now()
            due = Reminder.query.filter(
                Reminder.status == "pending",
                Reminder.remind_at <= now
            ).all()

            for r in due:
                notify({
                    "title": r.title,
                    "message": r.message,
                    "duration": 6
                })
                r.status = "sent"
                db.session.commit()

            time.sleep(poll_seconds)

def start_scheduler(app):
    t = Thread(target=reminder_loop, args=(app,), daemon=True)
    t.start()