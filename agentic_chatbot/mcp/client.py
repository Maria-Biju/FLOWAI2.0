from streamlit import title

from mcp.email_tool import *
class MCPClient:

    def call_tool(self, tool_name: str, tool_args: dict):

        if tool_name == "email.send":
            return send_email(tool_args)
        
        if tool_name == "note.save":
            return save_note(tool_args)
        
        if tool_name == "note.get_all":
            return get_all_notes()
        
        if tool_name == "note.get_by_id":
            return get_note_by_id(tool_args.get("id"))
        
        if tool_name == "note.get_by_title":
            return get_note_by_title(tool_args.get("title"))
        
        if tool_name == "reminder.set":
            return set_reminder(
                title=tool_args.get("title"),
                remind_at=tool_args.get("remind_at"),
                message=tool_args.get("message", "")
            )

        raise ValueError(f"Unknown tool: {tool_name}")
    

    
    def save_note_tool(args: dict):
        title = args.get("title")
        content = args.get("content")

        if not title or not content:
            return {"status": "error", "message": "Title and content required"}

        return save_note(title, content)
