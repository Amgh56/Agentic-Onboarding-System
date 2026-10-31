"""Set up the demo: one company at demo.com, the "Nov 2026 cohort" job and three applicants.

Run from backend/:

    python -m scripts.seed_demo

Safe to run twice. The plan is drafted (one model call) only when the procedure is new or changed.
Nothing starts here: the applicants wait until the demo starts onboarding.

To start the demo over, run it again with --reset: everything that happened to the applicants is cleared
and they go back to waiting. The plan, the documents and the applicants stay.
"""

import argparse
from datetime import date
from pathlib import Path

from sqlmodel import Session, delete, select

from app.core.database import engine
from app.core.events import Event
from app.features.agent.model import ActionLog
from app.features.approvals.model import Approval
from app.features.auth import service as auth_service
from app.features.auth.model import User
from app.features.auth.schema import SignupRequest
from app.features.candidates import service as candidates_service
from app.features.candidates.model import Candidate
from app.features.candidates.schema import CandidateCreate
from app.features.departments import service as departments_service
from app.features.departments.schema import DepartmentCreate
from app.features.documents import service as documents_service
from app.features.documents.model import CandidateDocument
from app.features.jobs import service as jobs_service
from app.features.jobs.schema import JobCreate
from app.features.notifications.model import Email, InboxMessage
from app.features.plans import service as plans_service
from app.features.systems import service as systems_service
from app.features.systems.model import Account, Ticket

HR_EMAIL = "hr@demo.com"
HR_PASSWORD = "demo1234"  # only used when the demo creates the HR user
COMPANY_NAME = "Abdullah's Company"
DOMAIN = "demo.com"  # work emails and department addresses, e.g. it@demo.com
JOB_TITLE = "Nov 2026 cohort"
TEMPLATES = Path(__file__).resolve().parents[2] / "demo_files" / "templates"  # the blank documents

PROCEDURE = """Send the new hire the attached documents and ask them to fill in the blanks, sign at the bottom of every page and send them back. Check that each one is signed on every page and in the new hire's name. If anything is missing or wrong, send one email listing all of it.
Once all documents are accepted, create the work email first.
Then set up accounts by role. Developers: Slack, Teams and GitHub (backend-team). Business roles (sales, finance, operations, HR): Slack, Teams and ERP. If the role is unclear, ask HR and wait.
Then tell Payroll the name, role and start date. Finance does not need to know.
Then ask IT for a laptop through the IT desk: a developer laptop for developers, a standard one for everyone else.
Finish with a welcome email to the personal address with the work email and what happens on day one."""

DOCUMENTS = ["Cybersecurity_Policy.pdf", "NDA.pdf", "Employment_Contract.pdf"]

# The names match the signed PDFs in demo_files/.
APPLICANTS = [
    {
        "full_name_en": "Yousef Haitham AlQurashi", "full_name_ar": "يوسف هيثم القرشي", "phone": "+966500000001",
        "email": "yousef@gmail.com", "date_of_birth": date(1995, 3, 12), "role": "Backend engineer",
        "avatar_url": "/avatars/yousef.jpg",
    },
    {
        "full_name_en": "Abdulaziz Ahmad", "full_name_ar": "عبدالعزيز أحمد", "phone": "+966500000002",
        "email": "abdulaziz@gmail.com", "date_of_birth": date(1993, 7, 21), "role": "Growth Lead",
        "avatar_url": "/avatars/abdulaziz.jpg",
    },
    {
        "full_name_en": "Omar Ateeq Alghamdi", "full_name_ar": "عمر عتيق الغامدي", "phone": "+966500000003",
        "email": "omar@gmail.com", "date_of_birth": date(1991, 11, 5), "role": "Sales manager",
        "avatar_url": "/avatars/omar.jpg",
    },
]


def demo_company_id(session: Session) -> int:
    """The company of the demo HR user."""
    user = session.exec(select(User).where(User.email == HR_EMAIL)).first()
    if not user:
        raise SystemExit("The demo is not set up. Run: python -m scripts.seed_demo")
    return user.company_id


