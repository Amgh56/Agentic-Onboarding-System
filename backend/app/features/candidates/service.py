import re

from fastapi import HTTPException
from sqlmodel import Session, func, select, update

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
            f"Added to {job.title}.",
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
        statuses = [c.status for c in candidates if c.job_id == job.id]
        completed = statuses.count("completed")
        counts.append(
            JobCounts(job_id=job.id, applicants=len(statuses), in_progress=len(statuses) - completed, completed=completed)
        )
    return counts


def set_status(session: Session, company_id: int, candidate_id: int, status: str) -> Candidate:
    candidate = get_candidate(session, company_id, candidate_id)
    candidate.status = status
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def list_open(session: Session, company_id: int) -> list[Candidate]:
    """Candidates HR has started and who are not finished yet."""
    query = select(Candidate).where(
        Candidate.company_id == company_id, Candidate.status.in_(["invited", "in_progress"])
    )
    return session.exec(query.order_by(Candidate.id)).all()


def set_documents_due(session: Session, company_id: int, candidate_id: int, due_at) -> Candidate:
    candidate = get_candidate(session, company_id, candidate_id)
    candidate.documents_due_at = due_at
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def reference_code(candidate_id: int) -> str:
    return f"ONB-{candidate_id}"


def match_sender(session: Session, company_id: int, from_address: str, subject: str) -> Candidate | None:
    """Find who sent a reply: the reference code in the subject first, then the sender address."""
    found = re.search(r"ONB-(\d+)", subject)
    if found:
        candidate = session.get(Candidate, int(found.group(1)))
        if candidate and candidate.company_id == company_id:
            return candidate
    query = select(Candidate).where(
        Candidate.company_id == company_id, func.lower(Candidate.email) == from_address.strip().lower()
    )
    return session.exec(query.order_by(Candidate.id.desc())).first()


def set_step_outcomes(session: Session, company_id: int, candidate_id: int, outcomes: dict) -> Candidate:
    candidate = get_candidate(session, company_id, candidate_id)
    candidate.step_status = {**candidate.step_status, **outcomes}
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def list_waiting(session: Session, company_id: int, job_id: int) -> list[Candidate]:
    """Applicants of this job whose onboarding has not started yet."""
    query = select(Candidate).where(
        Candidate.company_id == company_id, Candidate.job_id == job_id, Candidate.status == "draft"
    )
    return session.exec(query.order_by(Candidate.id)).all()


def claim_for_start(session: Session, company_id: int, candidate_id: int) -> bool:
    """Move a candidate out of "draft" exactly once, so two starts can never run for the same person."""
    result = session.execute(
        update(Candidate)
        .where(Candidate.id == candidate_id, Candidate.company_id == company_id, Candidate.status == "draft")
        .values(status="invited")
    )
    session.commit()
    session.expire_all()
    return result.rowcount == 1
