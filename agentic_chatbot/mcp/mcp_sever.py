from fastapi import FastAPI
from tools_registry import TOOLS
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()


@app.post("/call")
def call_tool(data: dict):
    tool = data.get("tool")
    args = data.get("arguments", {})

    if tool not in TOOLS:
        return {"status": "error", "message": "Unknown tool"}

    return TOOLS[tool](args)