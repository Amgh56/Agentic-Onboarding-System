from app.features.approvals import service
from tests.helpers import company_id, make_candidate, make_job


def test_escalation_is_created_once_and_listed(client, company_a, company_b, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a, make_job(client, company_a))

    first = service.create_approval(session, cid, candidate_id, "escalation", "", "Role is unclear")
    again = service.create_approval(session, cid, candidate_id, "escalation", "", "Role is unclear")
    assert first.id == again.id

    listed = client.get("/approvals", headers=company_a).json()
    assert [a["reason"] for a in listed] == ["Role is unclear"]
    assert listed[0]["status"] == "pending"
    assert client.get("/approvals", headers=company_b).json() == []
