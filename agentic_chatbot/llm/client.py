import os
import json
import re
import requests

try:
    from google import genai
except Exception:
    genai = None


class LLMClient:
    """
    Priority:
    1) Local Ollama
    2) Gemini fallback (optional)
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_client = None

        if self.gemini_key and genai is not None:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception:
                self.gemini_client = None

    # -----------------------
    # Helpers
    # -----------------------
    def _post_ollama(self, prompt: str) -> str:
        r = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": self.ollama_model, "prompt": prompt, "stream": False, "keep_alive": "30s", "options": {
        "num_predict": 120
    }},
            timeout=180,
        )
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

    def _extract_json(self, s: str) -> str:
        # grabs first {...} block
        m = re.search(r"\{.*\}", s, re.DOTALL)
        return m.group(0) if m else "{}"

    # -----------------------
    # Normal chat (no tool calls)
    # Returns dict: {"type":"message","reply":"..."}
    # -----------------------
    def generate_reply(self, message: str) -> dict:
        system_prompt = """
You are FLOWAI assistant.

Return ONLY one valid JSON object in this exact format:
{"type":"message","reply":"..."}
Rules:
- No markdown
- No extra keys
- reply must be plain text
"""
        prompt = system_prompt + "\nUser: " + (message or "").strip()

        # 1) Try Ollama
        try:
            text = self._post_ollama(prompt)
            obj = json.loads(self._extract_json(text))
            if isinstance(obj, dict) and obj.get("type") == "message" and "reply" in obj:
                return obj
        except Exception:
            pass

        # 2) Fallback Gemini (optional)
        try:
            if not self.gemini_client:
                raise RuntimeError("Gemini client not available.")
            resp = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=message
            )
            reply = (resp.text or "").strip() or "No response."
            return {"type": "message", "reply": reply}
        except Exception as e:
            return {"type": "message", "reply": f"LLM failed: {e}"}

    # -----------------------
    # Email draft generation
    # Returns dict: {"to":"...","subject":"...","body":"..."}
    # -----------------------
    def draft_email(self, user_message: str) -> dict:
        system_prompt = """
You are an email drafting assistant.

Extract 'to', 'subject', and 'body' from the user's request.
If missing info, make sensible placeholders, but keep body concise.

Return ONLY valid JSON:
{"to":"...","subject":"...","body":"..."}
Rules:
- No markdown
- No extra keys
"""
        prompt = system_prompt + "\nUser request: " + (user_message or "").strip()

        # 1) Try Ollama
        try:
            text = self._post_ollama(prompt)
            obj = json.loads(self._extract_json(text))
            if isinstance(obj, dict) and all(k in obj for k in ("to", "subject", "body")):
                return {
                    "to": str(obj["to"]).strip(),
                    "subject": str(obj["subject"]).strip(),
                    "body": str(obj["body"]).strip(),
                }
        except Exception:
            pass

        # 2) Fallback Gemini
        try:
            if not self.gemini_client:
                raise RuntimeError("Gemini client not available.")
            resp = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )
            text = (resp.text or "").strip()
            obj = json.loads(self._extract_json(text))
            if isinstance(obj, dict) and all(k in obj for k in ("to", "subject", "body")):
                return obj
        except Exception:
            pass

        # final fallback
        return {"to": "unknown@example.com", "subject": "Draft Email", "body": "Please provide the email body."}
