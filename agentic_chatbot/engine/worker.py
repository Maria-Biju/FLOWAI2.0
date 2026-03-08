import time
from models.workflow_queue import WorkflowQueue
from models.db import db
from engine.executor import execute_workflow


def worker_loop(app):

    while True:

        with app.app_context():

            job = WorkflowQueue.query.filter_by(status="queued").first()

            if not job:
                time.sleep(2)
                continue

            job.status = "running"
            db.session.commit()

            execute_workflow(job.workflow_id)

            job.status = "done"
            db.session.commit()