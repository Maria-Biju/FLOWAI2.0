import re


class WorkflowExecutor:

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    def run(self, workflow):

        steps = workflow["steps"]
        results = workflow["results"]

        for step in steps:

            tool = step["tool"]
            args = self._resolve_args(step["arguments"], results)

            result = self.mcp.call_tool(tool, args)

            results.append(result)

            if result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Step {step['step']} failed: {result.get('message')}"
                }

        return {
            "status": "success",
            "message": "Workflow completed successfully."
        }

    def _resolve_args(self, args, results):

        resolved = {}

        for key, value in args.items():

            if isinstance(value, str):

                # support {{step1.text}}
                match = re.findall(r"\{\{step(\d+)\.(\w+)\}\}", value)

                # support {step1.text}
                if not match:
                    match = re.findall(r"\{step(\d+)\.(\w+)\}", value)

                if match:
                    step_id, field = match[0]
                    step_id = int(step_id) - 1

                    if step_id < len(results):
                        resolved[key] = results[step_id].get(field)

                    else:
                        resolved[key] = value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved