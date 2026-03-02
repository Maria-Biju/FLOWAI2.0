import os
import smtplib
from email.message import EmailMessage


def send_email(args: dict):
    try:
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASS")
        from_addr = os.getenv("SMTP_FROM") or user

        if not host or not user or not password:
            return {"status": "error", "message": "SMTP configuration missing"}

        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = args.get("to")
        msg["Subject"] = args.get("subject")
        msg.set_content(args.get("body"))

        server = smtplib.SMTP(host, port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.send_message(msg)
        server.quit()

        return {"status": "success", "message": "Email sent successfully."}

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "message": "SMTP authentication failed. Use Gmail App Password."
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
TOOL = {
    "name": "send_email",
    "description": "Send an email to a recipient",
    "schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject"},
            "body": {"type": "string", "description": "Email content"}
        },
        "required": ["to", "subject", "body"]
    },
    "handler": send_email
}