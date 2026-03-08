from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional

app = FastAPI()


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


def uppercase_text(args: dict):
    text = args.get("text", "")
    upper = text.upper()

    return {
        "status": "success",
        "text": upper,
        "message": upper
    }


TOOLS = {
    "uppercase_text": uppercase_text
}

TOOLS_METADATA = [
    {
        "name": "uppercase_text",
        "description": "Convert text to uppercase",
        "schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to convert"
                }
            },
            "required": ["text"]
        }
    }
]


@app.post("/")
def handle_rpc(request: JSONRPCRequest):
    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": TOOLS_METADATA
            },
            "id": request.id
        }

    if request.method == "tools/call":
        tool = request.params.get("name")
        args = request.params.get("arguments", {})

        if tool not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "error": {"message": "Tool not found"},
                "id": request.id
            }

        result = TOOLS[tool](args)

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