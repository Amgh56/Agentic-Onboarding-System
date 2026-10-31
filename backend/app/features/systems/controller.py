from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.systems import service
from app.features.candidates import service as candidates_service
from app.features.systems.schema import CandidateAccounts, SystemContents, SystemRead

router = APIRouter(prefix="/systems", tags=["systems"])
candidate_router = APIRouter(tags=["systems"])


@router.get("", response_model=list[SystemRead])
def list_systems(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_systems(session, user.company_id)


@router.get("/contents", response_model=list[SystemContents])
def list_contents(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_contents(session, user.company_id)


@candidate_router.get("/candidates/{candidate_id}/accounts", response_model=CandidateAccounts)
def candidate_accounts(candidate_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    candidates_service.get_candidate(session, user.company_id, candidate_id)
    return {
        "accounts": service.list_candidate_accounts(session, user.company_id, candidate_id),
        "tickets": service.list_candidate_tickets(session, user.company_id, candidate_id),
    }
