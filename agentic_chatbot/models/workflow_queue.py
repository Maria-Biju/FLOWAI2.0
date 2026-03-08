
from datetime import datetime
from models.db import db

class WorkflowQueue(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    workflow_id = db.Column(db.Integer)

    status = db.Column(db.String(20), default="queued")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)