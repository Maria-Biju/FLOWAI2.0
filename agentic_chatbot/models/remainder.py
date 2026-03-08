# from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()

# class Reminder(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, nullable=False)

#     title = db.Column(db.String(200), nullable=False)
#     message = db.Column(db.Text, nullable=False)

#     remind_at = db.Column(db.DateTime, nullable=False)
#     status = db.Column(db.String(20), default="pending")  # pending/sent
#     channel = db.Column(db.String(50), default="windows") # windows/email etc

#     created_at = db.Column(db.DateTime, default=datetime.utcnow)