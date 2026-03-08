try:
    from win10toast import ToastNotifier
    _toaster = ToastNotifier()
    HAS_TOAST = True
except Exception:
    HAS_TOAST = False


def notify(args: dict):
    title = args.get("title", "FLOWAI")
    message = args.get("message", "")
    duration = int(args.get("duration", 6))

    if HAS_TOAST:
        _toaster.show_toast(title, message, duration=duration, threaded=True)
    else:
        print(f"[NOTIFY FALLBACK] {title}: {message}")

    return {"status": "success", "message": "Notification shown"}


TOOL = {
    "name": "notify",
    "description": "Show a local desktop notification",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Notification title"},
            "message": {"type": "string", "description": "Notification message"},
            "duration": {"type": "integer", "description": "Notification duration in seconds"}
        },
        "required": ["title", "message"]
    },
    "handler": notify
}