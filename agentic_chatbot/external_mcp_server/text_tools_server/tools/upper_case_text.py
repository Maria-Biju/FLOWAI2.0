def uppercase_text(args: dict):

    text = args.get("text", "")

    if not text:
        return {
            "status": "error",
            "message": "Text is required"
        }

    upper = text.upper()

    return {
        "status": "success",
        "text": upper,
        "message": upper
    }


TOOL = {
    "name": "uppercase_text",
    "description": "Convert text to uppercase",
    "schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert"
            }
        },
        "required": ["text"]
    },
    "handler": uppercase_text
}