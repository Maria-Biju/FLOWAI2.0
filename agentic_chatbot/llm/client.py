import os
import json
import re
import requests
from typing import Any, Dict, Optional


class LLMClient:
    """
    Agent-style client.

    Can return:
    1) {"type":"message","reply":"..."}
    2) {"type":"tool_call","tool":"...","arguments":{...}}
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b-q4_0")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30s")

    def fetch_tools_metadata(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }

        r = requests.post("http://127.0.0.1:8001/", json=payload)
        return r.json()["result"]["tools"]

    # -----------------------
    # Ollama Call
    # -----------------------
    def _post_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "format": "json",  # 🔥 Force strict JSON
            "options": {
                "temperature": 0.0,
                "num_predict": 200,
                "num_ctx": 2048,
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
    # Extract JSON
    # -----------------------
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
        return None

    # -----------------------
    # MAIN AGENT ENTRY
    # -----------------------
    def process(self, message: str):

        tools = self.fetch_tools_metadata()

        tool_descriptions = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tools
        ])

        system_prompt = f"""
You are FLOWAI Agent.

You MUST call a tool when the user request requires external data or stored information.

Available tools:
{tool_descriptions}

You MUST respond ONLY in valid JSON.
No explanations.
No conversational text.

If tool is required, respond EXACTLY like:

{{
  "type": "tool_call",
  "tool": "tool_name",
  "arguments": {{ ... }}
}}

If no tool is required:

{{
  "type": "message",
  "reply": "..."
}}

Never describe calling a tool.
Never say you will call a tool.
Return JSON only.
"""

        prompt = system_prompt + "\nUser: " + message

        try:
            text = self._post_ollama(prompt)
            obj = self._extract_json(text)

            if not obj:
                return {"type": "message", "reply": "I could not process that."}

            if obj.get("type") == "tool_call":
                return obj

            if obj.get("type") == "message":
                return obj

            return {"type": "message", "reply": "Invalid response format."}

        except Exception as e:
            return {
                "type": "message",
                "reply": f"LLM error: {str(e)}"
            }