import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USE_STARTTLS = os.getenv("SMTP_USE_STARTTLS", "true").lower() == "true"
_SMTP_USE_AUTH = os.getenv("SMTP_USE_AUTH", "true").lower() == "true"
_SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Sales AI")
_SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", _SMTP_USERNAME)

_DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def _parse_subject_and_body(email_text: str) -> tuple[str, str]:
    """
    Splits raw email text into (subject, body).
    Expects the first line to start with 'Subject:'.
    Falls back to a generic subject if none is found.
    """
    lines = email_text.strip().splitlines()

    if lines and lines[0].strip().lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body = "\n".join(lines[1:]).strip()
        return subject, body

    return "Following up", email_text.strip()


def send_email(to_address: str, email_text: str) -> dict:
    """
    Sends an email via SMTP, or prints it to the console if DRY_RUN=true.
    Returns a small status dict for the caller to inspect/log.
    """
    subject, body = _parse_subject_and_body(email_text)

    if _DRY_RUN:
        print("=" * 70)
        print("DRY RUN — email NOT actually sent")
        print(f"To:      {to_address}")
        print(f"From:    {_SMTP_FROM_NAME} <{_SMTP_FROM_EMAIL}>")
        print(f"Subject: {subject}")
        print("-" * 70)
        print(body)
        print("=" * 70)
        return {"status": "ok", "dry_run": True, "to": to_address, "subject": subject}

    msg = MIMEMultipart()
    msg["From"] = f"{_SMTP_FROM_NAME} <{_SMTP_FROM_EMAIL}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=15) as server:
            if _SMTP_USE_STARTTLS:
                server.starttls()
            if _SMTP_USE_AUTH:
                server.login(_SMTP_USERNAME, _SMTP_PASSWORD)
            server.sendmail(_SMTP_FROM_EMAIL, [to_address], msg.as_string())
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Failed to send email via SMTP: {exc}") from exc

    return {"status": "ok", "dry_run": False, "to": to_address, "subject": subject}
