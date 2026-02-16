from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from agent.orchestrator import AgentOrchestrator

app = Flask(__name__)
agent = AgentOrchestrator()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    conversation_id = data.get("conversation_id")
    message = data.get("message")

    reply = agent.handle_message(conversation_id, message)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=8000)
