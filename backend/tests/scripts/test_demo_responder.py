from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import select

from app.features.candidates import service as candidates_service
from app.features.documents.model import CandidateDocument
from app.features.notifications import service as notifications_service
from app.features.notifications.model import Email, EmailSettings, InboxMessage
from scripts import demo_responder, send_reply
from tests.helpers import approve_plan, company_id, make_candidate, make_job

PDF = b"%PDF-1.4 signed"
START = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self):
        self.current = START

    def now(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


@pytest.fixture
def demo_files(tmp_path, monkeypatch):
    (tmp_path / "omar" / "round1").mkdir(parents=True)
    (tmp_path / "omar" / "round2").mkdir()
    (tmp_path / "omar" / "round1" / "Omar_NDA.pdf").write_bytes(PDF)
    for name in ("Policy", "NDA", "Contract"):
        (tmp_path / "omar" / "round2" / f"Omar_{name}.pdf").write_bytes(PDF)
    monkeypatch.setattr(send_reply, "DEMO_FILES", tmp_path)
    return tmp_path


def setup(client, headers, session, fake_llm):
    cid = company_id(client, headers)
    job_id = make_job(client, headers)
    approve_plan(client, headers, job_id, fake_llm)
    omar = make_candidate(client, headers, job_id, full_name_en="Omar Ateeq", email="omar@gmail.com")
    stranger = make_candidate(client, headers, job_id, full_name_en="Layla Saad", email="layla@gmail.com")
    for candidate_id in (omar, stranger):
        candidates_service.set_status(session, cid, candidate_id, "invited")
    responder = demo_responder.Responder(cid, FakeClock(), delay=10, retry_delay=30, baseline=0)
    return cid, omar, stranger, responder


def agent_email(session, cid, candidate_id, subject, at_seconds, kind="general", documents=None):
    email = Email(
        company_id=cid, candidate_id=candidate_id, to_address="x@example.com", subject=subject, body="b", reason="r",
        kind=kind, documents=documents or [], created_at=START + timedelta(seconds=at_seconds),
    )
    session.add(email)
    session.commit()
    return email


def replies(session):
    return session.exec(select(InboxMessage)).all()


def test_replies_once_after_the_delay_to_a_document_request(client, company_a, session, fake_llm, demo_files):
    cid, omar, _, responder = setup(client, company_a, session, fake_llm)
    agent_email(session, cid, omar, f"Documents needed [ONB-{omar}]", 0, "documents_request", ["NDA", "Policy", "Contract"])
    fake_llm.finish("Looked.")

    responder.tick(session)
    assert replies(session) == []  # the delay has not passed
    responder.clock.advance(10)
    lines = responder.tick(session)
    responder.clock.advance(20)
    assert responder.tick(session) == []  # it does not answer the same email twice

    assert lines == ["Omar replied (round 1) after 10s"]
    [message] = replies(session)
    assert message.candidate_id == omar and message.body == demo_responder.FIRST_BODY
    assert [a["filename"] for a in message.attachments] == ["Omar_NDA.pdf"]  # round1 files


def test_does_not_reply_to_the_welcome_email(client, company_a, session, fake_llm, demo_files):
    cid, omar, _, responder = setup(client, company_a, session, fake_llm)
    agent_email(session, cid, omar, f"Documents needed [ONB-{omar}]", 0, "documents_request", ["NDA"])
    session.add(CandidateDocument(
        company_id=cid, candidate_id=omar, message_id=1, filename="n.pdf", stored_name="n", content_type="application/pdf",
        status="valid", result={"matches": "NDA"},
    ))
    agent_email(session, cid, omar, "Welcome aboard", 5)
    session.commit()

    responder.clock.advance(60)
    assert responder.tick(session) == [] and replies(session) == []


def test_a_second_email_gets_the_round_two_files_after_the_retry_delay(client, company_a, session, fake_llm, demo_files):
    cid, omar, _, responder = setup(client, company_a, session, fake_llm)
    agent_email(session, cid, omar, f"Documents needed [ONB-{omar}]", 0, "documents_request", ["NDA", "Policy", "Contract"])
    fake_llm.finish("Looked.")
    fake_llm.finish("Looked again.")
    responder.clock.advance(10)
    responder.tick(session)

    agent_email(session, cid, omar, f"Still needed [ONB-{omar}]", 40)
    responder.clock.advance(30)
    responder.tick(session)  # it sees the problem email
    responder.clock.advance(20)
    assert responder.tick(session) == []  # 20s old: the issue stays on screen
    responder.clock.advance(10)
    lines = responder.tick(session)

    assert lines == ["Omar replied (round 2) after 30s"]
    second = replies(session)[-1]
    assert len(second.attachments) == 3 and second.body == demo_responder.LATER_BODY


def test_ignores_other_applicants_and_emails_from_before_it_started(client, company_a, session, fake_llm, demo_files):
    cid, omar, stranger, responder = setup(client, company_a, session, fake_llm)
    old = agent_email(session, cid, omar, f"Old request [ONB-{omar}]", -100, "documents_request", ["NDA"])
    responder.baseline = old.id
    agent_email(session, cid, stranger, f"Documents needed [ONB-{stranger}]", 0, "documents_request", ["NDA"])

    responder.clock.advance(100)
    assert responder.tick(session) == [] and replies(session) == []


def test_refuses_to_start_unless_email_is_in_test_mode(client, company_a, session):
    cid = company_id(client, company_a)
    demo_responder.require_test_mode(session, cid)  # the test company is in test mode

    settings = session.exec(select(EmailSettings)).one()
    settings.provider = "smtp"
    session.add(settings)
    session.commit()
    with pytest.raises(SystemExit, match="test mode"):
        demo_responder.require_test_mode(session, cid)
