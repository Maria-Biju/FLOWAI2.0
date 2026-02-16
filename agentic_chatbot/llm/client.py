import os
from openai import OpenAI

class LLMClient:
    def __init__(self):
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=key)

    def generate_reply(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
