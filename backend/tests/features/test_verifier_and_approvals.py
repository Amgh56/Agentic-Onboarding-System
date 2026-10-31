import json

from app.features.agent import tools, verifier
from app.features.candidates import service as candidates_service
from app.features.documents import service as documents_service
from app.features.notifications.model import Email
from app.features.systems import service as systems_service
from sqlmodel import select
from tests.helpers import company_id, department_id, make_candidate, make_job, ready_candidate

PLAN_JSON = json.dumps({
    "steps": [{"title": "Collect the ID", "details": "Ask for it."}, {"title": "Tell payroll", "details": "Name and job only."}],
})


def setup(client, headers, session, fake_llm, start_mode="auto"):
    job_id = make_job(client, headers)
    job = client.get(f"/jobs/{job_id}", headers=headers).json()
    client.put(f"/jobs/{job_id}", json={**job, "start_mode": start_mode}, headers=headers)
    fake_llm.say(PLAN_JSON)
    client.post(f"/jobs/{job_id}/plan/draft", headers=headers)
    client.post(f"/jobs/{job_id}/plan/approve", headers=headers)
    cid = company_id(client, headers)
    candidate_id = make_candidate(client, headers, job_id)
    candidates_service.set_status(session, cid, candidate_id, "invited")
    return cid, job_id, candidates_service.get_candidate(session, cid, candidate_id)


def call(session, cid, candidate, name, **args):
    return tools.execute(session, cid, candidate, name, {"candidate_id": candidate.id, "reason": "test", **args})


# ---------- start mode


def test_start_mode_is_a_job_setting(client, company_a):
    job_id = make_job(client, company_a)
    job = client.get(f"/jobs/{job_id}", headers=company_a).json()
    assert job["start_mode"] == "auto"
    assert client.put(f"/jobs/{job_id}", json={**job, "start_mode": "ask_first"}, headers=company_a).json()["start_mode"] == "ask_first"
    assert client.put(f"/jobs/{job_id}", json={**job, "start_mode": "sometimes"}, headers=company_a).status_code == 422


# ---------- plan steps and completion


def test_steps_are_ticked_off_and_completion_needs_all_of_them(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm)

    assert "error" in call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-9", "outcome": "done"}])
    progress = call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-1", "outcome": "done"}])
    assert progress == {"done": 1, "total": 2, "remaining": ["Tell payroll"]}

    refused = call(session, cid, candidate, "mark_completed")
    assert "Tell payroll" in refused["error"]

    call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-2", "outcome": "skipped"}])
    assert candidate.step_status["step-2"]["outcome"] == "skipped"


def test_step_review_is_told_the_candidates_role(client, company_a, session, fake_llm, monkeypatch):
    monkeypatch.setattr(verifier, "ENABLED", True)
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    candidate.role = "Backend engineer"

    fake_llm.say('{"approved": true, "reason": "Fine."}')
    call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-1", "outcome": "done"}])
    assert "Candidate role: Backend engineer" in fake_llm.text_calls[-1]["prompt"]


