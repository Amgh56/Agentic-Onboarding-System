import re

from sqlmodel import select

from app.features.agent import tools
from app.features.candidates import service as candidates_service
from app.features.notifications.model import Email
from tests.helpers import company_id, make_candidate, make_job


def setup(client, headers, session):
    job_id = make_job(client, headers)
    contract = client.post(
        f"/jobs/{job_id}/documents",
        data={"instructions": "Please sign at the end of each page"},
        files={"file": ("contract.pdf", b"%PDF contract", "application/pdf")},
        headers=headers,
    ).json()
    client.post(f"/jobs/{job_id}/documents", files={"file": ("handbook.pdf", b"%PDF handbook", "application/pdf")}, headers=headers)
    cid = company_id(client, headers)
    candidate = candidates_service.get_candidate(session, cid, make_candidate(client, headers, job_id))
    return cid, job_id, contract, candidate


def call(session, cid, candidate, name, **args):
    return tools.execute(session, cid, candidate, name, {"candidate_id": candidate.id, "reason": "test", **args})


def test_instructions_are_saved_and_can_be_changed(client, company_a, session):
    _, job_id, contract, _ = setup(client, company_a, session)
    assert contract["instructions"] == "Please sign at the end of each page"

    updated = client.put(f"/documents/{contract['id']}", json={"instructions": "Sign and date every page"}, headers=company_a)
    assert updated.json()["instructions"] == "Sign and date every page"
    listed = client.get(f"/jobs/{job_id}/documents", headers=company_a).json()
    assert [d["instructions"] for d in listed] == ["Sign and date every page", ""]


def test_documents_with_instructions_must_come_back(client, company_a, session):
    cid, _, _, candidate = setup(client, company_a, session)
    call(session, cid, candidate, "request_documents", documents=["National ID"])

    email = session.exec(select(Email)).all()[-1]
    assert email.documents == ["National ID", "contract.pdf (Please sign at the end of each page)"]
    assert "contract.pdf (Please sign at the end of each page)" in email.body
    assert email.attachments == ["contract.pdf", "handbook.pdf"]


def test_missing_documents_email_lists_everything_still_needed(client, company_a, session, fake_llm):
    cid, _, _, candidate = setup(client, company_a, session)
    call(session, cid, candidate, "request_documents", documents=["National ID"])
    files = [("files", ("id.png", b"\x89PNG", "image/png"))]
    fake_llm.say('{"valid": false, "reason": "The photo is too blurry to read."}')
    client.post("/mock-inbox", data={"from_address": "omar@gmail.com", "subject": "docs"}, files=files, headers=company_a)
    document_id = call(session, cid, candidate, "read_inbox")["messages"][0]["documents"][0]["document_id"]
    call(session, cid, candidate, "validate_document", document_id=document_id)

    result = call(session, cid, candidate, "request_missing_documents")
    assert result["missing"] == ["National ID", "contract.pdf (Please sign at the end of each page)"]
    email = session.exec(select(Email)).all()[-1]
    assert email.subject.startswith("Still needed for your onboarding")
    assert "too blurry" in email.body and "contract.pdf" in email.body and "عمر عبدالله" in email.body

    reminder = call(session, cid, candidate, "request_missing_documents", reminder=True)
    assert reminder["status"] == "sent"
    assert session.exec(select(Email)).all()[-1].subject.startswith("Reminder:")


def test_missing_documents_email_keeps_the_upload_link(client, company_a, session):
    cid, _, _, candidate = setup(client, company_a, session)
    call(session, cid, candidate, "request_documents", documents=["National ID"], channel="upload_link")
    call(session, cid, candidate, "request_missing_documents")
    body = session.exec(select(Email)).all()[-1].body
    assert re.search(r"http://testserver/portal/upload/\S+", body)


def test_nothing_missing_means_no_email(client, company_a, session):
    cid = company_id(client, company_a)
    candidate = candidates_service.get_candidate(session, cid, make_candidate(client, company_a, make_job(client, company_a)))
    call(session, cid, candidate, "request_documents", documents=["National ID"])
    session.exec(select(Email)).all()
    assert "error" not in call(session, cid, candidate, "request_missing_documents")  # the ID is still missing

    from app.features.documents import service as documents_service
    files = [("files", ("id.txt", b"ID", "text/plain"))]
    client.post("/mock-inbox", data={"from_address": "omar@gmail.com", "subject": "docs"}, files=files, headers=company_a)
    document_id = call(session, cid, candidate, "read_inbox")["messages"][0]["documents"][0]["document_id"]
    documents_service.save_result(session, cid, document_id, "valid", {"valid": True, "matches": "National ID", "reason": "ok"})
    assert "Nothing is missing" in call(session, cid, candidate, "request_missing_documents")["error"]
