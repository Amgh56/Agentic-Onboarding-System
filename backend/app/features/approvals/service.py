from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.approvals.model import Approval
from app.features.candidates import service as candidates_service


def create_approval(
    session: Session, company_id: int, candidate_id: int, kind: str, action: str, reason: str,
    payload: dict | None = None,
) -> Approval:
    """Add an item to the HR queue once. A pending item for the same thing is returned instead."""
    query = select(Approval).where(
        Approval.company_id == company_id,
        Approval.candidate_id == candidate_id,
        Approval.kind == kind,
        Approval.action == action,
        Approval.status == "pending",
    )
    if not payload:
        query = query.where(Approval.reason == reason)
    existing = session.exec(query).first()
    if existing:
        return existing

    approval = Approval(
        company_id=company_id, candidate_id=candidate_id, kind=kind, action=action, reason=reason, payload=payload or {}
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)
    return approval


def create_notice(session: Session, company_id: int, candidate_id: int, action: str, reason: str) -> Approval:
    """Tell HR about an action the agent already took."""
    notice = Approval(company_id=company_id, candidate_id=candidate_id, kind="notice", action=action, reason=reason, status="done")
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


def find_decided(session: Session, company_id: int, candidate_id: int, action: str) -> Approval | None:
    """HR's latest decision on this exact action, if there is one."""
    query = select(Approval).where(
        Approval.company_id == company_id,
        Approval.candidate_id == candidate_id,
        Approval.kind == "approval",
        Approval.action == action,
        Approval.status.in_(["approved", "declined"]),
    )
    return session.exec(query.order_by(Approval.id.desc())).first()


def get_approval(session: Session, company_id: int, approval_id: int) -> Approval:
    approval = session.get(Approval, approval_id)
    if not approval or approval.company_id != company_id:
        raise HTTPException(404, "Approval not found")
    return approval


def record_decision(session: Session, approval: Approval, approve: bool, note: str) -> Approval:
    if approval.status != "pending":
        raise HTTPException(400, "This item was already decided")
    approval.status = "approved" if approve else "declined"
    approval.decision_note = note.strip()
    approval.decided_at = datetime.now(timezone.utc)
    session.add(approval)
    session.commit()
    session.refresh(approval)
    return approval


def list_approvals(
    session: Session, company_id: int, candidate_id: int | None = None, status: str | None = None
) -> list[Approval]:
    query = select(Approval).where(Approval.company_id == company_id)
    if candidate_id is not None:
        query = query.where(Approval.candidate_id == candidate_id)
    if status:
        query = query.where(Approval.status == status)
    return session.exec(query.order_by(Approval.id.desc())).all()


def list_for_candidate(session: Session, company_id: int, candidate_id: int) -> list[Approval]:
    query = select(Approval).where(Approval.company_id == company_id, Approval.candidate_id == candidate_id)
    return session.exec(query.order_by(Approval.id)).all()


def to_read(session: Session, company_id: int, approval: Approval) -> dict:
    candidate = candidates_service.get_candidate(session, company_id, approval.candidate_id)
    return {
        **approval.model_dump(),
        "candidate_name": candidate.full_name_en,
        "job_id": candidate.job_id,
    }
