# agent/state.py
from typing import Optional, Dict, Any


class ConversationState:
    """
    Per-conversation memory (in RAM).
    Used by the agent to store pending tool calls / workflows
    before confirmation.
    """
    def __init__(self):
        self.pending_action: Optional[str] = None
        self.pending_payload: Optional[Dict[str, Any]] = None
        self.data: Dict[str, Any] = {}
        
        self.last_result: Optional[Dict[str, Any]] = None
        self.preview_text: Optional[str] = None