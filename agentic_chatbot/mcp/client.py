# agent/mcp_client.py
import requests
import os


class MCPClient:
    def __init__(self):
        self.base_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001")

    def call_tool(self, tool_name: str, arguments: dict):
        try:
            r = requests.post(
                f"{self.base_url}/call",
                json={
                    "tool": tool_name,
                    "arguments": arguments
                },
                timeout=30
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}