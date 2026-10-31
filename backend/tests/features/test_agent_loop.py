from sqlmodel import select

from app.features.agent import loop
from app.features.agent.model import ActionLog
from app.features.agent.prompts import SYSTEM_PROMPT
from app.features.approvals.model import Approval
from tests.helpers import make_candidate, make_job, ready_candidate


def test_start_needs_an_approved_plan(client, company_a, fake_llm):
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    assert client.post(f"/candidates/{candidate_id}/start", headers=company_a).status_code == 400
    assert fake_llm.chat_calls == []


def test_other_company_cannot_start(client, company_a, company_b, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm)
    assert client.post(f"/candidates/{candidate_id}/start", headers=company_b).status_code == 404


def test_run_acts_then_stops_when_waiting(client, company_a, session, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm, role="Backend developer")
    fake_llm.act(("request_documents", {"candidate_id": candidate_id, "documents": ["National ID"], "channel": "email", "reason": "The plan starts with documents"}))
    fake_llm.finish("Waiting for the candidate to send the national ID.")

    response = client.post(f"/candidates/{candidate_id}/start", headers=company_a)
    assert response.status_code == 200
    assert response.json() == {"steps": 2, "summary": "Waiting for the candidate to send the national ID."}

    first_call = fake_llm.chat_calls[0]
    assert first_call["model"] == "test-strong"
    context = first_call["messages"][1]["content"]
    for expected in ["Backend Developer", "Builds our APIs", "Collect the national ID", "Collect documents",
                     "IT", "backend-team", "Omar Abdullah", "Backend developer", f"ONB-{candidate_id}", "HR pressed Start"]:
        assert expected in context, expected

    second_call = fake_llm.chat_calls[1]["messages"]
    assert second_call[-1]["role"] == "tool" and '"sent"' in second_call[-1]["content"]

    assert [log.tool for log in session.exec(select(ActionLog)).all()] == ["request_documents"]
    titles = [e["title"] for e in client.get(f"/candidates/{candidate_id}/events", headers=company_a).json()]
    assert titles[0] == "Run finished" and "Requested documents" in titles


def test_bad_tool_arguments_do_not_stop_the_run(client, company_a, session, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm)
    fake_llm.chat_replies.append({
        "role": "assistant", "content": None,
        "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "create_ticket", "arguments": "{not json"}}],
    })
    fake_llm.finish("Done for now.")

    assert client.post(f"/candidates/{candidate_id}/start", headers=company_a).json()["summary"] == "Done for now."
    assert '"error"' in fake_llm.chat_calls[1]["messages"][-1]["content"]


def test_step_limit_stops_the_run_and_escalates(client, company_a, session, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm)
    for _ in range(loop.MAX_STEPS):
        fake_llm.act(("create_ticket", {"candidate_id": candidate_id, "item": "Laptop", "reason": "again"}))

    result = client.post(f"/candidates/{candidate_id}/start", headers=company_a).json()
    assert result["steps"] == loop.MAX_STEPS
    assert "step limit" in result["summary"]
    assert len(fake_llm.chat_calls) == loop.MAX_STEPS
    assert session.exec(select(Approval).where(Approval.kind == "escalation")).first() is not None


def test_reply_wakes_the_agent_only_after_start(client, company_a, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm)
    data = {"from_address": "omar@gmail.com", "subject": "docs"}

    client.post("/mock-inbox", data=data, headers=company_a)
    assert fake_llm.chat_calls == []

    fake_llm.act(("request_documents", {"candidate_id": candidate_id, "documents": ["National ID"], "reason": "start"}))
    fake_llm.finish("Waiting.")
    client.post(f"/candidates/{candidate_id}/start", headers=company_a)

    fake_llm.finish("Read the reply.")
    client.post("/mock-inbox", data={**data, "subject": "docs again"}, headers=company_a)
    assert len(fake_llm.chat_calls) == 3
    assert "document_received" in fake_llm.chat_calls[2]["messages"][1]["content"]


def test_agent_does_not_email_hr_about_progress():
    assert "do not email the HR department" in SYSTEM_PROMPT


def test_agent_is_told_to_keep_going_until_it_is_really_blocked():
    assert "Keep going through the steps in the same run" in SYSTEM_PROMPT
    assert "The verifier answers inside the tool result" in SYSTEM_PROMPT


def test_agent_is_told_to_match_roles_sensibly_and_not_to_escalate_over_missing_groups():
    prompt = " ".join(SYSTEM_PROMPT.split())
    assert "a backend engineer is a developer" in prompt
    assert "no groups; do not escalate for that" in prompt


def test_the_agent_asks_hr_when_a_title_could_fit_several_roles():
    prompt = " ".join(SYSTEM_PROMPT.split())
    assert "could fit more than one role, or none, ask HR before creating any role account" in prompt
