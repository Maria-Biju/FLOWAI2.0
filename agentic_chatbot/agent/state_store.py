from agent.state import ConversationState

STATE_STORE = {}

def get_state(conversation_id: str) -> ConversationState:
    if conversation_id not in STATE_STORE:
        STATE_STORE[conversation_id] = ConversationState()
    return STATE_STORE[conversation_id]

def clear_state(conversation_id: str):
    STATE_STORE.pop(conversation_id, None)