def company_for_hr(session: Session) -> int:
    """The company of the demo HR user, created the normal way if it does not exist yet."""
    user = session.exec(select(User).where(User.email == HR_EMAIL)).first()
    if not user:
        auth_service.signup(
            session, SignupRequest(company_name=COMPANY_NAME, full_name="HR", email=HR_EMAIL, password=HR_PASSWORD)
        )
        user = session.exec(select(User).where(User.email == HR_EMAIL)).first()
    return user.company_id


def use_demo_domain(session: Session, company_id: int) -> None:
    """Work emails and every department address use the demo domain."""
    work_email = systems_service.get_system(session, company_id, "work_email")
    work_email.config = {"domain": DOMAIN}
    session.add(work_email)
    session.commit()
    departments_service.ensure_defaults(session, company_id, DOMAIN)
    for department in departments_service.list_departments(session, company_id):
        email = f"{department.name.lower()}@{DOMAIN}"
        data = DepartmentCreate(name=department.name, email=email, handles=department.handles)
        departments_service.update_department(session, company_id, department.id, data)


def save_job(session: Session, company_id: int) -> int:
    """Save the job and its procedure like HR does: a new or changed procedure drafts the plan."""
    job = next((j for j in jobs_service.list_jobs(session, company_id) if j.title == JOB_TITLE), None)
    if not job:
        job = jobs_service.create_job(session, company_id, JobCreate(title=JOB_TITLE))
    changed = job.procedure != PROCEDURE or job.start_mode != "auto"
    data = JobCreate(**{**job.model_dump(), "start_mode": "auto", "procedure": PROCEDURE})
    jobs_service.update_job(session, company_id, job.id, data)
    if changed or not plans_service.has_approved_plan(session, company_id, job.id):
        plans_service.draft_plan(session, company_id, job.id)
    return job.id


def add_documents(session: Session, company_id: int, job_id: int) -> None:
    """Upload the blank documents, with no instructions: the procedure says what to do with them.
    A stored file that is not the blank one is replaced."""
    stored = dict(documents_service.job_files(session, company_id, job_id))
    existing = {d.filename: d for d in documents_service.list_documents(session, company_id, job_id)}
    for filename in DOCUMENTS:
        data = (TEMPLATES / filename).read_bytes()
        document = existing.get(filename)
        if document and stored[filename] == data:
            documents_service.set_instructions(session, company_id, document.id, "")
            continue
        if document:
            documents_service.delete_document(session, company_id, document.id)
        documents_service.add_document(session, company_id, job_id, filename, "application/pdf", data)


def add_applicants(session: Session, company_id: int, job_id: int) -> None:
    """Add each applicant once. Running again brings an existing one's details back to the demo values."""
    existing = {c.email: c for c in candidates_service.list_candidates(session, company_id, job_id)}
    for applicant in APPLICANTS:
        details = {k: v for k, v in applicant.items() if k != "avatar_url"}
        candidate = existing.get(applicant["email"])
        if not candidate:
            candidate = candidates_service.add_candidate(session, company_id, job_id, CandidateCreate(**details))
        for field, value in applicant.items():
            setattr(candidate, field, value)
        session.add(candidate)
    session.commit()


def seed(session: Session) -> tuple[int, int]:
    company_id = company_for_hr(session)
    use_demo_domain(session, company_id)
    job_id = save_job(session, company_id)
    add_documents(session, company_id, job_id)
    add_applicants(session, company_id, job_id)
    return company_id, job_id


def reset(session: Session, company_id: int) -> None:
    """Forget everything that happened to the applicants and put them back to waiting."""
    for model in (Account, Ticket, Email, InboxMessage, CandidateDocument, Approval, ActionLog, Event):
        session.exec(delete(model).where(model.company_id == company_id))
    for candidate in session.exec(select(Candidate).where(Candidate.company_id == company_id)):
        candidate.status, candidate.stage, candidate.step_status, candidate.documents_due_at = "draft", "Invited", {}, None
        session.add(candidate)
    session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="start the demo over")
    args = parser.parse_args()
    with Session(engine) as session:
        company_id, job_id = seed(session)
        if args.reset:
            reset(session, company_id)
    print(f"Demo {'reset and ' if args.reset else ''}ready: company {company_id}, job {job_id} ({JOB_TITLE}). Log in as {HR_EMAIL}.")
