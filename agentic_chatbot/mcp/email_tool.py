def send_email(args: dict):

    print("📧 Sending email...")
    print("To:", args.get("to"))
    print("Subject:", args.get("subject"))
    print("Body:", args.get("body"))

    return {
        "status": "success",
        "message": "Email sent successfully"
    }
