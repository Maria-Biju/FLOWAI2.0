from mcp.email_tool import send_email

class MCPClient:

    def call_tool(self, tool_name: str, tool_args: dict):

        if tool_name == "email.send":
            return send_email(tool_args)

        raise ValueError(f"Unknown tool: {tool_name}")
