import hashlib
import re
import imaplib
import smtplib

from fastapi import HTTPException
from sqlmodel import Session, or_, select

from app.core.crypto import decrypt, encrypt
from app.features.candidates import service as candidates_service
from app.features.departments import service as departments_service
from app.features.documents import service as documents_service
from app.features.notifications import email_sender, mail_client
from app.features.notifications.model import Email, EmailSettings, InboxMessage
from app.features.notifications.schema import EmailSettingsSave

# ---------- settings


def find_settings(session: Session, company_id: int) -> EmailSettings | None:
    return session.exec(select(EmailSettings).where(EmailSettings.company_id == company_id)).first()


def get_settings(session: Session, company_id: int) -> EmailSettings:
    settings = find_settings(session, company_id)
    if not settings:
        raise HTTPException(404, "Email is not set up for this company")
    return settings


def save_settings(session: Session, company_id: int, data: EmailSettingsSave) -> EmailSettings:
    settings = find_settings(session, company_id) or EmailSettings(company_id=company_id, email_address=data.email_address)
    if data.password:
        settings.password_encrypted = encrypt(data.password)
    if data.provider == "smtp" and not settings.password_encrypted:
        raise HTTPException(400, "Add the email app password")

    settings.provider = data.provider
    settings.email_address = data.email_address.strip()
    settings.smtp_host, settings.smtp_port = data.smtp_host, data.smtp_port
    settings.imap_host, settings.imap_port = data.imap_host, data.imap_port
    settings.allowed_recipients = [a.strip().lower() for a in data.allowed_recipients if a.strip()]
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def settings_read(settings: EmailSettings) -> dict:
    """What the API may show. The password never leaves the server."""
    return {
        "provider": settings.provider,
        "email_address": settings.email_address,
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "imap_host": settings.imap_host,
        "imap_port": settings.imap_port,
        "allowed_recipients": settings.allowed_recipients,
        "has_password": bool(settings.password_encrypted),
    }


def check_connection(session: Session, company_id: int) -> dict:
    settings = get_settings(session, company_id)
    if settings.provider == "mock":
        return {"ok": True, "smtp": "Test mode: emails are only stored, not sent", "imap": "Test mode: replies come from the mock inbox"}

    password = decrypt(settings.password_encrypted)
    try:
        mail_client.send(settings, password, settings.email_address, "Onboarding test email", "Your mailbox is connected.", [])
        smtp = f"Sent a test email to {settings.email_address}"
    except (smtplib.SMTPException, OSError) as error:
        smtp = f"Failed: {error}"
    try:
        mail_client.check_login(settings, password)
        imap = "Logged in to the inbox"
    except (imaplib.IMAP4.error, OSError) as error:
        imap = f"Failed: {error}"
    return {"ok": not smtp.startswith("Failed") and not imap.startswith("Failed"), "smtp": smtp, "imap": imap}


# ---------- sending


def is_allowed(address: str, allowed: list[str]) -> bool:
    """An empty list allows everyone. Entries are full addresses or a domain like "@company.com"."""
    address = address.lower()
    return not allowed or any(address == a or (a.startswith("@") and address.endswith(a)) for a in allowed)


def _send(session: Session, email: Email, files: list[tuple[str, bytes]]) -> tuple[Email, bool]:
    """Sends once. The same subject to the same recipient is refused and the first email is returned."""
    settings = find_settings(session, email.company_id)
    if not settings:
        raise HTTPException(400, "Email is not set up for this company. HR must add it in Email settings.")
    if not is_allowed(email.to_address, settings.allowed_recipients):
        raise HTTPException(400, f"{email.to_address} is not on the allowed recipients list")

    query = select(Email).where(
        Email.company_id == email.company_id,
        Email.candidate_id == email.candidate_id,
        Email.department_id == email.department_id,
        Email.regarding_candidate_id == email.regarding_candidate_id,
        Email.subject == email.subject,
    )
    existing = session.exec(query).first()
    if existing:
        return existing, False

    email_sender.deliver(settings, email.to_address, email.subject, email.body, files)
    session.add(email)
    session.commit()
    session.refresh(email)
    return email, True


def send_to_candidate(
    session: Session, company_id: int, candidate_id: int, subject: str, body: str, reason: str,
    kind: str = "general", documents: list[str] | None = None, files: list[tuple[str, bytes]] | None = None,
) -> tuple[Email, bool]:
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    files = files or []
    email = Email(
        company_id=company_id, candidate_id=candidate.id, to_address=candidate.email,
        subject=subject, body=body, reason=reason, kind=kind,
        documents=documents or [], attachments=[name for name, _ in files],
    )
    return _send(session, email, files)


