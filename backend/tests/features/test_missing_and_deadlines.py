from datetime import datetime, timedelta, timezone

from app.features.agent import prompts, service as agent_service, tools
from app.features.candidates import service as candidates_service
from app.features.documents import service as documents_service
from tests.helpers import company_id, ready_candidate

ID_OK = '{"valid": true, "matches": "National ID", "reason": "Fine"}'


def started(client, headers, session, fake_llm, documents=("National ID", "Personal photo"), **args):
    candidate_id = ready_candidate(client, headers, fake_llm)
    cid = company_id(client, headers)
    candidate = candidates_service.get_candidate(session, cid, candidate_id)
    tools.execute(session, cid, candidate, "request_documents", {
        "candidate_id": candidate_id, "documents": list(documents), "reason": "start", **args,
    })
    return cid, candidate


def now():
    return datetime.now(timezone.utc)


def aware(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def due_in(candidate):
    return aware(candidate.documents_due_at) - now()


def reply_with_id(client, headers, session, cid, candidate, fake_llm):
    fake_llm.finish("Noted.")  # the reply wakes the agent, which just stops here
    files = [("files", ("id.txt", b"NATIONAL ID Omar Abdullah", "text/plain"))]
    client.post("/mock-inbox", data={"from_address": "x@x.com", "subject": f"[ONB-{candidate.id}]"}, files=files, headers=headers)
    return tools.execute(session, cid, candidate, "read_inbox", {"candidate_id": candidate.id, "reason": "r"})["messages"][0]["documents"][0]["document_id"]


def test_validation_says_what_is_still_missing(client, company_a, session, fake_llm):
    cid, candidate = started(client, company_a, session, fake_llm)
    document_id = reply_with_id(client, company_a, session, cid, candidate, fake_llm)
    fake_llm.say(ID_OK)

    result = tools.execute(session, cid, candidate, "validate_document", {"candidate_id": candidate.id, "document_id": document_id, "reason": "r"})
    assert result["still_missing"] == ["Personal photo"]
    assert "Still missing: Personal photo" in prompts.build_context(session, cid, candidate, "test")
    assert "matches" in fake_llm.text_calls[-1]["system"]


def test_request_sets_a_due_date(client, company_a, session, fake_llm):
    _, candidate = started(client, company_a, session, fake_llm)
    assert timedelta(days=2, hours=23) < due_in(candidate) < timedelta(days=3, hours=1)

    _, other = started(client, company_a, session, fake_llm, due_in_days=7)
    assert due_in(other) > timedelta(days=6)


def test_deadline_check_wakes_only_overdue_candidates_with_missing_documents(client, company_a, session, fake_llm):
    cid, candidate = started(client, company_a, session, fake_llm)

    assert agent_service.check_deadlines(session, cid, now()) == 0
    assert fake_llm.chat_calls == []

    fake_llm.finish("Sent a reminder.")
    later = now() + timedelta(days=4)
    assert agent_service.check_deadlines(session, cid, later) == 1
    assert "deadline_passed" in fake_llm.chat_calls[0]["messages"][1]["content"]
    assert aware(candidate.documents_due_at) > later

    assert agent_service.check_deadlines(session, cid, later) == 0


def test_no_deadline_wake_when_everything_arrived(client, company_a, session, fake_llm):
    cid, candidate = started(client, company_a, session, fake_llm, documents=["National ID"])
    document_id = reply_with_id(client, company_a, session, cid, candidate, fake_llm)
    fake_llm.say(ID_OK)
    documents_service.validate(session, cid, candidate.id, document_id, ["National ID"])

    assert agent_service.check_deadlines(session, cid, now() + timedelta(days=10)) == 0


def test_deadline_endpoint_can_fast_forward(client, company_a, session, fake_llm):
    started(client, company_a, session, fake_llm)
    fake_llm.finish("Sent a reminder.")
    later = (now() + timedelta(days=5)).isoformat()
    assert client.post("/deadlines/check", json={"now": later}, headers=company_a).json() == {"woken": 1}


def test_a_document_covers_a_request_written_with_alternatives(client, company_a, session, fake_llm):
    cid, candidate = started(client, company_a, session, fake_llm, documents=["National ID or Iqama", "Personal photo"])
    document_id = reply_with_id(client, company_a, session, cid, candidate, fake_llm)
    fake_llm.say('{"valid": true, "matches": "National ID", "reason": "Fine"}')

    result = tools.execute(session, cid, candidate, "validate_document", {"candidate_id": candidate.id, "document_id": document_id, "reason": "r"})
    assert result["still_missing"] == ["Personal photo"]
