from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service as agent_service
from app.features.auth.service import get_current_user
from app.features.notifications import service
from app.features.notifications.schema import (
    ConnectionResult, EmailRead, EmailSettingsRead, EmailSettingsSave, InboxRead, SyncResult,
)

router = APIRouter(tags=["email"])


@router.get("/email-settings", response_model=EmailSettingsRead)
def get_settings(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.settings_read(service.get_settings(session, user.company_id))


@router.put("/email-settings", response_model=EmailSettingsRead)
def save_settings(
    data: EmailSettingsSave, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.settings_read(service.save_settings(session, user.company_id, data))


@router.post("/email-settings/test", response_model=ConnectionResult)
def check_connection(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.check_connection(session, user.company_id)


@router.post("/email/sync", response_model=SyncResult)
def sync_inbox(user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Fetch new replies from the real inbox and wake the agent for each candidate who replied."""
    return agent_service.receive(session, user.company_id, service.sync_inbox(session, user.company_id))


@router.get("/outbox", response_model=list[EmailRead])
def list_outbox(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_outbox(session, user.company_id)


@router.post("/mock-inbox", response_model=InboxRead, status_code=201)
def drop_message(
    from_address: str = Form(),
    subject: str = Form(),
    body: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    uploads = [(f.filename or "file", f.content_type or "", f.file.read()) for f in files]
    message = service.drop_message(session, user.company_id, from_address, subject, body, uploads)
    agent_service.receive(session, user.company_id, [message])
    return message
