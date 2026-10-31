import json
import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.core.events import log_event
from app.features.agent import tools

from app.features.agent.loop import run_loop
from app.features.approvals import service as approvals_service
from app.features.candidates import service as candidates_service
from app.features.documents import service as documents_service
from app.features.notifications import service as notifications_service
from app.features.notifications.model import InboxMessage
from app.features.plans import service as plans_service

logger = logging.getLogger(__name__)

# Adding applicants or saving the procedure starts onboarding on its own. Tests turn this off.
AUTO_START = True

EVENTS = {
    "document_received": "document_received: the candidate sent a reply. Read the inbox.",
    "deadline_passed": "deadline_passed: the deadline for the candidate's documents has passed.",
}


def start(session: Session, company_id: int, candidate_id: int) -> dict:
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    plans_service.get_approved_plan(session, company_id, candidate.job_id)
    if not candidates_service.claim_for_start(session, company_id, candidate.id):
        return {"steps": 0, "summary": "Onboarding already started."}
    return run_loop(session, company_id, candidate, "HR pressed Start.")


def start_waiting(bind, company_id: int, job_id: int) -> None:
    """Start onboarding for everyone in this job who is waiting, once the job has a procedure.

    Runs after the response is sent, so it opens its own database session."""
    if not AUTO_START:
        return
    with Session(bind) as session:
        if not plans_service.has_approved_plan(session, company_id, job_id):
            return
        for waiting in candidates_service.list_waiting(session, company_id, job_id):
            if not candidates_service.claim_for_start(session, company_id, waiting.id):
                continue
            candidate = candidates_service.get_candidate(session, company_id, waiting.id)
            try:
                run_loop(session, company_id, candidate, "The candidate was added and the job has an onboarding procedure, so onboarding starts now.")
            except Exception as error:  # one failed run must not stop the others; HR sees it in the activity log
                session.rollback()
                log_event(session, company_id, candidate.id, "system", "The agent could not run", str(error))
                session.commit()


def wake_if_started(session: Session, company_id: int, candidate_id: int, event: str) -> dict | None:
    """Run the agent for an event, but only for candidates HR has started and not finished."""
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    if candidate.status in ("draft", "completed"):
        return None
    if not plans_service.has_approved_plan(session, company_id, candidate.job_id):
        return None
    return run_loop(session, company_id, candidate, EVENTS.get(event, event))


def receive(session: Session, company_id: int, messages: list[InboxMessage]) -> dict:
    """Replies have arrived and are stored. Wake the agent once for each applicant they belong to.
    A reply that matches nobody is left alone and logged."""
    for message in messages:
        if not message.candidate_id:
            logger.info("Reply from %s ('%s') matched no applicant, so it was left alone", message.from_address, message.subject)
    for candidate_id in sorted({m.candidate_id for m in messages if m.candidate_id}):
        wake_if_started(session, company_id, candidate_id, "document_received")
    return {"new_messages": len(messages), "matched": sum(1 for m in messages if m.candidate_id)}


def check_deadlines(session: Session, company_id: int, now: datetime) -> int:
    """Wake the agent for every started candidate whose document deadline has passed with documents
    still missing. The deadline then moves 2 days on, so each candidate is woken once per period."""
    woken = 0
    for candidate in candidates_service.list_open(session, company_id):
        due = candidate.documents_due_at
        if due and due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if not due or due > now:
            continue
        requested = notifications_service.latest_requested_documents(session, company_id, candidate.id)
        if not requested or not documents_service.still_missing(session, company_id, candidate.id, requested):
            continue
        candidates_service.set_documents_due(session, company_id, candidate.id, now + timedelta(days=2))
        wake_if_started(session, company_id, candidate.id, "deadline_passed")
        woken += 1
    return woken


def decide(session: Session, company_id: int, approval_id: int, approve: bool, note: str):
    """HR answers an item in the queue. An approved action runs now, then the agent continues."""
    approval = approvals_service.get_approval(session, company_id, approval_id)
    approvals_service.record_decision(session, approval, approve, note)
    candidate = candidates_service.get_candidate(session, company_id, approval.candidate_id)

    outcome = ""
    payload = approval.payload or {}
    if approve and payload.get("tool"):
        result = tools.execute(session, company_id, candidate, payload["tool"], payload["args"], approved_by_hr=True)
        outcome = f" The action ran: {json.dumps(result, ensure_ascii=False)}"
    if payload.get("document_id"):
        documents_service.save_result(
            session, company_id, payload["document_id"], "valid" if approve else "rejected",
            {"valid": approve, "reason": f"HR decided: {note or ('valid' if approve else 'not valid')}"},
        )

    verb = "approved" if approve else "declined"
    log_event(session, company_id, candidate.id, "hr", f"HR {verb}: {approval.action or approval.reason}", note)
    session.commit()
    wake_if_started(
        session, company_id, candidate.id,
        f"hr_decision: HR {verb} '{approval.action or approval.reason}'. HR's note: {note or 'none'}.{outcome}",
    )
    return approval
