{
  "name": "create_note",
  "description": "Save a note.",
  "input_schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "content": {"type": "string"},
      "tags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["content"]
  }
}