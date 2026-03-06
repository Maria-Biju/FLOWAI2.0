# agent/orchestrator.py

from agent.state_store import get_state
from mcp.client import MCPClient


class AgentOrchestrator:

    def __init__(self, llm_client):
        self.llm = llm_client
        self.mcp = MCPClient()

    def handle_message(self, conversation_id, message: str):

        cid = conversation_id or "default"
        msg = (message or "").strip()

        if not msg:
            return {"type": "message", "reply": "Please type a message."}

        st = get_state(cid)

        # ---------- Pending Confirmation ----------
        if st.pending_action and st.pending_payload:

            if self._is_confirmation(msg):

                action = st.pending_action
                payload = st.pending_payload

                result = self.mcp.call_tool(action, payload)

                # Always clear state after execution
                st.pending_action = None
                st.pending_payload = None

                if result.get("status") == "success":
                    reply = (
                        result.get("text")
                        or result.get("answer")
                        or result.get("message")
                        or "Action completed successfully."
                    )
                    return {"type": "message", "reply": reply}

                return {
                    "type": "message",
                    "reply": f"Action failed: {result.get('message', 'Unknown error')}"
                }

        # ---------- LLM Agent Decision ----------
        result = self.llm.process(msg)

        # Tool call requested by LLM
        if result.get("type") == "tool_call":

            tool = result.get("tool")
            arguments = result.get("arguments", {})

            if not tool:
                return {"type": "message", "reply": "Invalid tool request."}

            # Store for confirmation
            st.pending_action = tool
            st.pending_payload = arguments

            return {
                "type": "message",
                "reply": (
                    f"Tool request detected: {tool}\n\n"
                    f"Arguments:\n{arguments}\n\n"
                    "Reply confirm to execute or cancel."
                )
            }

        # Normal message
        if result.get("type") == "message":
            return result

        return {"type": "message", "reply": "Unexpected response."}

    # ---------------- helpers ----------------

    def _is_confirmation(self, msg: str) -> bool:
        return msg.lower().strip() in {"confirm", "yes", "ok", "proceed"}

    def _is_cancellation(self, msg: str) -> bool:
        return msg.lower().strip() in {"cancel", "no", "stop", "abort"}