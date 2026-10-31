import logging

import pytest
from sqlmodel import select

from app.features.agent import service as agent_service
from app.features.candidates import service as candidates_service
from app.features.documents.model import CandidateDocument
from app.features.notifications import service as notifications_service
from app.features.notifications.model import InboxMessage
from scripts import send_reply
from tests.helpers import approve_plan, company_id, make_candidate, make_job

PDF = b"%PDF-1.4 signed"


@pytest.fixture
def demo_files(tmp_path, monkeypatch):
    for persona in ("omar", "yousef"):
        (tmp_path / persona).mkdir()
        for name in ("Policy", "NDA", "Contract"):
            (tmp_path / persona / f"{persona.title()}_{name}.pdf").write_bytes(PDF)
    (tmp_path / "omar" / "round1").mkdir()
    (tmp_path / "omar" / "round1" / "Omar_NDA.pdf").write_bytes(PDF)
    monkeypatch.setattr(send_reply, "DEMO_FILES", tmp_path)
    return tmp_path


def two_applicants(client, headers, session, fake_llm):
    """Omar and Yousef, both waiting for documents, with the agent's request email sent to each."""
    cid = company_id(client, headers)
    job_id = make_job(client, headers)
    approve_plan(client, headers, job_id, fake_llm)
    ids = {
        "omar": make_candidate(client, headers, job_id, full_name_en="Omar Ateeq", email="omar@gmail.com"),
        "yousef": make_candidate(client, headers, job_id, full_name_en="Yousef Haitham", email="yousef@gmail.com"),
    }
    for candidate_id in ids.values():
        candidates_service.set_status(session, cid, candidate_id, "invited")
        subject = f"Documents needed for your onboarding [ONB-{candidate_id}]"
        notifications_service.send_to_candidate(
            session, cid, candidate_id, subject, "Please send them.", "test", kind="documents_request", documents=["NDA"],
        )
    return cid, ids


def test_a_reply_with_three_attachments_reaches_the_right_applicant(client, company_a, session, fake_llm, demo_files):
    cid, ids = two_applicants(client, company_a, session, fake_llm)
    fake_llm.act(("read_inbox", {"reason": "A reply arrived."}))
    fake_llm.finish("Checking the documents.")

    line = send_reply.send(session, cid, "yousef")

    assert "Yousef" in line and "3" in line
    message = session.exec(select(InboxMessage)).one()
    assert message.candidate_id == ids["yousef"]
    assert message.subject == f"Re: Documents needed for your onboarding [ONB-{ids['yousef']}]"
    assert message.in_reply_to
    documents = session.exec(select(CandidateDocument)).all()
    assert {d.candidate_id for d in documents} == {ids["yousef"]} and len(documents) == 3
    assert len(fake_llm.chat_calls) == 2  # the agent woke up and read the inbox


def test_a_round_sends_the_files_in_its_own_folder(client, company_a, session, fake_llm, demo_files):
    cid, ids = two_applicants(client, company_a, session, fake_llm)
    fake_llm.finish("Looked at it.")

    send_reply.send(session, cid, "omar", round_number=1)

    assert [a["filename"] for a in session.exec(select(InboxMessage)).one().attachments] == ["Omar_NDA.pdf"]


def test_a_reply_that_matches_nobody_is_left_alone_and_logged(client, company_a, session, fake_llm, caplog):
    cid, _ = two_applicants(client, company_a, session, fake_llm)
    message = notifications_service.drop_message(session, cid, "stranger@example.com", "Hello there", "Hi", [])

    with caplog.at_level(logging.INFO):
        result = agent_service.receive(session, cid, [message])

    assert result == {"new_messages": 1, "matched": 0}
    assert message.candidate_id is None and fake_llm.chat_calls == []
    assert "stranger@example.com" in caplog.text and "matched no applicant" in caplog.text
