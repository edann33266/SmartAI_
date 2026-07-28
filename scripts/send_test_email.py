import os
import sys

from dotenv import load_dotenv

from email_sender import send_email


def main() -> int:
    load_dotenv()

    to_address = None
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        to_address = sys.argv[1].strip()
    else:
        to_address = (os.getenv("TEST_EMAIL_TO") or "").strip()

    if not to_address:
        print("Usage: py send_test_email.py someone@example.com")
        print("Or set TEST_EMAIL_TO in .env")
        return 2

    email_text = (
        "Subject: SalesAI SMTP test\n"
        "\n"
        "This is a test email sent from SalesAI via SMTP.\n"
        "If you received this, your SMTP configuration is working.\n"
    )

    send_email(to_address=to_address, email_text=email_text)
    print("Triggered send_email() successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
