import os
import requests


class MCPClient:
    def __init__(self):
        # Local MCP server
        self.base_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001").rstrip("/")

        # External MCP servers (comma-separated in .env)
        raw_external = os.getenv("EXTERNAL_MCP_SERVERS", "").strip()

        if raw_external:
            self.external_servers = [url.strip().rstrip("/") for url in raw_external.split(",") if url.strip()]
        else:
            self.external_servers = []

        # Tool routing map:
        # tool_name -> server_url
        self.tool_server_map = {}

    def _rpc(self, server_url: str, method: str, params=None):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": 1
        }

        if params is not None:
            payload["params"] = params

        r = requests.post(server_url + "/", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    def list_tools(self):
        """
        Discover tools from:
        1. local MCP server
        2. external MCP servers

        Returns merged list of tools, each tool annotated with:
        - server_url
        - source (local/external)
        """
        all_tools = []
        self.tool_server_map = {}

        servers = [(self.base_url, "local")] + [(url, "external") for url in self.external_servers]

        for server_url, source in servers:
            try:
                data = self._rpc(server_url, "tools/list")

                if "error" in data:
                    continue

                tools = data.get("result", {}).get("tools", [])

                for tool in tools:
                    tool_name = tool.get("name")
                    if not tool_name:
                        continue

                    # Add routing info
                    tool_with_meta = dict(tool)
                    tool_with_meta["server_url"] = server_url
                    tool_with_meta["source"] = source

                    all_tools.append(tool_with_meta)
                    self.tool_server_map[tool_name] = server_url

            except Exception as e:
                print(f"[MCPClient] Failed to fetch tools from {server_url}: {e}")
                continue

        return all_tools

    def call_tool(self, tool_name: str, arguments: dict):
        """
        Route tool call to the correct MCP server.
        If tool routing is unknown, fallback to local MCP server.
        """
        server_url = self.tool_server_map.get(tool_name)
        if not server_url:
            self.list_tools()
            server_url = self.tool_server_map.get(tool_name)

        candidate_servers = []
        if server_url:
            candidate_servers.append(server_url)

        candidate_servers.extend([self.base_url] + [url for url in self.external_servers if url != self.base_url])

        last_error = None
        attempted = set()

        for url in candidate_servers:
            if url in attempted:
                continue
            attempted.add(url)

            try:
                data = self._rpc(
                    url,
                    "tools/call",
                    {
                        "name": tool_name,
                        "arguments": arguments
                    }
                )

                if "error" in data:
                    error_message = data["error"].get("message", "Unknown error")
                    if error_message == "Tool not found":
                        continue
                    return {
                        "status": "error",
                        "message": error_message
                    }

                result = data.get("result")
                if result is None:
                    return {"status": "error", "message": "Tool returned no result"}

                return result

            except Exception as e:
                last_error = e
                continue

        message = str(last_error) if last_error else f"Tool not found: {tool_name}"
        return {"status": "error", "message": message}