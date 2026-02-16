# FLOWAI
A workflow automation system for non-technical users

The LLM must always respond in this JSON format:

{
  "thought": "internal reasoning",
  "action": "ask_user | tool_call | finish",
  "tool_name": "email.send",
  "tool_args": {
    "to": ["user@example.com"],
    "subject": "Hello",
    "body": "Test email"
  },
  "message": "Message to show the user"
}