import re

from app.features.agent import tools
from app.features.candidates import service as candidates_service
from app.features.notifications.model import Email
from sqlmodel import select
from tests.helpers import company_id, ready_candidate


def request_by_link(client, headers, session, candidate_id):
    cid = company_id(client, headers)
    candidate = candidates_service.get_candidate(session, cid, candidate_id)
    tools.execute(session, cid, candidate, "request_documents", {
        "candidate_id": candidate_id, "documents": ["National ID"], "channel": "upload_link", "reason": "procedure says upload link",
    })
    body = session.exec(select(Email)).all()[-1].body
    return re.search(r"http://testserver(/portal/upload/\S+)", body).group(1)


def test_upload_link_flow(client, company_a, session, fake_llm):
    candidate_id = ready_candidate(client, company_a, fake_llm)
    link = request_by_link(client, company_a, session, candidate_id)

    page = client.get(link)
    assert page.status_code == 200
    assert "Omar Abdullah" in page.text and "National ID" in page.text

    fake_llm.finish("Read the upload.")
    done = client.post(link, files=[("files", ("id.txt", b"NATIONAL ID", "text/plain"))])
    assert done.status_code == 200

    message = client.get("/candidates/%d/events" % candidate_id, headers=company_a)
    assert message.status_code == 200
    assert len(fake_llm.chat_calls) == 1
    assert "document_received" in fake_llm.chat_calls[0]["messages"][1]["content"]


def test_bad_or_finished_links_are_refused(client, company_a, session, fake_llm):
    assert client.get("/portal/upload/not-a-token").status_code == 404

    candidate_id = ready_candidate(client, company_a, fake_llm)
    link = request_by_link(client, company_a, session, candidate_id)
    candidates_service.set_status(session, company_id(client, company_a), candidate_id, "completed")
    assert client.get(link).status_code == 400
