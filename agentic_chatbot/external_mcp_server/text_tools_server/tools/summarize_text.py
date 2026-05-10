import requests
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


def summarize_text(args: dict):

    text = args.get("text", "")

    if not text:
        return {
            "status": "error",
            "message": "Text is required for summarization"
        }

    prompt = f"""
Summarize the following text in 2 or 3 short sentences.

Text:
{text}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        summary = data.get("response", "").strip()

        return {
            "status": "success",
            "text": summary,
            "message": summary
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


TOOL = {
    "name": "summarize_text",
    "description": "Summarize long text using the Ollama language model",
    "schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text that needs to be summarized"
            }
        },
        "required": ["text"]
    },
    "handler": summarize_text
}