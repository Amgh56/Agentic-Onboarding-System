from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service
from app.features.agent.schema import DeadlineCheck, DeadlineResult, RunResult
from app.features.auth.service import get_current_user
from app.features.jobs import service as jobs_service
from app.features.plans import service as plans_service

router = APIRouter(tags=["agent"])


@router.post("/candidates/{candidate_id}/start", response_model=RunResult)
def start(candidate_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.start(session, user.company_id, candidate_id)


@router.post("/jobs/{job_id}/start", status_code=202)
def start_job(
    job_id: int, background: BackgroundTasks, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    """Start every waiting applicant of this job. It runs after the response, one applicant at a time."""
    jobs_service.get_job(session, user.company_id, job_id)
    plans_service.get_approved_plan(session, user.company_id, job_id)
    background.add_task(service.start_waiting, session.get_bind(), user.company_id, job_id)
    return {"status": "started"}


@router.post("/deadlines/check", response_model=DeadlineResult)
def check_deadlines(
    data: DeadlineCheck | None = None, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    now = (data.now if data else None) or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return {"woken": service.check_deadlines(session, user.company_id, now)}
