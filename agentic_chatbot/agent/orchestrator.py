# agent/orchestrator.py
from agent.state_store import get_state
from mcp.client import MCPClient
from agent.workflow_store import create_workflow, create_scheduled_workflow
from agent.workflow_executor import WorkflowExecutor
import json
import re
from models.workflow import Workflow, db
from datetime import datetime


class AgentOrchestrator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.mcp = MCPClient()
        self.executor = WorkflowExecutor(self.mcp)

    def handle_message(self, conversation_id, message: str):
        cid = conversation_id or "default"
        msg = (message or "").strip()

        if not msg:
            return {"type": "message", "reply": "Please type a message."}

        st = get_state(cid)

        # ---------- Show stored result ----------
        if msg.lower().strip() in {"show result", "display result", "return the result"}:
            if getattr(st, "preview_text", None):
                return {"type": "message", "reply": st.preview_text}

            if getattr(st, "last_result", None):
                last_result = st.last_result

                if last_result.get("message"):
                    return {"type": "message", "reply": last_result["message"]}

                if last_result.get("text"):
                    return {"type": "message", "reply": last_result["text"]}

                if last_result.get("results"):
                    last_step = last_result["results"][-1]
                    if last_step.get("text"):
                        return {"type": "message", "reply": last_step["text"]}
                    if last_step.get("message"):
                        return {"type": "message", "reply": last_step["message"]}

            return {"type": "message", "reply": "No previous result available."}

        # ---------- Handle existing pending confirmation ----------
        if st.pending_action and st.pending_payload:
            if self._is_confirmation(msg):
                action = st.pending_action
                payload = st.pending_payload

                if action == "run_workflow":
                    result = self.executor.run(payload)
                elif action == "schedule_workflow":
                    result = self._schedule_workflow(payload)
                else:
                    result = self.mcp.call_tool(action, payload)

                st.pending_action = None
                st.pending_payload = None
                st.last_result = result

                if result.get("status") == "success":
                    # If tool has a message, show it
                    if result.get("message"):
                        return {"type": "message", "reply": result.get("message")}

                    # If google_search returns text, show that
                    if result.get("text"):
                        return {"type": "message", "reply": result.get("text")}
                    if result.get("result"):
                        return {"type": "message", "reply": str(result.get("result"))}
                    # If notes tool returns notes list
                    if result.get("notes"):
                        notes_text = "\n\n".join(
                            [
                                f"{n.get('title', 'Untitled')}\n{n.get('content', '')}"
                                for n in result["notes"]
                            ]
                        )
                        return {
                            "type": "message",
                            "reply": notes_text or "Notes retrieved successfully."
                        }

                    return {"type": "message", "reply": "Action completed successfully."}

                return {
                    "type": "message",
                    "reply": f"Action failed: {result.get('message')}"
                }

            if self._is_cancellation(msg):
                st.pending_action = None
                st.pending_payload = None
                st.preview_text = None
                return {"type": "message", "reply": "Cancelled."}

            return {
                "type": "message",
                "reply": self._format_pending_preview(st.pending_action, st.pending_payload)
            }

        # ---------- Handle empty pending + confirm/cancel ----------
        if self._is_confirmation(msg):
            return {"type": "message", "reply": "Nothing is waiting for confirmation."}

        if self._is_cancellation(msg):
            return {"type": "message", "reply": "Nothing to cancel."}

        # ---------- Discover available tools dynamically ----------
        tools_metadata = self.mcp.list_tools()

        if not tools_metadata:
            return {
                "type": "message",
                "reply": "No MCP tools are available right now. Please make sure the MCP server is running."
            }

        # ---------- Ask LLM to decide ----------
        result = self.llm.process(msg, tools_metadata)

        # ---------- Workflow plan ----------
        if result.get("type") == "workflow":
            workflow = create_workflow(result["steps"])
            schedule_info = self._parse_schedule(msg)

            preview = self.executor.preview(workflow)

            if preview.get("status") != "success":
                return {
                    "type": "message",
                    "reply": f"Workflow preview failed: {preview.get('message')}"
                }

            if schedule_info:
                st.pending_action = "schedule_workflow"
                st.pending_payload = {
                    "steps": workflow["steps"],
                    "interval_seconds": schedule_info["interval_seconds"],
                    "next_run": schedule_info["next_run"],
                    "description": schedule_info["description"]
                }
                st.preview_text = preview.get("preview_text")
                st.last_result = preview

                preview_text = (preview.get("preview_text") or "").strip()

                if preview_text:
                    return {
                        "type": "message",
                        "reply": (
                            f"Workflow preview:\n\n{preview_text}\n\n"
                            f"This workflow will be scheduled {schedule_info['description']}.\n"
                            "Reply confirm to schedule or cancel."
                        )
                    }

                return {
                    "type": "message",
                    "reply": (
                        f"Workflow created with {len(workflow.get('steps', []))} step(s).\n"
                        f"This workflow will be scheduled {schedule_info['description']}.\n"
                        "Reply confirm to schedule or cancel."
                    )
                }

            st.pending_action = "run_workflow"
            st.pending_payload = preview["remaining_workflow"]
            st.preview_text = preview.get("preview_text")
            st.last_result = preview

            preview_text = (preview.get("preview_text") or "").strip()

            if preview_text:
                return {
                    "type": "message",
                    "reply": (
                        f"Preview result:\n\n{preview_text}\n\n"
                        "The next action is ready.\n"
                        "Reply confirm to continue or cancel."
                    )
                }

            return {
                "type": "message",
                "reply": self._format_workflow_preview(workflow)
            }

        # ---------- Single tool call ----------
        if result.get("type") == "tool_call":
            tool = result.get("tool")
            arguments = result.get("arguments", {})

            if not tool:
                return {"type": "message", "reply": "Invalid tool request."}

            schedule_info = self._parse_schedule(msg)
            if schedule_info:
                scheduled_steps = [
                    {
                        "step": 1,
                        "tool": tool,
                        "arguments": arguments
                    }
                ]
                st.pending_action = "schedule_workflow"
                st.pending_payload = {
                    "steps": scheduled_steps,
                    "interval_seconds": schedule_info["interval_seconds"],
                    "next_run": schedule_info["next_run"],
                    "description": schedule_info["description"]
                }
                st.preview_text = None
                st.last_result = {
                    "type": "workflow",
                    "steps": scheduled_steps
                }

                return {
                    "type": "message",
                    "reply": (
                        f"This action will be scheduled {schedule_info['description']}.\n"
                        "Reply confirm to schedule or cancel."
                    )
                }

            st.pending_action = tool
            st.pending_payload = arguments
            st.preview_text = None

            return {
                "type": "message",
                "reply": self._format_pending_preview(tool, arguments)
            }

        # ---------- Normal message ----------
        if result.get("type") == "message":
            return result

        return {"type": "message", "reply": "Unexpected response."}

    # ---------------- helpers ----------------

    def _is_confirmation(self, msg: str) -> bool:
        return msg.lower().strip() in {"confirm", "yes", "ok", "proceed"}

    def _is_cancellation(self, msg: str) -> bool:
        return msg.lower().strip() in {"cancel", "no", "stop", "abort"}

    def _format_pending_preview(self, action: str, payload: dict) -> str:
        lines = [f"Pending action: {action}", ""]
        if isinstance(payload, dict):
            for key, value in payload.items():
                lines.append(f"{key}: {value}")
        else:
            lines.append(str(payload))
        lines.append("")
        lines.append("Reply confirm to execute or cancel.")
        return "\n".join(lines)

    def _parse_schedule(self, msg: str):
        if not msg:
            return None

        normalized = msg.lower().strip()
        
        if "every second" in normalized or "every 1 second" in normalized:
            return {
                "interval_seconds": 1,
                "next_run": datetime.now(),
                "description": "every second"
            }

        if "every minute" in normalized or "minutely" in normalized:
            return {
                "interval_seconds": 60,
                "next_run": datetime.now(),
                "description": "every minute"
            }

        if "hourly" in normalized or "every hour" in normalized:
            return {
                "interval_seconds": 3600,
                "next_run": datetime.now(),
                "description": "every hour"
            }

        if "everyday" in normalized or "every day" in normalized or "daily" in normalized:
            return {
                "interval_seconds": 86400,
                "next_run": datetime.now(),
                "description": "every day"
            }

        if "weekly" in normalized or "every week" in normalized:
            return {
                "interval_seconds": 604800,
                "next_run": datetime.now(),
                "description": "every week"
            }

        if "monthly" in normalized or "every month" in normalized:
            return {
                "interval_seconds": 2592000,
                "next_run": datetime.now(),
                "description": "every month"
            }

        if "yearly" in normalized or "every year" in normalized:
            return {
                "interval_seconds": 31536000,
                "next_run": datetime.now(),
                "description": "every year"
            }

        match = re.search(r"\bevery(?:\s+an?|\s+one)?\s*(\d+)?\s*(seconds?|minutes?|hours?|days?|weeks?|months?)\b", normalized)
        if not match:
            return None

        count = match.group(1)
        unit = match.group(2).lower()

        if count is None:
            count = 1
        else:
            count = int(count)

        seconds = None
        if unit.startswith("second"):
            seconds = count
        elif unit.startswith("minute"):
            seconds = count * 60
        elif unit.startswith("hour"):
            seconds = count * 3600
        elif unit.startswith("day"):
            seconds = count * 86400
        elif unit.startswith("week"):
            seconds = count * 604800
        elif unit.startswith("month"):
            seconds = count * 2592000

        if seconds is None:
            return None

        description = f"every {count} {unit}{'s' if count != 1 else ''}"
        return {
            "interval_seconds": seconds,
            "next_run": datetime.now(),
            "description": description
        }

    def _schedule_workflow(self, payload: dict):
        steps = payload.get("steps")
        interval_seconds = payload.get("interval_seconds")
        next_run = payload.get("next_run")

        if not steps or not interval_seconds:
            return {
                "status": "error",
                "message": "Unable to schedule workflow. Missing scheduling details."
            }

        workflow = create_scheduled_workflow(
            steps=steps,
            interval_seconds=interval_seconds,
            next_run=next_run
        )

        return {
            "status": "success",
            "message": (
                f"Scheduled workflow {workflow.id} to run {payload.get('description')} starting at {workflow.next_run}."
            )
        }

    def _format_workflow_preview(self, workflow: dict) -> str:
        lines = [f"Workflow created with {len(workflow.get('steps', []))} step(s):", ""]
        for step in workflow.get("steps", []):
            lines.append(f"Step {step.get('step')}: {step.get('tool')}")
            args = step.get("arguments", {})
            if args:
                for k, v in args.items():
                    lines.append(f"  - {k}: {v}")
        lines.append("")
        lines.append("Reply confirm to execute or cancel.")
        return "\n".join(lines)