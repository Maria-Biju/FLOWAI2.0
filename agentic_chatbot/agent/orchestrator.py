# agent/orchestrator.py
import re
from mcp.email_tool import send_email


class AgentOrchestrator:
    def __init__(self, llm_client):
        self.llm = llm_client
        # in-memory state: {conversation_id: {"pending_email": {...}}}
        self.state = {}

    def handle_message(self, conversation_id, message: str):
        conversation_id = conversation_id or "default"
        msg = (message or "").strip()

        # 1) CONFIRM -> send pending
        if self._has_pending_email(conversation_id) and self._is_confirmation(msg):
            pending = self.state[conversation_id]["pending_email"]
            send_email(pending)
            self.state[conversation_id] = {}
            return {"type": "message", "reply": "Email sent successfully."}

        # 2) CANCEL -> discard pending
        if self._has_pending_email(conversation_id) and self._is_cancellation(msg):
            self.state[conversation_id] = {}
            return {"type": "message", "reply": "Cancelled. Email was not sent."}

        # 3) EDIT -> revise pending draft (do NOT send)
        if self._has_pending_email(conversation_id) and self._looks_like_edit(msg):
            current = self.state[conversation_id]["pending_email"]

            # Ask LLM to revise based on existing draft + user changes
            prompt = (
                "Revise this email draft.\n\n"
                f"CURRENT DRAFT:\n"
                f"To: {current.get('to','')}\n"
                f"Subject: {current.get('subject','')}\n"
                f"Body:\n{current.get('body','')}\n\n"
                f"USER CHANGES:\n{msg}\n\n"
                "Return JSON with keys: to, subject, body."
            )

            updated = self.llm.draft_email(prompt)
            self.state[conversation_id] = {"pending_email": updated}

            return {"type": "message", "reply": self._format_preview(updated)}

        # 4) EMAIL REQUEST -> draft first, store, ask confirm
        if self._looks_like_email_request(msg):
            draft = self.llm.draft_email(msg)
            self.state[conversation_id] = {"pending_email": draft}
            return {"type": "message", "reply": self._format_preview(draft)}

        # 5) NORMAL CHAT -> return LLM dict directly
        return self.llm.generate_reply(msg)

    # ---------------- helpers ----------------

    def _has_pending_email(self, conversation_id):
        return bool(self.state.get(conversation_id, {}).get("pending_email"))

    def _is_confirmation(self, msg: str):
        m = msg.lower().strip()
        return m in {"confirm", "yes", "send", "ok", "okay", "go ahead", "sure"}

    def _is_cancellation(self, msg: str):
        m = msg.lower().strip()
        return m in {"cancel", "no", "stop", "dont send", "don't send", "discard"}

    def _looks_like_email_request(self, msg: str):
        m = msg.lower()
        return (
            m.startswith("send email")
            or m.startswith("draft email")
            or "send an email" in m
            or "send email to" in m
        )

    def _looks_like_edit(self, msg: str):
        return msg.lower().startswith("edit")

    def _format_preview(self, draft: dict) -> str:
        return (
            "Here is the draft:\n\n"
            f"To: {draft.get('to','')}\n"
            f"Subject: {draft.get('subject','')}\n"
            f"Body:\n{draft.get('body','')}\n\n"
            "Reply: confirm (to send), edit <changes>, or cancel."
        )
