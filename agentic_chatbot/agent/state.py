from typing import Optional, Dict

class ConversationState:
    def __init__(self):
        self.pending_action: Optional[str] = None
        self.data: Dict = {}
