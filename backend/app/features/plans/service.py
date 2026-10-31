from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.departments import service as departments_service
from app.features.jobs import service as jobs_service
from app.features.plans.drafting import draft
from app.features.plans.model import Plan
from app.features.systems import service as systems_service


def _find_plan(session: Session, company_id: int, job_id: int) -> Plan | None:
    query = select(Plan).where(Plan.company_id == company_id, Plan.job_id == job_id)
    return session.exec(query).first()


def draft_plan(session: Session, company_id: int, job_id: int) -> Plan:
    job = jobs_service.get_job(session, company_id, job_id)
    if not job.procedure.strip():
        raise HTTPException(400, "Add the onboarding procedure first")

    departments = departments_service.list_departments(session, company_id)
    steps = draft(job, departments, systems_service.list_systems(session, company_id))

    plan = _find_plan(session, company_id, job_id) or Plan(company_id=company_id, job_id=job_id)
    plan.steps = steps
    plan.departments = [{"name": d.name, "email": d.email, "handles": d.handles} for d in departments]
    plan.approved = True  # HR saving the procedure is the approval; the plan stays visible to read
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_plan(session: Session, company_id: int, job_id: int) -> Plan:
    jobs_service.get_job(session, company_id, job_id)
    plan = _find_plan(session, company_id, job_id)
    if not plan:
        raise HTTPException(404, "This job has no plan yet")
    return plan


def approve_plan(session: Session, company_id: int, job_id: int) -> Plan:
    plan = get_plan(session, company_id, job_id)
    plan.approved = True
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_approved_plan(session: Session, company_id: int, job_id: int) -> Plan:
    plan = _find_plan(session, company_id, job_id)
    if not plan or not plan.approved:
        raise HTTPException(400, "Approve this job's plan before starting")
    return plan


def has_approved_plan(session: Session, company_id: int, job_id: int) -> bool:
    plan = _find_plan(session, company_id, job_id)
    return bool(plan and plan.approved)


def find_approved_plan(session: Session, company_id: int, job_id: int) -> Plan | None:
    plan = _find_plan(session, company_id, job_id)
    return plan if plan and plan.approved else None
