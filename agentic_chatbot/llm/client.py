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
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
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

        tool_descriptions = ""

        for t in tools:

            tool_descriptions += f"\n{t['name']}\n"
            tool_descriptions += f"description: {t['description']}\n"
            tool_descriptions += "arguments:\n"

            props = t["schema"]["properties"]

            tool_descriptions += json.dumps(props, indent=2)
            tool_descriptions += "\n\n"

        system_prompt = f"""
You are FLOWAI Agent.

Available tools:
{tool_descriptions}

You MUST respond with ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.
Do NOT include text before or after the JSON.
Only include tools that are strictly required to complete the task.
Do NOT add unnecessary tools.
Do NOT add steps unrelated to the user's request.

Allowed formats:

For multi-step tasks:

{{
 "type": "workflow",
 "steps": [
  {{
   "step": 1,
   "tool": "tool_name",
   "arguments": {{}}
  }}
 ]
}}

For single tool calls:

{{
 "type": "tool_call",
 "tool": "tool_name",
 "arguments": {{}}
}}

For normal chat:

{{
 "type": "message",
 "reply": "..."
}}

If the request requires using information from one tool in another tool,
you MUST return a workflow instead of a single tool call.

When a tool produces information that will be used in another step,
reference it using {{step1.field}}.

Example:
Step1: google_search  
Step2: send_email with body "{{step1.text}}"

Workflows may optionally include a schedule field.

Example:

{{
 "type": "workflow",
 "schedule": {{
   "type": "once",
   "run_at": "ISO datetime"
 }},
 "steps": [
  {{
   "step": 1,
   "tool": "tool_name",
   "arguments": {...}
  }}
 ]
}}
"""

        prompt = system_prompt + "\nUser: " + message

        try:
            text = self._post_ollama(prompt)
            print("LLM RAW OUTPUT:\n", text)
            obj = self._extract_json(text)

            if not obj:
                return {"type": "message", "reply": "I could not process that."}

            if obj.get("type") == "tool_call":
                return obj

            if obj.get("type") == "message":
                return obj
            if obj.get("type") == "workflow":
                return obj

            return {"type": "message", "reply": "Invalid response format."}

        except Exception as e:
            return {
                "type": "message",
                "reply": f"LLM error: {str(e)}"
            }