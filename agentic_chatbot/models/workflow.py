from models.db import db
from datetime import datetime



class Workflow(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    workflow_json = db.Column(db.Text)

    status = db.Column(db.String(20), default="pending")

    next_run = db.Column(db.DateTime)

    interval_seconds = db.Column(db.Integer, nullable=True)

    repeat = db.Column(db.Boolean, default=False)

    retries = db.Column(db.Integer, default=0)

    last_run = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)