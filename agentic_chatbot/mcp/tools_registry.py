from tools.email_tool import send_email
from tools.notify_tool import notify
from tools.create_note import save_note
# from tools.create_reminder import set_reminder

TOOLS = {
    "send_email": send_email,
    "notify": notify,
    "save_note": save_note,
#   "set_reminder": set_reminder,
}