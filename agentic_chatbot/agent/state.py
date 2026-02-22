# agent/state.py
from typing import Optional, Dict, Any


class ConversationState:
    """
    Per-conversation memory (in RAM).
    Keep this minimal so it doesn't conflict with other modules.
    """
    def __init__(self):
        self.pending_action: Optional[str] = None  # e.g., "email_confirm"
        self.data: Dict[str, Any] = {}            # generic storage (future use)

        # Email-specific
        self.pending_email: Optional[Dict[str, str]] = None
        self.pending_email_meta: Dict[str, Any] = {}  # optional metadata (future)