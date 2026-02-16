from llm.client import LLMClient

class AgentOrchestrator:
    def __init__(self):
        self.llm = LLMClient()

    def handle_message(self, conversation_id, message):
        return self.llm.generate_reply(message)
