from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service as agent_service
from app.features.approvals import service
from app.features.approvals.schema import ApprovalRead, Decision
from app.features.auth.service import get_current_user

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def list_approvals(
    candidate_id: int | None = None,
    status: str | None = None,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    approvals = service.list_approvals(session, user.company_id, candidate_id, status)
    return [service.to_read(session, user.company_id, a) for a in approvals]


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
def decide(
    approval_id: int, data: Decision, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    approval = agent_service.decide(session, user.company_id, approval_id, data.approve, data.note)
    return service.to_read(session, user.company_id, approval)
