from datetime import datetime
from models.workflow import Workflow
from models.workflow_queue import WorkflowQueue
from models.db import db
from apscheduler.schedulers.background import BackgroundScheduler


def check_workflows(app):

    with app.app_context():

        now = datetime.now()

        workflows = Workflow.query.filter(
            Workflow.status == "pending",
            Workflow.next_run <= now
        ).all()

        for wf in workflows:
            job = WorkflowQueue(workflow_id=wf.id)
            db.session.add(job)
            wf.status = "queued"

        db.session.commit()




scheduler = BackgroundScheduler()


def start_scheduler(app):

    scheduler.add_job(
        check_workflows,
        "interval",
        seconds=30,
        args=[app],
        id="workflow_scheduler",
        replace_existing=True
    )

    scheduler.start()