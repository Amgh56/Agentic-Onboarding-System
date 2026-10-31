import smtplib

from fastapi import HTTPException

from app.core.crypto import decrypt
from app.features.notifications import mail_client


def deliver(settings, to_address: str, subject: str, body: str, files: list[tuple[str, bytes]]) -> None:
    """Send one email from the company's mailbox. In test mode ("mock") it is only stored in the outbox."""
    if settings.provider == "mock":
        return
    try:
        mail_client.send(settings, decrypt(settings.password_encrypted), to_address, subject, body, files)
    except (smtplib.SMTPException, OSError) as error:
        raise HTTPException(502, f"Sending the email failed: {error}")
