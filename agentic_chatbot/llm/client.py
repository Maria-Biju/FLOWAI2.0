import os
import json
import re
import requests
from typing import Any, Dict, Optional, List


class LLMClient:
    """
    Agent-style client.

    Returns one of:
    1) {"type":"message","reply":"..."}
    2) {"type":"tool_call","tool":"...","arguments":{...}}
    3) {"type":"workflow","steps":[...]}
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30s")

    def _post_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": 300,
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

    def process(self, message: str, tools_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        tool_descriptions = []

        for t in tools_metadata:
            block = {
                "name": t.get("name"),
                "description": t.get("description"),
                "schema": t.get("schema", {})
            }
            tool_descriptions.append(block)

        system_prompt = f"""
You are FLOWAI Agent.

Available MCP tools:
{json.dumps(tool_descriptions, indent=2)}

You MUST respond with ONLY valid JSON.
No markdown.
No extra explanations.
No text outside JSON.

Allowed formats:

For a workflow:
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

For a single tool call:
{{
  "type": "tool_call",
  "tool": "tool_name",
  "arguments": {{}}
}}

For a normal reply:
{{
  "type": "message",
  "reply": "..."
}}

Rules:
- Only use tools from the available MCP tools list.
- If the task needs more than one tool, return a workflow.
- If the task is simple and only one tool is enough, return tool_call.
- If no tool is needed, return a normal message.

IMPORTANT WORKFLOW RULES:
- If one step uses output from an earlier step, you MUST use placeholders in this exact format:
  {{step1.text}}
  {{step2.text}}
  {{step3.text}}

- Use ONLY the field name "text" when passing text output from one tool to another.
- Do NOT invent custom field names.
- Do NOT use placeholders like:
  {{step4.uppercase_test_result}}
  {{step2.output}}
  {{step1.answer}}
- Always use {{stepN.text}} for text-producing tools.

Tools that produce text output include:
- google_search
- summarize_text
- uppercase_text

Examples:

Example 1:
User: Convert hello world to uppercase
Response:
{{
  "type": "tool_call",
  "tool": "uppercase_text",
  "arguments": {{
    "text": "hello world"
  }}
}}

Example 2:
User: Search the largest mountain in the world and send the result to my email
Response:
{{
  "type": "workflow",
  "steps": [
    {{
      "step": 1,
      "tool": "google_search",
      "arguments": {{
        "query": "largest mountain in the world"
      }}
    }},
    {{
      "step": 2,
      "tool": "send_email",
      "arguments": {{
        "to": "user@example.com",
        "subject": "Largest Mountain Search Result",
        "body": "{{step1.text}}"
      }}
    }}
  ]
}}

Example 3:
User: Search the largest mountain in the world, summarize it, convert it to uppercase, and send it to my email
Response:
{{
  "type": "workflow",
  "steps": [
    {{
      "step": 1,
      "tool": "google_search",
      "arguments": {{
        "query": "largest mountain in the world"
      }}
    }},
    {{
      "step": 2,
      "tool": "summarize_text",
      "arguments": {{
        "text": "{{step1.text}}"
      }}
    }},
    {{
      "step": 3,
      "tool": "uppercase_text",
      "arguments": {{
        "text": "{{step2.text}}"
      }}
    }},
    {{
      "step": 4,
      "tool": "send_email",
      "arguments": {{
        "to": "user@example.com",
        "subject": "Largest Mountain Result",
        "body": "{{step3.text}}"
      }}
    }}
  ]
}}
"""

        prompt = system_prompt + "\nUser: " + message.strip()

        try:
            text = self._post_ollama(prompt)
            print("LLM RAW OUTPUT:\n", text)

            obj = self._extract_json(text)

            if not obj:
                return {"type": "message", "reply": "I could not process that."}

            if obj.get("type") in {"tool_call", "message", "workflow"}:
                return obj

            return {"type": "message", "reply": "Invalid response format."}

        except Exception as e:
            return {"type": "message", "reply": f"LLM error: {str(e)}"}