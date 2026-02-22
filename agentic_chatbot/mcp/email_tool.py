
import os
import smtplib
from email.message import EmailMessage


def send_email(args: dict):
    to_addr = (args.get("to") or "").strip()
    subject = (args.get("subject") or "").strip()
    body = (args.get("body") or "").strip()

    if not to_addr or not subject or not body:
        return {"status": "error", "message": "Missing fields"}

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM") or user

    try:
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        print("📧 Email sent via Gmail SMTP")
        return {"status": "success", "message": "Email sent"}

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "message": "SMTP auth failed. Use Gmail App Password, not Gmail login password."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}