import pytest
from fastapi import HTTPException

from app.features.notifications import service
from tests.helpers import company_id, department_id, make_candidate, make_job


def test_email_to_candidate_is_sent_once(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))

    email, created = service.send_to_candidate(session, cid, candidate_id, "Welcome", "Hello", "Say hello")
    again, created_again = service.send_to_candidate(session, cid, candidate_id, "Welcome", "Hello", "Say hello")

    assert created is True and created_again is False
    assert email.id == again.id
    assert email.to_address == "omar@gmail.com"


def test_email_to_department_uses_its_address(client, company_a, company_b, session):
    it = department_id(client, company_a, "IT")
    email, _ = service.send_to_department(session, company_id(client, company_a), it, "Laptop", "Please", "New hire")
    assert email.to_address.startswith("it@")

    with pytest.raises(HTTPException) as error:
        service.send_to_department(session, company_id(client, company_b), it, "Laptop", "Please", "New hire")
    assert error.value.status_code == 404


def drop(client, headers, sender, subject, files=None):
    data = {"from_address": sender, "subject": subject, "body": "Here you go"}
    return client.post("/mock-inbox", data=data, files=files or [], headers=headers)


def test_reply_is_matched_by_sender_address(client, company_a):
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    files = [("files", ("id.txt", b"NATIONAL ID", "text/plain"))]
    message = drop(client, company_a, "Omar@Gmail.com", "Re: documents", files).json()
    assert message["candidate_id"] == candidate_id
    assert [a["filename"] for a in message["attachments"]] == ["id.txt"]


def test_reply_is_matched_by_reference_code(client, company_a):
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    message = drop(client, company_a, "someone@else.com", f"Re: documents [ONB-{candidate_id}]").json()
    assert message["candidate_id"] == candidate_id


def test_unknown_sender_is_not_matched(client, company_a):
    make_candidate(client, company_a, make_job(client, company_a))
    assert drop(client, company_a, "stranger@x.com", "Hello").json()["candidate_id"] is None


def test_reference_code_of_another_company_is_not_matched(client, company_a, company_b):
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    message = drop(client, company_b, "x@x.com", f"Re: [ONB-{candidate_id}]").json()
    assert message["candidate_id"] is None


def test_outbox_shows_only_own_company(client, company_a, company_b, session):
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    service.send_to_candidate(session, company_id(client, company_a), candidate_id, "Welcome", "Hi", "Hello")

    assert len(client.get("/outbox", headers=company_a).json()) == 1
    assert client.get("/outbox", headers=company_b).json() == []