def send_to_department(
    session: Session, company_id: int, department_id: int, subject: str, body: str, reason: str,
    candidate_id: int | None = None,
) -> tuple[Email, bool]:
    department = departments_service.get_department(session, company_id, department_id)
    email = Email(
        company_id=company_id, department_id=department.id, regarding_candidate_id=candidate_id,
        to_address=department.email, subject=subject, body=body, reason=reason,
    )
    return _send(session, email, [])


def list_outbox(session: Session, company_id: int) -> list[Email]:
    query = select(Email).where(Email.company_id == company_id)
    return session.exec(query.order_by(Email.id.desc())).all()


def list_for_candidate(session: Session, company_id: int, candidate_id: int) -> list[Email]:
    """Emails to the candidate, and emails to departments about them."""
    query = select(Email).where(
        Email.company_id == company_id,
        or_(Email.candidate_id == candidate_id, Email.regarding_candidate_id == candidate_id),
    )
    return session.exec(query.order_by(Email.id)).all()


def departments_told(session: Session, company_id: int, candidate_id: int) -> set[int]:
    return {e.department_id for e in list_for_candidate(session, company_id, candidate_id) if e.department_id}


def latest_requested_documents(session: Session, company_id: int, candidate_id: int) -> list[str]:
    requests = [
        e for e in list_for_candidate(session, company_id, candidate_id)
        if e.kind == "documents_request" and e.candidate_id == candidate_id
    ]
    return requests[-1].documents if requests else []


# ---------- receiving


def _store_message(
    session: Session, company_id: int, from_address: str, subject: str, body: str,
    files: list[tuple[str, str, bytes]], candidate_id: int | None = None, external_id: str | None = None,
    in_reply_to: str | None = None,
) -> InboxMessage:
    if candidate_id is None:
        candidate = candidates_service.match_sender(session, company_id, from_address, subject)
        candidate_id = candidate.id if candidate else None
    attachments = [
        {"filename": filename, "content_type": content_type, "stored_name": documents_service.save_upload(filename, data)}
        for filename, content_type, data in files
    ]
    message = InboxMessage(
        company_id=company_id, candidate_id=candidate_id, from_address=from_address,
        subject=subject, body=body, attachments=attachments, external_id=external_id, in_reply_to=in_reply_to,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def drop_message(
    session: Session, company_id: int, from_address: str, subject: str, body: str,
    files: list[tuple[str, str, bytes]], in_reply_to: str | None = None,
) -> InboxMessage:
    """Mock inbox: store a reply as if it had arrived by email."""
    return _store_message(session, company_id, from_address, subject, body, files, in_reply_to=in_reply_to)


def store_upload(session: Session, company_id: int, candidate_id: int, files: list[tuple[str, str, bytes]]) -> InboxMessage:
    """Files a candidate sent through their upload link. They are read like an email reply."""
    reference = candidates_service.reference_code(candidate_id)
    return _store_message(
        session, company_id, "upload link", f"Files uploaded through the link [{reference}]", "", files, candidate_id
    )


def sync_inbox(session: Session, company_id: int) -> list[InboxMessage]:
    """Fetch new replies from the company's real inbox. Each email is stored once."""
    settings = get_settings(session, company_id)
    if settings.provider == "mock":
        return []
    try:
        raw_emails = mail_client.fetch(settings, decrypt(settings.password_encrypted), settings.created_at.date())
    except (imaplib.IMAP4.error, OSError) as error:
        raise HTTPException(502, f"Reading the inbox failed: {error}")

    new_messages = []
    for raw in raw_emails:
        parsed = mail_client.parse(raw)
        if parsed["from_address"] == settings.email_address.lower():
            continue
        external_id = parsed["message_id"] or hashlib.sha256(raw).hexdigest()
        if session.exec(select(InboxMessage).where(
            InboxMessage.company_id == company_id, InboxMessage.external_id == external_id
        )).first():
            continue
        new_messages.append(_store_message(
            session, company_id, parsed["from_address"], parsed["subject"], parsed["body"],
            parsed["attachments"], external_id=external_id,
        ))
    return new_messages


def take_unread(session: Session, company_id: int, candidate_id: int) -> list[InboxMessage]:
    """Unread replies from this candidate, marked as read."""
    query = select(InboxMessage).where(
        InboxMessage.company_id == company_id,
        InboxMessage.candidate_id == candidate_id,
        InboxMessage.processed == False,  # noqa: E712
    )
    messages = session.exec(query.order_by(InboxMessage.id)).all()
    for message in messages:
        message.processed = True
        session.add(message)
    session.commit()
    return messages


def latest_upload_link(session: Session, company_id: int, candidate_id: int) -> str | None:
    """The upload link from the latest documents request, if that request used one."""
    for email in reversed(list_for_candidate(session, company_id, candidate_id)):
        if email.kind == "documents_request" and email.candidate_id == candidate_id:
            found = re.search(r"https?://\S+/portal/upload/\S+", email.body)
            return found.group(0) if found else None
    return None
