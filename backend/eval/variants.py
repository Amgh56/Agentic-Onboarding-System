"""The ways of running onboarding that the evaluation compares.

full: the agent with the verifier (second document reading, review of risky actions).
agent: the same agent with the verifier switched off.
rules: a fixed checklist with no model, written the way one company's HR would hard-code it.
"""

import re
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import patch

from app.features.agent import service as agent_service
from app.features.agent import tools, verifier
from app.features.candidates import service as candidates_service
from app.features.departments import service as departments_service
from app.features.documents import storage
from app.features.documents.model import CandidateDocument


class AgentVariant:
    needs_plan = True
    verifier = False

    @contextmanager
    def environment(self):
        with patch.object(verifier, "ENABLED", self.verifier):
            yield

    def start(self, ctx):
        ctx.client.post(f"/candidates/{ctx.candidate_id}/start", headers=ctx.headers)

    def on_reply(self, ctx):
        """Nothing to do: the reply already woke the agent."""

    def on_deadline(self, ctx, days):
        now = ctx.started_at + timedelta(days=days)
        ctx.client.post("/deadlines/check", json={"now": now.isoformat()}, headers=ctx.headers)


class FullVariant(AgentVariant):
    verifier = True


class RulesVariant:
    needs_plan = False

    @contextmanager
    def environment(self):
        # The checklist runs itself: a reply must not wake the agent, and there is no verifier.
        with patch.object(agent_service, "wake_if_started", lambda *args, **kwargs: None), patch.object(verifier, "ENABLED", False):
            yield

    def _run(self, ctx, tool, **args):
        ctx.session.expire_all()
        candidate = candidates_service.get_candidate(ctx.session, ctx.company_id, ctx.candidate_id)
        return tools.execute(ctx.session, ctx.company_id, candidate, tool, {"candidate_id": ctx.candidate_id, "reason": "Fixed checklist", **args})

    def _department(self, ctx, name):
        found = [d for d in departments_service.list_departments(ctx.session, ctx.company_id) if d.name == name]
        return found[0].id if found else None

    def start(self, ctx):
        self._run(ctx, "request_documents", documents=["National ID"], channel="email")

    def on_reply(self, ctx):
        messages = self._run(ctx, "read_inbox")["messages"]
        document_ids = [d["document_id"] for m in messages for d in m["documents"]]
        problems = [problem for problem in (self._check(ctx, i) for i in document_ids) if problem]
        if document_ids and not problems:
            self._provision(ctx)
        elif problems:
            self._run(ctx, "send_email", subject="Your document was rejected", body=problems[0])

    def _check(self, ctx, document_id) -> str | None:
        """The checklist's own document check: the name appears and the expiry date is in the future."""
        ctx.session.expire_all()
        document = ctx.session.get(CandidateDocument, document_id)
        candidate = candidates_service.get_candidate(ctx.session, ctx.company_id, ctx.candidate_id)
        text = storage.file_path(document.stored_name).read_text(errors="ignore")
        expiry = re.search(r"Expiry date:\s*(\d{4}-\d{2}-\d{2})", text)

        problem = None
        if candidate.full_name_en.lower() not in text.lower():
            problem = "The name on the document does not match."
        elif not expiry or date.fromisoformat(expiry.group(1)) < date.today():
            problem = "The document is expired."
        document.status = "rejected" if problem else "valid"
        document.result = {"valid": not problem, "matches": None if problem else "National ID", "reason": problem or "ok"}
        ctx.session.add(document)
        ctx.session.commit()
        return problem

    def _provision(self, ctx):
        candidate = candidates_service.get_candidate(ctx.session, ctx.company_id, ctx.candidate_id)
        role = (candidate.role or "").lower()
        email = self._run(ctx, "create_account", system="work_email", groups=[])["address"]
        accounts = ["Work email: " + email]
        told = []

        if "developer" in role or "engineer" in role:
            self._run(ctx, "create_account", system="github", groups=["backend-team"])
            self._run(ctx, "create_ticket", item="Laptop")
            it = self._department(ctx, "IT")
            if it:
                self._run(ctx, "send_email", candidate_id=None, department_id=it, subject=f"Laptop for {candidate.full_name_en}", body="Please prepare a laptop.")
                told.append("IT")
            accounts.append("GitHub: invited")
        else:
            self._run(ctx, "create_account", system="erp", groups=["accountant"])
            accounts.append("ERP: created")

        payroll = self._department(ctx, "Payroll")
        if payroll:
            self._run(ctx, "send_email", candidate_id=None, department_id=payroll, subject=f"New joiner: {candidate.full_name_en}", body=f"{candidate.full_name_en} is joining as {candidate.role}.")
            told.append("Payroll")
        self._run(ctx, "send_email", subject="Welcome", body="Welcome! Your accounts:\n" + "\n".join(accounts))
        skipped = [
            {"name": d.name, "reason": "Not on the checklist for this role"}
            for d in departments_service.list_departments(ctx.session, ctx.company_id) if d.name not in told
        ]
        self._run(ctx, "mark_completed", skipped_departments=skipped)

    def on_deadline(self, ctx, days):
        if not ctx.state.get("reminded"):
            ctx.state["reminded"] = True
            self._run(ctx, "send_email", subject="Reminder: documents needed", body="Please send your documents.")
        else:
            self._run(ctx, "escalate")


VARIANTS = {"full": FullVariant, "agent": AgentVariant, "rules": RulesVariant}
