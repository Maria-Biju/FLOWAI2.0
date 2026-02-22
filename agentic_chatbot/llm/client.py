import os
import json
import re
import requests
from typing import Any, Dict, Optional

try:
    from google import genai
except Exception:
    genai = None


class LLMClient:
    """
    Two capabilities:
    1) generate_reply(message) -> {"type":"message","reply":"..."}
    2) draft_email(user_message, existing_draft=None) -> {"to":"...","subject":"...","body":"..."}

    Notes:
    - This client NEVER returns tool_call JSON.
    - Tool execution must be handled by orchestrator (send_email tool).
    """

    def __init__(self):
        # Ollama
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

        # Gemini (optional fallback)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_client = None

        if self.gemini_key and genai is not None:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception:
                self.gemini_client = None

        # Ollama request tuning (safe defaults for 8GB RAM)
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30s")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))
        self.num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "160"))

    # -----------------------
    # Ollama call
    # -----------------------
    def _post_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "num_predict": self.num_predict,
                # reduce ram spikes a bit
                "temperature": 0.2,
                "top_p": 0.9,
            },
        }

        r = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

    # -----------------------
    # Robust JSON extraction
    # -----------------------
    def _extract_json_obj(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try hard to extract a single JSON object from an LLM response.
        Handles cases where model outputs extra text around JSON.
        """
        if not text:
            return None

        # 1) Fast path: whole string is JSON
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # 2) Find all {...} candidates and try parsing largest-first
        candidates = re.findall(r"\{[\s\S]*?\}", text)
        candidates = sorted(candidates, key=len, reverse=True)

        for c in candidates:
            try:
                obj = json.loads(c)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue

        return None

    # -----------------------
    # Normal chat response
    # -----------------------
    def generate_reply(self, message: str) -> Dict[str, str]:
        """
        Always returns:
        {"type":"message","reply":"..."}
        """
        user_msg = (message or "").strip()

        system_prompt = (
            "You are FLOWAI assistant.\n"
            "Return ONLY one valid JSON object in this exact format:\n"
            '{"type":"message","reply":"..."}\n'
            "Rules:\n"
            "- No markdown\n"
            "- No extra keys\n"
            "- reply must be plain text\n"
            "- Do NOT output tool calls\n"
        )

        prompt = f"{system_prompt}\nUser: {user_msg}"

        # 1) Ollama
        try:
            text = self._post_ollama(prompt)
            obj = self._extract_json_obj(text)
            if obj and obj.get("type") == "message" and isinstance(obj.get("reply"), str):
                return {"type": "message", "reply": obj["reply"].strip()}
        except Exception:
            pass

        # 2) Gemini fallback
        try:
            if not self.gemini_client:
                raise RuntimeError("Gemini client not available.")
            resp = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=user_msg
            )
            reply = (resp.text or "").strip() or "No response."
            return {"type": "message", "reply": reply}
        except Exception as e:
            return {
                "type": "message",
                "reply": "LLM is currently unavailable (quota/connection). Try: send email / edit / confirm / cancel."
}

    # -----------------------
    # Email draft generation
    # -----------------------
    def draft_email(self, user_message: str, existing_draft: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Returns only:
        {"to":"...","subject":"...","body":"..."}
        No tool calls.

        existing_draft: use when user says "make the subject more formal" etc.
        """
        user_msg = (user_message or "").strip()
        existing = existing_draft or {"to": "", "subject": "", "body": ""}

        system_prompt = (
            "You are an email drafting assistant.\n"
            "Your job: produce an email draft.\n\n"
            "Return ONLY valid JSON:\n"
            '{"to":"...","subject":"...","body":"..."}\n'
            "Rules:\n"
            "- No markdown\n"
            "- No extra keys\n"
            "- Keep body concise and professional\n"
            "- If user asks to edit only one field, keep other fields from existing draft\n"
        )

        prompt = (
            f"{system_prompt}\n"
            f"Existing draft:\n"
            f"to: {existing.get('to','')}\n"
            f"subject: {existing.get('subject','')}\n"
            f"body: {existing.get('body','')}\n\n"
            f"User request:\n{user_msg}"
        )

        # 1) Ollama
        try:
            text = self._post_ollama(prompt)
            obj = self._extract_json_obj(text)
            if obj and all(k in obj for k in ("to", "subject", "body")):
                return {
                    "to": str(obj["to"]).strip(),
                    "subject": str(obj["subject"]).strip(),
                    "body": str(obj["body"]).strip(),
                }
        except Exception:
            pass

        # 2) Gemini fallback
        try:
            if not self.gemini_client:
                raise RuntimeError("Gemini client not available.")
            resp = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )
            text = (resp.text or "").strip()
            obj = self._extract_json_obj(text)
            if obj and all(k in obj for k in ("to", "subject", "body")):
                return {
                    "to": str(obj["to"]).strip(),
                    "subject": str(obj["subject"]).strip(),
                    "body": str(obj["body"]).strip(),
                }
        except Exception:
            pass

        # final fallback (no LLM available)
        # (Try to extract email and subject from text minimally)
        to_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_msg)
        to_addr = to_match.group(0) if to_match else (existing.get("to") or "unknown@example.com")

        subj = existing.get("subject") or "Email Draft"
        if "subject" in user_msg.lower():
            # super basic: "subject X" or "subject: X"
            m = re.search(r"subject\s*[:\-]\s*(.+)$", user_msg, re.IGNORECASE)
            if m:
                subj = m.group(1).strip()

        body = existing.get("body") or "Hello,\n\nPlease find the details below.\n\nRegards,\n"

        return {"to": to_addr, "subject": subj, "body": body}
