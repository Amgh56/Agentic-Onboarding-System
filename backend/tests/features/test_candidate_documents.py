from app.features.documents import service
from tests.helpers import company_id, make_candidate, make_job

VALID = '{"valid": true, "reason": "Name matches, expires 2031.", "document_type": "National ID"}'


def add_document(session, cid, candidate_id, filename, content_type, data):
    stored_name = service.save_upload(filename, data)
    return service.add_candidate_document(session, cid, candidate_id, 1, filename, stored_name, content_type)


def test_text_document_is_checked_once(client, company_a, session, fake_llm):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    document = add_document(session, cid, candidate_id, "id.txt", "text/plain", b"NATIONAL ID\nName: Omar Abdullah")
    fake_llm.say(VALID)

    result = service.validate(session, cid, candidate_id, document.id, ["National ID"])
    again = service.validate(session, cid, candidate_id, document.id, ["National ID"])

    assert result["status"] == "valid"
    assert again == result
    assert len(fake_llm.text_calls) == 1
    assert "Name: Omar Abdullah" in fake_llm.text_calls[0]["prompt"]
    assert "National ID" in fake_llm.text_calls[0]["prompt"]


def test_image_document_is_sent_to_the_model_as_an_image(client, company_a, session, fake_llm):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    document = add_document(session, cid, candidate_id, "id.png", "image/png", b"\x89PNG fake")
    fake_llm.say('{"valid": false, "reason": "Too blurry to read the expiry date."}')

    result = service.validate(session, cid, candidate_id, document.id, ["National ID"])
    assert result["status"] == "rejected"
    assert fake_llm.text_calls[0]["file"] == (b"\x89PNG fake", "image/png", "id.png")


def test_unreadable_file_is_rejected_without_a_model_call(client, company_a, session, fake_llm):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    document = add_document(session, cid, candidate_id, "id.docx", "application/msword", b"\x00\x01\x02")

    result = service.validate(session, cid, candidate_id, document.id, ["National ID"])
    assert result["status"] == "rejected"
    assert fake_llm.text_calls == []


def test_pdf_is_sent_to_the_model_as_a_file_so_signatures_are_visible(client, company_a, session, fake_llm):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))
    document = add_document(session, cid, candidate_id, "contract.pdf", "application/pdf", b"%PDF-1.4 scanned")
    fake_llm.say('{"valid": false, "reason": "Page 2 is not signed."}')

    result = service.validate(session, cid, candidate_id, document.id, ["contract.pdf (Please sign at the end of each page)"])
    assert result["status"] == "rejected"
    assert fake_llm.text_calls[0]["file"] == (b"%PDF-1.4 scanned", "application/pdf", "contract.pdf")
    assert "sign at the end of each page" in fake_llm.text_calls[0]["prompt"]
