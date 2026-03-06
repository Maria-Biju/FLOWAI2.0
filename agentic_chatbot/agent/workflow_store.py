import uuid

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