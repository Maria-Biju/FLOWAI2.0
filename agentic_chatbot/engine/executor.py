import json
import re
from datetime import datetime, timedelta
from mcp.client import MCPClient
from models.workflow import Workflow
from models.db import db

mcp = MCPClient()


def resolve_refs(args, results):

    for k, v in args.items():

        if isinstance(v, str):

            match = re.findall(r"{step(\d+)\.(\w+)}", v)

            for step_num, field in match:

                key = f"step{step_num}"

                if key in results:
                    replacement = results[key].get(field, "")
                    v = v.replace(f"{{step{step_num}.{field}}}", str(replacement))

            args[k] = v

    return args


def execute_workflow(workflow_id):

    workflow = db.session.get(Workflow, workflow_id)

    if not workflow:
        print("Workflow not found:", workflow_id)
        return False

    # Ensure tool_server_map is populated by discovering available tools
    available_tools = mcp.list_tools()
    print(f"[Executor] Discovered {len(available_tools)} tools")

    plan = json.loads(workflow.workflow_json)

    results = {}
    success = True

    for step in plan["steps"]:
        tool = step["tool"]
        args = step["arguments"]

        args = resolve_refs(args, results)

        result = mcp.call_tool(tool, args)

        step_key = f"step{step['step']}"
        results[step_key] = result

        print("Executing:", tool)
        print("Arguments:", args)
        print("Result:", result)

        if result.get("status") != "success":
            success = False
            break

    now = datetime.now()
    workflow.last_run = now

    if workflow.repeat and workflow.interval_seconds:
        workflow.next_run = now + timedelta(seconds=workflow.interval_seconds)
        workflow.status = "pending"
    else:
        workflow.status = "completed" if success else "failed"

    db.session.commit()
    return success