def test_completion_needs_every_department_told_or_skipped_with_a_reason(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-1", "outcome": "done"}, {"step_id": "step-2", "outcome": "done"}])

    refused = call(session, cid, candidate, "mark_completed")
    assert all(name in refused["error"] for name in ("IT", "Payroll", "Finance", "HR"))

    everyone = [{"name": name, "reason": "Not needed for this role"} for name in ("IT", "payroll", "Finance", "HR")]
    assert call(session, cid, candidate, "mark_completed", skipped_departments=everyone) == {"status": "completed"}


def test_an_email_to_a_department_counts_as_telling_it(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    payroll = department_id(client, company_a, "Payroll")
    call(session, cid, candidate, "complete_steps", steps=[{"step_id": "step-1", "outcome": "done"}, {"step_id": "step-2", "outcome": "done"}])
    tools.execute(session, cid, candidate, "send_email", {"department_id": payroll, "subject": "New joiner", "body": "Omar joins", "reason": "r"})

    refused = call(session, cid, candidate, "mark_completed")
    assert "Payroll" not in refused["error"] and "IT" in refused["error"]
    skipped = [{"name": name, "reason": "Not needed"} for name in ("IT", "Finance", "HR")]
    assert call(session, cid, candidate, "mark_completed", skipped_departments=skipped) == {"status": "completed"}
    email = session.exec(select(Email)).all()[-1]
    assert email.regarding_candidate_id == candidate.id


# ---------- start modes and HR decisions


def test_ask_first_turns_risky_actions_into_hr_approvals(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm, start_mode="ask_first")

    first = call(session, cid, candidate, "create_account", system="work_email", groups=[])
    again = call(session, cid, candidate, "create_account", system="work_email", groups=[], reason="other words")
    assert first["status"] == "waiting_for_hr" and again["approval_id"] == first["approval_id"]
    assert systems_service.list_candidate_accounts(session, cid, candidate.id) == []

    pending = client.get("/approvals", params={"candidate_id": candidate.id}, headers=company_a).json()
    assert pending[0]["candidate_name"] == "Omar Abdullah" and pending[0]["status"] == "pending"

    fake_llm.finish("Continuing after HR approval.")
    decided = client.post(f"/approvals/{first['approval_id']}/decide", json={"approve": True, "note": "Go ahead"}, headers=company_a)
    assert decided.json()["status"] == "approved"
    assert len(systems_service.list_candidate_accounts(session, cid, candidate.id)) == 1
    assert "hr_decision" in fake_llm.chat_calls[-1]["messages"][1]["content"]

    rerun = call(session, cid, candidate, "create_account", system="work_email", groups=[])
    assert rerun["status"] == "created"


def test_declined_action_is_not_run_and_not_asked_again(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm, start_mode="ask_first")
    approval_id = call(session, cid, candidate, "create_account", system="work_email", groups=[])["approval_id"]

    fake_llm.finish("Understood.")
    client.post(f"/approvals/{approval_id}/decide", json={"approve": False, "note": "Wait for the contract"}, headers=company_a)
    assert systems_service.list_candidate_accounts(session, cid, candidate.id) == []
    assert "declined" in fake_llm.chat_calls[-1]["messages"][1]["content"]

    again = call(session, cid, candidate, "create_account", system="work_email", groups=[])
    assert "Wait for the contract" in again["error"]
    assert client.post(f"/approvals/{approval_id}/decide", json={"approve": True}, headers=company_a).status_code == 400


def test_notify_mode_runs_the_action_and_leaves_hr_a_notice(client, company_a, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm, start_mode="notify")
    assert call(session, cid, candidate, "create_account", system="work_email", groups=[])["status"] == "created"
    notices = client.get("/approvals", params={"candidate_id": candidate.id}, headers=company_a).json()
    assert notices[0]["kind"] == "notice" and notices[0]["status"] == "done"


def test_other_company_cannot_see_or_decide_approvals(client, company_a, company_b, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm, start_mode="ask_first")
    approval_id = call(session, cid, candidate, "create_account", system="work_email", groups=[])["approval_id"]
    assert client.get("/approvals", headers=company_b).json() == []
    assert client.post(f"/approvals/{approval_id}/decide", json={"approve": True}, headers=company_b).status_code == 404


# ---------- the verifier


def test_verifier_blocks_an_action_it_does_not_approve(client, company_a, session, fake_llm, monkeypatch):
    monkeypatch.setattr(verifier, "ENABLED", True)
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    payroll = department_id(client, company_a, "Payroll")

    fake_llm.say('{"approved": false, "reason": "Payroll does not need the laptop model."}')
    blocked = tools.execute(session, cid, candidate, "send_email", {"department_id": payroll, "subject": "Joiner", "body": "Laptop: MacBook", "reason": "r"})
    assert "laptop model" in blocked["error"]
    assert session.exec(select(Email)).all() == []
    assert "MacBook" in fake_llm.text_calls[-1]["prompt"] and "Salaries" in fake_llm.text_calls[-1]["prompt"]

    fake_llm.say('{"approved": true, "reason": "Fine."}')
    sent = tools.execute(session, cid, candidate, "send_email", {"department_id": payroll, "subject": "Joiner 2", "body": "Omar joins", "reason": "r"})
    assert sent["status"] == "sent"


def received_document(client, headers, session, cid, candidate, fake_llm):
    call(session, cid, candidate, "request_documents", documents=["National ID"])
    files = [("files", ("id.txt", b"NATIONAL ID Omar Abdullah 2031", "text/plain"))]
    fake_llm.finish("Noted.")
    client.post("/mock-inbox", data={"from_address": "omar@gmail.com", "subject": "docs"}, files=files, headers=headers)
    return call(session, cid, candidate, "read_inbox")["messages"][0]["documents"][0]["document_id"]


def test_second_reading_that_agrees_confirms_the_document(client, company_a, session, fake_llm, monkeypatch):
    monkeypatch.setattr(verifier, "ENABLED", True)
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    document_id = received_document(client, company_a, session, cid, candidate, fake_llm)
    fake_llm.say('{"valid": true, "matches": "National ID", "reason": "Fine"}')
    fake_llm.say('{"valid": true, "matches": "National ID", "reason": "Also fine"}')

    result = call(session, cid, candidate, "validate_document", document_id=document_id)
    assert result["status"] == "valid" and result["verified"] is True
    assert fake_llm.text_calls[-1]["model"] == "test-strong"  # the second reader is a different model


def test_readings_that_keep_disagreeing_go_to_hr(client, company_a, session, fake_llm, monkeypatch):
    monkeypatch.setattr(verifier, "ENABLED", True)
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    document_id = received_document(client, company_a, session, cid, candidate, fake_llm)
    for _ in range(2):
        fake_llm.say('{"valid": true, "matches": "National ID", "reason": "Looks valid"}')
        fake_llm.say('{"valid": false, "reason": "The expiry date is unreadable"}')

    result = call(session, cid, candidate, "validate_document", document_id=document_id)
    assert result["status"] == "disputed"
    escalation = client.get("/approvals", params={"candidate_id": candidate.id}, headers=company_a).json()[0]
    assert escalation["kind"] == "escalation"

    fake_llm.finish("Continuing.")
    client.post(f"/approvals/{escalation['id']}/decide", json={"approve": True, "note": "I checked it, it is valid"}, headers=company_a)
    documents = client.get(f"/candidates/{candidate.id}/documents", headers=company_a).json()
    assert documents[0]["status"] == "valid"


# ---------- what the HR screens read


def test_candidate_documents_and_accounts_endpoints(client, company_a, company_b, session, fake_llm):
    cid, _, candidate = setup(client, company_a, session, fake_llm)
    document_id = received_document(client, company_a, session, cid, candidate, fake_llm)
    systems_service.create_account(session, cid, candidate.id, "work_email", [])  # the tool would refuse: the document is unchecked
    call(session, cid, candidate, "create_ticket", item="Laptop")

    documents = client.get(f"/candidates/{candidate.id}/documents", headers=company_a).json()
    assert documents[0]["filename"] == "id.txt" and documents[0]["status"] == "received"
    assert client.get(f"/candidate-documents/{document_id}/download", headers=company_a).content.startswith(b"NATIONAL ID")

    accounts = client.get(f"/candidates/{candidate.id}/accounts", headers=company_a).json()
    assert accounts["accounts"][0]["system_key"] == "work_email"
    assert accounts["tickets"][0]["item"] == "Laptop"

    assert client.get(f"/candidates/{candidate.id}/documents", headers=company_b).status_code == 404
    assert client.get(f"/candidates/{candidate.id}/accounts", headers=company_b).status_code == 404
    assert client.get(f"/candidate-documents/{document_id}/download", headers=company_b).status_code == 404
