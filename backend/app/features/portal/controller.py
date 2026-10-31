from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service as agent_service
from app.features.portal import pages, service

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/upload/{token}", response_class=HTMLResponse)
def upload_page(token: str, session: Session = Depends(get_session)):
    candidate = service.candidate_for_link(session, token)
    return pages.upload_page(candidate.full_name_en, candidate.full_name_ar, service.requested_documents(session, candidate))


@router.post("/upload/{token}", response_class=HTMLResponse)
def upload_files(token: str, files: list[UploadFile] = File(), session: Session = Depends(get_session)):
    candidate = service.candidate_for_link(session, token)
    service.receive_files(session, candidate, [(f.filename or "file", f.content_type or "", f.file.read()) for f in files])
    agent_service.wake_if_started(session, candidate.company_id, candidate.id, "document_received")
    return pages.done_page()
