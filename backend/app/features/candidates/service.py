from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.events import Event, log_event
from app.features.candidates.csv_import import parse_candidates
from app.features.candidates.model import Candidate
from app.features.candidates.schema import CandidateCreate, JobCounts
from app.features.jobs import service as jobs_service


def add_candidate(session: Session, company_id: int, job_id: int, data: CandidateCreate) -> Candidate:
    return add_candidates(session, company_id, job_id, [data])[0]


def add_candidates(
    session: Session, company_id: int, job_id: int, rows: list[CandidateCreate]
) -> list[Candidate]:
    job = jobs_service.get_job(session, company_id, job_id)
    candidates = [
        Candidate(company_id=company_id, job_id=job.id, stage=job.stages[0], **row.model_dump())
        for row in rows
    ]
    session.add_all(candidates)
    session.flush()
    for candidate in candidates:
        log_event(
            session, company_id, candidate.id, "hr", "Applicant added",
            f"Added to {job.title}, first step: {candidate.stage}.",
        )
    session.commit()
    for candidate in candidates:
        session.refresh(candidate)
    return candidates


def import_csv(session: Session, company_id: int, job_id: int, content: bytes) -> list[Candidate]:
    rows = parse_candidates(content.decode("utf-8-sig"))
    return add_candidates(session, company_id, job_id, rows)


def list_candidates(session: Session, company_id: int, job_id: int) -> list[Candidate]:
    jobs_service.get_job(session, company_id, job_id)
    query = select(Candidate).where(Candidate.company_id == company_id, Candidate.job_id == job_id)
    return session.exec(query.order_by(Candidate.id)).all()


def get_candidate(session: Session, company_id: int, candidate_id: int) -> Candidate:
    candidate = session.get(Candidate, candidate_id)
    if not candidate or candidate.company_id != company_id:
        raise HTTPException(404, "Applicant not found")
    return candidate


def list_events(session: Session, company_id: int, candidate_id: int) -> list[Event]:
    get_candidate(session, company_id, candidate_id)
    query = select(Event).where(Event.candidate_id == candidate_id)
    return session.exec(query.order_by(Event.id.desc())).all()


def move_stage(session: Session, company_id: int, candidate_id: int, stage: str) -> Candidate:
    candidate = get_candidate(session, company_id, candidate_id)
    job = jobs_service.get_job(session, company_id, candidate.job_id)
    if stage not in job.stages:
        raise HTTPException(400, "Unknown stage for this job")
    log_event(session, company_id, candidate.id, "hr", f"Moved to {stage}", f"Moved from {candidate.stage}.")
    candidate.stage = stage
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def job_counts(session: Session, company_id: int) -> list[JobCounts]:
    candidates = session.exec(select(Candidate).where(Candidate.company_id == company_id)).all()
    counts = []
    for job in jobs_service.list_jobs(session, company_id):
        stages = [c.stage for c in candidates if c.job_id == job.id]
        completed = stages.count(job.stages[-1])
        counts.append(
            JobCounts(
                job_id=job.id,
                applicants=len(stages),
                in_progress=len(stages) - completed,
                completed=completed,
            )
        )
    return counts
