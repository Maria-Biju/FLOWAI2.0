# agent/workflow_store.py
import uuid
import json
from datetime import datetime

from models.workflow import Workflow
from models.db import db

WORKFLOWS = {}


def create_workflow(steps):
    workflow_id = str(uuid.uuid4())

    workflow = {
        "id": workflow_id,
        "steps": steps,
        "current_step": 0,
        "results": []
    }

    WORKFLOWS[workflow_id] = workflow
    return workflow


def get_workflow(workflow_id):
    return WORKFLOWS.get(workflow_id)


def save_step_result(workflow, result):
    workflow["results"].append(result)
    workflow["current_step"] += 1


def create_scheduled_workflow(steps, interval_seconds, next_run=None):
    if next_run is None:
        next_run = datetime.now()

    workflow = Workflow(
        workflow_json=json.dumps({"steps": steps}),
        next_run=next_run,
        interval_seconds=interval_seconds,
        repeat=True,
        status="pending"
    )

    db.session.add(workflow)
    db.session.commit()

    # If the workflow should run immediately, enqueue it right away rather than waiting for the scheduler interval.
    if next_run <= datetime.now():
        from models.workflow_queue import WorkflowQueue

        workflow.status = "queued"
        db.session.add(WorkflowQueue(workflow_id=workflow.id))
        db.session.commit()

    return workflow