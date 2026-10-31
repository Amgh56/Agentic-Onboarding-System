"""The only code that talks to a real mailbox: SMTP to send, IMAP to read."""

import email
import imaplib
import smtplib
from datetime import date
from email.message import EmailMessage
from email.policy import default
from email.utils import parseaddr


def send(settings, password: str, to: str, subject: str, body: str, files: list[tuple[str, bytes]]) -> None:
    message = EmailMessage()
    message["From"] = settings.email_address
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    for filename, data in files:
        message.add_attachment(data, maintype="application", subtype="octet-stream", filename=filename)

    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.login(settings.email_address, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(settings.email_address, password)
            smtp.send_message(message)


def check_login(settings, password: str) -> None:
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port, timeout=30) as imap:
        imap.login(settings.email_address, password)


def fetch(settings, password: str, since: date) -> list[bytes]:
    """Raw emails in the inbox since a date. Read-only, so nothing is marked as read."""
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port, timeout=30) as imap:
        imap.login(settings.email_address, password)
        imap.select("INBOX", readonly=True)
        _, found = imap.search(None, "SINCE", since.strftime("%d-%b-%Y"))
        raw_emails = []
        for number in found[0].split():
            _, parts = imap.fetch(number, "(BODY.PEEK[])")
            raw_emails.append(parts[0][1])
        return raw_emails


def parse(raw: bytes) -> dict:
    message = email.message_from_bytes(raw, policy=default)
    body_part = message.get_body(preferencelist=("plain", "html"))
    return {
        "message_id": str(message.get("Message-ID", "")).strip(),
        "from_address": parseaddr(str(message.get("From", "")))[1].lower(),
        "subject": str(message.get("Subject", "")),
        "body": body_part.get_content() if body_part else "",
        "attachments": [
            (part.get_filename() or "attachment", part.get_content_type(), part.get_payload(decode=True) or b"")
            for part in message.iter_attachments()
        ],
    }
