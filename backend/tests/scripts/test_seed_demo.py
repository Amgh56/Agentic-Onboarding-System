import re

from app.features.agent import prompts
from app.features.candidates import service as candidates_service
from app.features.departments import service as departments_service
from app.features.documents import service as documents_service
from app.features.jobs import service as jobs_service
from app.features.notifications import service as notifications_service
from app.features.notifications.schema import EmailSettingsSave
from app.features.plans import service as plans_service
from app.features.systems import service as systems_service
from scripts import seed_demo
from tests.helpers import PLAN_JSON


def test_seed_builds_the_demo_and_is_safe_to_run_twice(session, fake_llm):
    fake_llm.say(PLAN_JSON)
    company_id, job_id = seed_demo.seed(session)
    assert seed_demo.seed(session) == (company_id, job_id)
    assert len(fake_llm.text_calls) == 1  # the plan is drafted once, not again on the second run

    job = jobs_service.get_job(session, company_id, job_id)
    assert job.title == "Nov 2026 cohort" and job.start_mode == "auto"
    assert job.procedure == seed_demo.PROCEDURE
    assert "tell hr" not in job.procedure.lower()
    assert job.procedure.index("tell Payroll") < job.procedure.index("ask IT for a laptop")  # we are HR: we see everything in the app
    assert not re.search(r"^\s*\d+\.", job.procedure, re.M)  # plain text; the plan numbers the steps
    assert plans_service.has_approved_plan(session, company_id, job_id)

    documents = documents_service.list_documents(session, company_id, job_id)
    assert [d.filename for d in documents] == ["Cybersecurity_Policy.pdf", "NDA.pdf", "Employment_Contract.pdf"]
    assert {d.instructions for d in documents} == {""}  # the procedure says what to do with them
    blanks = {name: (seed_demo.TEMPLATES / name).read_bytes() for name, _ in documents_service.job_files(session, company_id, job_id)}
    assert dict(documents_service.job_files(session, company_id, job_id)) == blanks

    departments = departments_service.list_departments(session, company_id)
    assert [d.name for d in departments] == ["IT", "Payroll", "Finance", "HR"]
    assert [d.email for d in departments] == ["it@demo.com", "payroll@demo.com", "finance@demo.com", "hr@demo.com"]
    assert systems_service.get_system(session, company_id, "work_email").config["domain"] == "demo.com"

    candidates = candidates_service.list_candidates(session, company_id, job_id)
    assert [(c.full_name_en, c.role) for c in candidates] == [
        ("Yousef Haitham AlQurashi", "Backend engineer"),
        ("Abdulaziz Ahmad", "Growth Lead"),
        ("Omar Ateeq Alghamdi", "Sales manager"),
    ]
    assert {c.status for c in candidates} == {"draft"}  # nothing starts until the demo does
    assert "role: Growth Lead" in prompts.build_context(session, company_id, candidates[1], "test")


def test_reset_puts_every_applicant_back_to_waiting_and_clears_what_happened(session, fake_llm):
    fake_llm.say(PLAN_JSON)
    company_id, job_id = seed_demo.seed(session)
    notifications_service.save_settings(session, company_id, EmailSettingsSave(provider="mock", email_address="demo@demo.com"))
    candidate = candidates_service.list_candidates(session, company_id, job_id)[0]
    systems_service.create_account(session, company_id, candidate.id, "work_email", [])
    notifications_service.send_to_candidate(session, company_id, candidate.id, "Hello", "Hi", "test")
    candidates_service.set_status(session, company_id, candidate.id, "completed")
    candidates_service.set_step_outcomes(session, company_id, candidate.id, {"step-1": {"outcome": "done", "reason": "x"}})

    seed_demo.reset(session, company_id)

    assert systems_service.list_candidate_accounts(session, company_id, candidate.id) == []
    assert notifications_service.list_for_candidate(session, company_id, candidate.id) == []
    assert candidates_service.list_events(session, company_id, candidate.id) == []
    candidates = candidates_service.list_candidates(session, company_id, job_id)
    assert {(c.status, c.stage, tuple(c.step_status)) for c in candidates} == {("draft", "Invited", ())}
    assert len(candidates) == 3 and plans_service.has_approved_plan(session, company_id, job_id)
