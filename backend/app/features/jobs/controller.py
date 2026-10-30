from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.jobs import service
from app.features.jobs.schema import JobCreate, JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=201)
def create_job(
    data: JobCreate, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.create_job(session, user.company_id, data)


@router.get("", response_model=list[JobRead])
def list_jobs(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_jobs(session, user.company_id)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.get_job(session, user.company_id, job_id)


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    data: JobCreate,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.update_job(session, user.company_id, job_id, data)
