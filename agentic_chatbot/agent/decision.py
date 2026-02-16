from pydantic import BaseModel
from typing import Dict, Any, Optional

class AgentDecision(BaseModel):
    thought: str
    action: str               # ask_user | tool_call | finish
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    message: str
