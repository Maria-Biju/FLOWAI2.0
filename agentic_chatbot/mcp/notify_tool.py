from win10toast import ToastNotifier

_toaster = ToastNotifier()

def notify(args: dict):
    title = args.get("title", "FLOWAI Reminder")
    message = args.get("message", "")
    duration = int(args.get("duration", 6))

    _toaster.show_toast(title, message, duration=duration, threaded=True)

    return {"status": "success", "message": "Notification shown"}