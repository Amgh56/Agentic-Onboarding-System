from fastapi import HTTPException
from sqlmodel import Session

from app.core.security import read_upload_token
from app.features.candidates import service as candidates_service
from app.features.notifications import service as notifications_service


def candidate_for_link(session: Session, token: str):
    """The candidate an upload link belongs to. The token is the only key: no login needed."""
    found = read_upload_token(token)
    if not found:
        raise HTTPException(404, "This link is not valid")
    candidate_id, company_id = found
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    if candidate.status == "completed":
        raise HTTPException(400, "This onboarding is already finished")
    return candidate


def requested_documents(session: Session, candidate) -> list[str]:
    return notifications_service.latest_requested_documents(session, candidate.company_id, candidate.id)


def receive_files(session: Session, candidate, files: list[tuple[str, str, bytes]]) -> None:
    notifications_service.store_upload(session, candidate.company_id, candidate.id, files)
