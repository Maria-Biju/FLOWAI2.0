# server.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional
import importlib
import os

app = FastAPI()

TOOLS = {}
TOOLS_METADATA = []


# -------- Load Tools Dynamically --------
def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"external_mcp_server.text_tools_server.tools.{filename[:-3]}"
            module = importlib.import_module(module_name)

            if hasattr(module, "TOOL"):
                tool_def = module.TOOL

                TOOLS[tool_def["name"]] = tool_def["handler"]

                TOOLS_METADATA.append({
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "schema": tool_def["schema"]
                })


load_tools()


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


@app.post("/")
def handle_rpc(request: JSONRPCRequest):

    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {"tools": TOOLS_METADATA},
            "id": request.id
        }

    if request.method == "tools/call":

        tool_name = request.params.get("name")
        args = request.params.get("arguments", {})

        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "error": {"message": "Tool not found"},
                "id": request.id
            }

        result = TOOLS[tool_name](args)

        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request.id
        }

    return {
        "jsonrpc": "2.0",
        "error": {"message": "Unknown method"},
        "id": request.id
    }