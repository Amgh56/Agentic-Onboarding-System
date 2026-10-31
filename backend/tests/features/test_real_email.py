from email.message import EmailMessage

import pytest
from fastapi import HTTPException

from app.features.notifications import mail_client, service
from tests.conftest import signup
from tests.helpers import company_id, department_id, make_candidate, make_job, ready_candidate

GMAIL = {"provider": "smtp", "email_address": "hr@gmail.com", "password": "app-password"}


def raw_email(sender, subject, body="Here are my documents", attachment=None, message_id="<1@mail>"):
    message = EmailMessage()
    message["From"] = f"Omar <{sender}>"
    message["To"] = "hr@gmail.com"
    message["Subject"] = subject
    message["Message-ID"] = message_id
    message.set_content(body)
    if attachment:
        message.add_attachment(attachment[1], maintype="text", subtype="plain", filename=attachment[0])
    return message.as_bytes()


def test_parse_reads_sender_subject_body_and_attachments():
    parsed = mail_client.parse(raw_email("omar@gmail.com", "مستنداتي [ONB-3]", attachment=("هوية.txt", b"ID")))
    assert parsed["from_address"] == "omar@gmail.com"
    assert parsed["subject"] == "مستنداتي [ONB-3]"
    assert "Here are my documents" in parsed["body"]
    assert parsed["attachments"] == [("هوية.txt", "text/plain", b"ID")]
    assert parsed["message_id"] == "<1@mail>"


def test_no_email_settings_means_no_sending(client, session):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    candidate_id = make_candidate(client, headers, make_job(client, headers))
    with pytest.raises(HTTPException) as error:
        service.send_to_candidate(session, company_id(client, headers), candidate_id, "Hi", "Hello", "test")
    assert error.value.status_code == 400
    assert "not set up" in error.value.detail


def test_allow_list_blocks_other_addresses(client, company_a, session):
    client.put("/email-settings", json={"provider": "mock", "email_address": "hr@a.com", "allowed_recipients": ["@companya.example"]}, headers=company_a)
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))

    with pytest.raises(HTTPException) as error:
        service.send_to_candidate(session, cid, candidate_id, "Hi", "Hello", "test")
    assert "allowed" in error.value.detail

    department = {"id": department_id(client, company_a, "IT")}
    email, sent = service.send_to_department(session, cid, department["id"], "Laptop", "Please", "test")
    assert sent is True


def test_real_mode_sends_through_smtp_with_attachments(client, monkeypatch, session):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    client.put("/email-settings", json=GMAIL, headers=headers)
    job_id = make_job(client, headers)
    client.post(f"/jobs/{job_id}/documents", files={"file": ("policy.pdf", b"PDF", "application/pdf")}, headers=headers)
    candidate_id = make_candidate(client, headers, job_id)
    outgoing = []
    monkeypatch.setattr(mail_client, "send", lambda settings, password, to, subject, body, files: outgoing.append((password, to, files)))

    from app.features.agent import tools
    from app.features.candidates import service as candidates_service
    cid = company_id(client, headers)
    candidate = candidates_service.get_candidate(session, cid, candidate_id)
    result = tools.execute(session, cid, candidate, "request_documents", {"candidate_id": candidate_id, "documents": ["National ID"], "reason": "start"})

    assert result["status"] == "sent"
    assert outgoing == [("app-password", "omar@gmail.com", [("policy.pdf", b"PDF")])]


def test_sync_stores_new_replies_once_and_wakes_the_agent(client, monkeypatch, fake_llm):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    client.put("/email-settings", json=GMAIL, headers=headers)
    candidate_id = ready_candidate(client, headers, fake_llm)
    monkeypatch.setattr(mail_client, "send", lambda *args: None)
    fake_llm.act(("request_documents", {"candidate_id": candidate_id, "documents": ["National ID"], "reason": "start"}))
    fake_llm.finish("Waiting.")
    client.post(f"/candidates/{candidate_id}/start", headers=headers)

    inbox = [
        raw_email("omar@gmail.com", "Re: documents", attachment=("id.txt", b"ID")),
        raw_email("hr@gmail.com", "Onboarding test email", message_id="<self@mail>"),
        raw_email("stranger@x.com", "Hello", message_id="<2@mail>"),
    ]
    monkeypatch.setattr(mail_client, "fetch", lambda settings, password, since: inbox)
    fake_llm.finish("Read the reply.")

    first = client.post("/email/sync", headers=headers).json()
    assert first == {"new_messages": 2, "matched": 1}
    assert len(fake_llm.chat_calls) == 3

    second = client.post("/email/sync", headers=headers).json()
    assert second == {"new_messages": 0, "matched": 0}
