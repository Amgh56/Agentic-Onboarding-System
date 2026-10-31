from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service as agent_service
from app.features.auth.service import get_current_user
from app.features.plans import service
from app.features.plans.schema import PlanRead

router = APIRouter(prefix="/jobs/{job_id}/plan", tags=["plans"])


@router.post("/draft", response_model=PlanRead, status_code=201)
def draft_plan(
    job_id: int, background: BackgroundTasks, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    plan = service.draft_plan(session, user.company_id, job_id)
    background.add_task(agent_service.start_waiting, session.get_bind(), user.company_id, job_id)
    return plan


@router.get("", response_model=PlanRead)
def get_plan(job_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.get_plan(session, user.company_id, job_id)


@router.post("/approve", response_model=PlanRead)
def approve_plan(job_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.approve_plan(session, user.company_id, job_id)
