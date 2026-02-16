from fastapi import FastAPI
from agent.orchestrator import AgentOrchestrator
from models.chat_request import ChatRequest

app = FastAPI()
agent = AgentOrchestrator()

@app.post("/chat")
def chat(request: ChatRequest):
    print("User:", request.message)

    reply = agent.handle_message(
        request.conversation_id,
        request.message
    )

    print("LLM:", reply)
    return {"reply": reply}
