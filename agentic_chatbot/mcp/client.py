import requests


class MCPClient:

    def __init__(self):
        self.base_url = "http://127.0.0.1:8001"

    def call_tool(self, tool_name: str, arguments: dict):
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }

        try:
            r = requests.post(self.base_url + "/", json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()

            if "error" in data:
                return {
                    "status": "error",
                    "message": data["error"].get("message", "Unknown error")
                }

            result = data.get("result")

            if result is None:
                return {
                    "status": "error",
                    "message": "Tool returned no result"
                }

            return result

        except Exception as e:
            return {"status": "error", "message": str(e)}