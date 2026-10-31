from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.features.agent import service as agent_service
from app.features.auth.service import get_current_user
from app.features.candidates import service
from app.features.candidates.schema import CandidateCreate, CandidateRead, EventRead, JobCounts, StageUpdate

router = APIRouter(tags=["candidates"])


@router.post("/jobs/{job_id}/candidates", response_model=CandidateRead, status_code=201)
def add_candidate(
    job_id: int,
    data: CandidateCreate,
    background: BackgroundTasks,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    candidate = service.add_candidate(session, user.company_id, job_id, data)
    background.add_task(agent_service.start_waiting, session.get_bind(), user.company_id, job_id)
    return candidate


@router.post("/jobs/{job_id}/candidates/bulk", response_model=list[CandidateRead], status_code=201)
def add_candidates(
    job_id: int,
    data: list[CandidateCreate],
    background: BackgroundTasks,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    candidates = service.add_candidates(session, user.company_id, job_id, data)
    background.add_task(agent_service.start_waiting, session.get_bind(), user.company_id, job_id)
    return candidates


@router.post("/jobs/{job_id}/candidates/import", response_model=list[CandidateRead], status_code=201)
def import_candidates(
    job_id: int,
    file: UploadFile,
    background: BackgroundTasks,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    candidates = service.import_csv(session, user.company_id, job_id, file.file.read())
    background.add_task(agent_service.start_waiting, session.get_bind(), user.company_id, job_id)
    return candidates


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateRead])
def list_candidates(
    job_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.list_candidates(session, user.company_id, job_id)


@router.put("/candidates/{candidate_id}/stage", response_model=CandidateRead)
def move_stage(
    candidate_id: int,
    data: StageUpdate,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.move_stage(session, user.company_id, candidate_id, data.stage)


@router.get("/candidates/counts", response_model=list[JobCounts])
def job_counts(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.job_counts(session, user.company_id)


@router.get("/candidates/{candidate_id}", response_model=CandidateRead)
def get_candidate(
    candidate_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.get_candidate(session, user.company_id, candidate_id)


@router.get("/candidates/{candidate_id}/events", response_model=list[EventRead])
def list_events(
    candidate_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.list_events(session, user.company_id, candidate_id)
