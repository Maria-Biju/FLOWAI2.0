# agent/workflow_executor.py
import re


class WorkflowExecutor:
    SAFE_PREVIEW_TOOLS = {"google_search", "get_all_notes"}

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    def preview(self, workflow: dict):
        steps = workflow.get("steps", [])
        results = []

        remaining_steps = []
        preview_lines = []

        for step in steps:
            tool = step.get("tool")
            args = step.get("arguments", {})

            # safe read-only tools can be previewed now
            if tool in self.SAFE_PREVIEW_TOOLS:
                resolved_args = self._resolve_args(args, results)
                result = self.mcp.call_tool(tool, resolved_args)

                if result.get("status") != "success":
                    return {
                        "status": "error",
                        "message": f"Preview step {step.get('step')} failed: {result.get('message')}"
                    }

                results.append(result)

                # build readable preview
                if result.get("text"):
                    preview_lines.append(result["text"])
                elif result.get("notes"):
                    preview_lines.append(
                        "\n\n".join(
                            [f"{n.get('title','Untitled')}\n{n.get('content','')}" for n in result["notes"]]
                        )
                    )
                elif result.get("message"):
                    preview_lines.append(result["message"])

            else:
                # action steps kept for confirmation
                resolved_args = self._resolve_args(args, results)
                remaining_steps.append({
                    **step,
                    "arguments": resolved_args
                })

        return {
            "status": "success",
            "preview_text": "\n\n".join(preview_lines).strip(),
            "remaining_workflow": {
                "steps": remaining_steps,
                "results": results
            }
        }

    def run(self, workflow: dict):
        steps = workflow.get("steps", [])
        results = workflow.get("results", [])

        if not steps:
            return {
                "status": "error",
                "message": "Workflow has no steps."
            }

        for step in steps:
            tool = step.get("tool")
            args = step.get("arguments", {})

            resolved_args = self._resolve_args(args, results)
            result = self.mcp.call_tool(tool, resolved_args)

            if result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Step {step.get('step')} failed: {result.get('message', 'Unknown error')}",
                    "results": results
                }

            results.append(result)

        last_result = results[-1] if results else {}

        return {
            "status": "success",
            "message": (
                last_result.get("message")
                or last_result.get("text")
                or "Workflow completed successfully."
            ),
            "results": results
        }

    def _resolve_args(self, args: dict, results: list):
        resolved = {}

        for key, value in args.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_placeholders_in_text(value, results)
            else:
                resolved[key] = value

        return resolved

    def _resolve_placeholders_in_text(self, text: str, results: list) -> str:
        text = re.sub(
            r"\{\{step(\d+)\.(\w+)\}\}",
            lambda m: self._lookup_result(m, results),
            text
        )

        text = re.sub(
            r"\{step(\d+)\.(\w+)\}",
            lambda m: self._lookup_result(m, results),
            text
        )

        return text

    def _lookup_result(self, match, results: list) -> str:
        step_id = int(match.group(1)) - 1
        field = match.group(2)

        if 0 <= step_id < len(results):
            step_result = results[step_id]

            value = step_result.get(field)
            if value is not None:
                return str(value)

    # fallback: if asking for text but tool returned result
            if field == "text" and step_result.get("result") is not None:
                return str(step_result.get("result"))

    # fallback: if asking for result but tool returned text
            if field == "result" and step_result.get("text") is not None:
                return str(step_result.get("text"))

        return match.group(0)