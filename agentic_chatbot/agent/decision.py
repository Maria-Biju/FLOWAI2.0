# agent/decision.py
from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal


class AgentDecision(BaseModel):
    """
    Backwards-compatible decision object.

    action:
      - ask_user: ask for missing info / confirmation
      - tool_call: invoke an MCP tool
      - finish: normal reply to user
    """
    thought: str = ""
    action: Literal["ask_user", "tool_call", "finish"] = "finish"
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    message: str = ""