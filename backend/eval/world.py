"""Builds a small world for one run (a fresh database, one company, one candidate), plays the
candidate's side of the story, and reads back what happened."""

import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.database import get_session
from app.features.agent.model import ActionLog
from app.features.approvals.model import Approval
from app.features.candidates.model import Candidate
from app.features.departments.model import Department
from app.features.documents import storage
from app.features.documents.model import CandidateDocument
from app.features.notifications.model import Email
from app.features.plans.model import Plan
from app.features.systems.model import Account, Ticket
from app.main import app
from scripts import seed_demo, send_reply


@dataclass
class World:
    """What happened, as plain data. The checks in cases.py read this."""

    candidate_status: str = "draft"
    accounts: list = field(default_factory=list)
    tickets: list = field(default_factory=list)
    emails: list = field(default_factory=list)
    approvals: list = field(default_factory=list)
    documents: list = field(default_factory=list)
    tool_calls: int = 0
    steps_done: int = 0
    steps_total: int = 0
    checkpoint: "World | None" = None  # what the world looked like part-way, for cases that check the middle of the story

    def account(self, system: str) -> dict | None:
        return next((a for a in self.accounts if a.get("system") == system), None)

    def has_account(self, system: str) -> bool:
        return self.account(system) is not None

    def account_address(self, system: str) -> str | None:
        return (self.account(system) or {}).get("address")

    def emails_to_candidate(self) -> list:
        return [e for e in self.emails if e["to_candidate"]]

    def emails_to(self, department: str) -> list:
        return [e for e in self.emails if e["department"] == department]

    @property
    def escalated(self) -> bool:
        return any(a["kind"] == "escalation" for a in self.approvals)


@dataclass
class Context:
    client: TestClient
    headers: dict
    session: Session
    company_id: int
    candidate_id: int
    case: object
    started_at: datetime
    state: dict = field(default_factory=dict)


@contextmanager
def fresh_app():
    """The app on a brand new in-memory database, with uploads in a temp folder."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    previous_uploads = storage.UPLOADS_DIR
    with tempfile.TemporaryDirectory() as folder:
        storage.UPLOADS_DIR = Path(folder)
        app.dependency_overrides[get_session] = override_session
        try:
            yield TestClient(app), engine
        finally:
            app.dependency_overrides.pop(get_session, None)
            storage.UPLOADS_DIR = previous_uploads


def deliver_reply(ctx: Context) -> None:
    """The candidate sends their document, the way the case says they do."""
    reply, candidate = ctx.case.reply, ctx.case.candidate
    files = [("files", (reply["filename"], reply["text"].encode(), "text/plain"))]
    if reply["via"] == "inbox":
        ctx.client.post(
            "/mock-inbox",
            data={"from_address": candidate["email"], "subject": f"Re: documents [ONB-{ctx.candidate_id}]", "body": "Here is my document."},
            files=files,
            headers=ctx.headers,
        )
        return

    for email in reversed(ctx.client.get("/outbox", headers=ctx.headers).json()):
        link = re.search(r"https?://\S+/portal/upload/\S+", email["body"])
        if link and email["candidate_id"] == ctx.candidate_id:
            ctx.client.post(urlparse(link.group(0)).path, files=files)
            return
    # no upload link was ever sent, so this candidate has nothing to upload


def play_script(ctx: Context, variant) -> None:
    """A case with a script: the applicant replies through the reply script, HR answers, and so on."""
    persona = ctx.case.candidate["name_en"].split()[0].lower()
    for step, argument in ctx.case.script:
        if step == "reply":
            send_reply.send(ctx.session, ctx.company_id, persona, argument)
            variant.on_reply(ctx)
        elif step == "checkpoint":
            ctx.state["checkpoint"] = snapshot(ctx)
        elif step == "hr":
            pending = ctx.client.get("/approvals", params={"candidate_id": ctx.candidate_id}, headers=ctx.headers).json()
            for approval in [a for a in pending if a["kind"] == "escalation" and a["status"] == "pending"]:
                ctx.client.post(f"/approvals/{approval['id']}/decide", json={"approve": True, "note": argument}, headers=ctx.headers)


def snapshot(ctx: Context) -> World:
    ctx.session.expire_all()
    session, company_id = ctx.session, ctx.company_id
    plan = session.exec(select(Plan).where(Plan.company_id == company_id)).first()
    departments = {d.id: d.name for d in session.exec(select(Department).where(Department.company_id == company_id))}
    candidate = session.get(Candidate, ctx.candidate_id)
    return World(
        candidate_status=candidate.status,
        accounts=[
            {"system": a.system_key, "address": a.address, "status": a.status, "groups": a.groups}
            for a in session.exec(select(Account).where(Account.company_id == company_id))
        ],
        tickets=[t.item for t in session.exec(select(Ticket).where(Ticket.company_id == company_id))],
        emails=[
            {
                "to": e.to_address, "subject": e.subject, "body": e.body,
                "to_candidate": e.candidate_id == ctx.candidate_id, "department": departments.get(e.department_id),
            }
            for e in session.exec(select(Email).where(Email.company_id == company_id).order_by(Email.id))
        ],
        approvals=[{"kind": a.kind, "reason": a.reason} for a in session.exec(select(Approval).where(Approval.company_id == company_id))],
        documents=[d.status for d in session.exec(select(CandidateDocument).where(CandidateDocument.company_id == company_id))],
        tool_calls=len(session.exec(select(ActionLog).where(ActionLog.company_id == company_id)).all()),
        steps_total=len(plan.steps) if plan else 0,
        steps_done=sum(1 for step in (plan.steps if plan else []) if candidate.step_status.get(step["id"])),
        checkpoint=ctx.state.get("checkpoint"),
    )


def play(case, variant) -> World:
    """Set up the company and candidate, run the variant through the story, return what happened."""
    with fresh_app() as (client, engine), Session(engine) as session:
        slug = re.sub(r"[^a-z]", "", case.company["name"].lower())
        token = client.post("/auth/signup", json={
            "company_name": case.company["name"], "full_name": "Eval HR", "email": f"hr@{slug}.example", "password": "eval-password",
        }).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.put("/email-settings", json={"provider": "mock", "email_address": f"onboarding@{slug}.example"}, headers=headers)
        company_id = client.get("/companies/me", headers=headers).json()["id"]

        job = client.post("/jobs", json={**case.job, "procedure": case.company["procedure"]}, headers=headers).json()
        candidate = client.post(f"/jobs/{job['id']}/candidates", json={
            "full_name_en": case.candidate["name_en"], "full_name_ar": case.candidate["name_ar"], "phone": "0500000000",
            "email": case.candidate["email"], "date_of_birth": "1992-03-14", "role": case.candidate["role"],
        }, headers=headers).json()

        for filename in case.company.get("documents", []):
            client.post(f"/jobs/{job['id']}/documents", files={"file": (filename, (seed_demo.TEMPLATES / filename).read_bytes(), "application/pdf")}, headers=headers)

        ctx = Context(client, headers, session, company_id, candidate["id"], case, datetime.now(timezone.utc))
        with variant.environment():
            if variant.needs_plan:
                # Drafting the plan puts it in use and starts onboarding for the waiting candidate.
                client.post(f"/jobs/{job['id']}/plan/draft", headers=headers)
            variant.start(ctx)
            play_script(ctx, variant)
            if case.reply:
                deliver_reply(ctx)
                variant.on_reply(ctx)
            for days in case.deadline_checks:
                variant.on_deadline(ctx, days)
        return snapshot(ctx)
