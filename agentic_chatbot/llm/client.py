import os
import requests

try:
    # Optional: only needed if you really want Gemini fallback
    from google import genai
except Exception:
    genai = None


class LLMClient:
    """
    Priority:
    1) Local Ollama (recommended for your 8GB/no-GPU laptop)
    2) Gemini (only if key is set + working)
    """

    def __init__(self):
        # Ollama settings
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

        # Gemini settings (optional)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_client = None

        if self.gemini_key and genai is not None:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception:
                self.gemini_client = None

    # ---------- Local LLM (Ollama) ----------
    def _ollama_generate(self, message: str) -> str:
        r = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.ollama_model,
                "prompt": message,
                "stream": False,
            },
            timeout=180,
        )
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()

    # ---------- Gemini (fallback) ----------
    def _gemini_generate(self, message: str) -> str:
        if not self.gemini_client:
            raise RuntimeError("Gemini client not available (missing key or package).")

        resp = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=message
        )
        return (resp.text or "").strip()

    # ---------- Public API ----------
    def generate_reply(self, message: str) -> str:
        # 1) Try Ollama first
        try:
            reply = self._ollama_generate(message)
            if reply:
                return reply
        except Exception as e:
            ollama_err = str(e)
        else:
            ollama_err = None

        # 2) Fallback to Gemini
        try:
            reply = self._gemini_generate(message)
            if reply:
                return reply
            return "No response from Gemini."
        except Exception as e:
            # final: return readable error for UI
            if ollama_err:
                return f"Local LLM failed: {ollama_err} | Gemini failed: {e}"
            return f"Gemini LLM failed: {e}"
