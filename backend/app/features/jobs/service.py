from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.jobs.model import Job
from app.features.jobs.schema import JobCreate
from app.features.templates import service as templates_service


def create_job(session: Session, company_id: int, data: JobCreate) -> Job:
    if data.template_id is not None:
        templates_service.get_template(session, company_id, data.template_id)
    job = Job(company_id=company_id, **data.model_dump())
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def list_jobs(session: Session, company_id: int) -> list[Job]:
    return session.exec(select(Job).where(Job.company_id == company_id)).all()


def get_job(session: Session, company_id: int, job_id: int) -> Job:
    job = session.get(Job, job_id)
    if not job or job.company_id != company_id:
        raise HTTPException(404, "Job not found")
    return job


def update_job(session: Session, company_id: int, job_id: int, data: JobCreate) -> Job:
    job = get_job(session, company_id, job_id)
    if data.template_id is not None:
        templates_service.get_template(session, company_id, data.template_id)
    for field, value in data.model_dump().items():
        setattr(job, field, value)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
