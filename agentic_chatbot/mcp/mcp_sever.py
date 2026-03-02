# mcp/mcp_sever.py
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional
from mcp.tools_registry import TOOLS, TOOLS_METADATA

app = FastAPI()


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


@app.post("/")
def handle_rpc(request: JSONRPCRequest):

    # Validate JSON-RPC version
    if request.jsonrpc != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid JSON-RPC version"},
            "id": request.id,
        }

    # ---- tools/list ----
    if request.method == "tools/list":
        

        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": TOOLS_METADATA
            },
            "id": request.id,
        }

    # ---- tools/call ----
    if request.method == "tools/call":
        if not request.params:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Missing params"},
                "id": request.id,
            }

        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Tool not found"},
                "id": request.id,
            }

        try:
            result = TOOLS[tool_name](arguments)

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request.id,
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request.id,
            }

    # ---- Unknown Method ----
    return {
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": "Method not found"},
        "id": request.id,
    }