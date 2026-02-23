# agent/orchestrator.py
from agent.state_store import get_state, clear_state
from mcp.email_tool import send_email


class AgentOrchestrator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def handle_message(self, conversation_id, message: str):
        cid = conversation_id or "default"
        msg = (message or "").strip()

        if not msg:
            return {"type": "message", "reply": "Please type a message."}

        st = get_state(cid)

        # ---------- Pending email flow ----------
        if st.pending_email:
            pending = st.pending_email

            # CONFIRM -> send
            if self._is_confirmation(msg):
                result = send_email(pending)

                # Always clear pending state after attempting to send
                st.pending_email = None
                st.pending_action = None

                if result.get("status") == "success":
                    return {"type": "message", "reply": "Email sent successfully."}
                return {"type": "message", "reply": f"Email failed: {result.get('message')}"}

            # CANCEL -> discard pending
            if self._is_cancellation(msg):
                st.pending_email = None
                st.pending_action = None
                return {"type": "message", "reply": "Cancelled. Email was not sent."}

            # EDIT -> revise draft
            if self._looks_like_edit(msg):
                updated = self.llm.draft_email(msg, existing_draft=pending)

                # harden output
                updated = {
                    "to": (updated.get("to") or pending.get("to") or "").strip(),
                    "subject": (updated.get("subject") or pending.get("subject") or "").strip(),
                    "body": (updated.get("body") or pending.get("body") or "").strip(),
                }

                st.pending_email = updated
                st.pending_action = "email_confirm"
                return {"type": "message", "reply": self._format_preview(updated)}

            # Anything else while pending -> guide user
            return {
                "type": "message",
                "reply": (
                    "You have a draft ready.\n"
                    "Reply with: confirm (send), edit <changes>, or cancel.\n\n"
                    + self._format_preview(pending)
                ),
            }

        # ---------- New email request ----------
        if self._looks_like_email_request(msg):
            draft = self.llm.draft_email(msg)

            # harden draft
            draft = {
                "to": (draft.get("to") or "").strip(),
                "subject": (draft.get("subject") or "").strip(),
                "body": (draft.get("body") or "").strip(),
            }

            st.pending_email = draft
            st.pending_action = "email_confirm"
            return {"type": "message", "reply": self._format_preview(draft)}

        # ---------- Normal chat ----------
        out = self.llm.generate_reply(msg)
        if isinstance(out, dict) and "type" in out and "reply" in out:
            return out
        return {"type": "message", "reply": str(out)}

    # ---------------- helpers ----------------

    def _is_confirmation(self, msg: str) -> bool:
        m = msg.lower().strip()
        return m in {"confirm", "yes", "send", "ok", "okay", "go ahead", "sure"}

    def _is_cancellation(self, msg: str) -> bool:
        m = msg.lower().strip()
        return m in {"cancel", "no", "stop", "dont send", "don't send", "discard"}

    def _looks_like_email_request(self, msg: str) -> bool:
        m = msg.lower()
        return (
            m.startswith("send email")
            or m.startswith("draft email")
            or "send an email" in m
            or "send email to" in m
            or "email to" in m
        )

    def _looks_like_edit(self, msg: str) -> bool:
        m = msg.lower().strip()

    # explicit edit
        if m == "edit" or m.startswith("edit "):
            return True

    # common edit intents (short/long/formal, rewrite, etc.)
        edit_phrases = [
            "change subject", "update subject", "make subject", "subject more", "rewrite subject",
            "change the subject", "update the subject", "make the subject",
            "rewrite the body", "change body", "update body",
            "make it shorter", "make it short", "shorten", "make it concise", "reduce it",
            "make it longer", "expand it",
            "make it formal", "make it more formal", "formalize",
            "rewrite", "rephrase", "polish",
            "change recipient", "update recipient", "change to ", "update to ",
    ]

        return any(p in m for p in edit_phrases)

    def _format_preview(self, draft: dict) -> str:
        return (
            "Here is the draft:\n\n"
            f"To: {draft.get('to','')}\n"
            f"Subject: {draft.get('subject','')}\n"
            f"Body:\n{draft.get('body','')}\n\n"
            "Reply: confirm (to send), edit <changes>, or cancel."
        )