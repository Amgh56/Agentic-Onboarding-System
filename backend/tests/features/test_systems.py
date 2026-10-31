import pytest
from fastapi import HTTPException

from app.features.systems import service

APPLICANT = {
    "full_name_en": "Omar Abdullah",
    "full_name_ar": "عمر عبدالله",
    "phone": "0500000000",
    "email": "omar@gmail.com",
    "date_of_birth": "1995-04-12",
}


def company_id(client, headers):
    return client.get("/companies/me", headers=headers).json()["id"]


def make_candidate(client, headers, name="Omar Abdullah"):
    job_id = client.post("/jobs", json={"title": "Developer"}, headers=headers).json()["id"]
    body = {**APPLICANT, "full_name_en": name}
    return client.post(f"/jobs/{job_id}/candidates", json=body, headers=headers).json()["id"]


def test_new_company_gets_the_default_systems(client, company_a):
    systems = {s["key"]: s for s in client.get("/systems", headers=company_a).json()}
    assert set(systems) == {"work_email", "erp", "github", "slack", "teams", "it_desk"}
    assert systems["github"]["kind"] == "invite"
    assert systems["work_email"]["kind"] == "mailbox"
    assert "backend-team" in [g["name"] for g in systems["github"]["groups"]]
    assert all(s["name_ar"] for s in systems.values())


def test_work_email_is_made_from_the_name(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)

    account = service.create_account(session, cid, candidate_id, "work_email", [])
    assert account.address.startswith("omar.abdullah@")
    assert account.status == "created"


def test_same_name_gets_a_different_address(client, company_a, session):
    cid = company_id(client, company_a)
    first = service.create_account(session, cid, make_candidate(client, company_a), "work_email", [])
    second = service.create_account(session, cid, make_candidate(client, company_a), "work_email", [])
    assert first.address != second.address
    assert second.address.startswith("omar.abdullah2@")


def test_creating_the_same_account_twice_gives_one(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    first = service.create_account(session, cid, candidate_id, "work_email", [])
    again = service.create_account(session, cid, candidate_id, "work_email", [])

    assert first.id == again.id
    contents = client.get("/systems/contents", headers=company_a).json()
    email_system = next(s for s in contents if s["key"] == "work_email")
    assert len(email_system["accounts"]) == 1


def test_other_systems_need_the_work_email_first(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    with pytest.raises(HTTPException) as error:
        service.create_account(session, cid, candidate_id, "erp", ["accountant"])
    assert error.value.status_code == 400


def test_github_is_an_invite_to_the_new_work_email(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    email = service.create_account(session, cid, candidate_id, "work_email", [])

    invite = service.create_account(session, cid, candidate_id, "github", ["backend-team"])
    assert invite.status == "invited"
    assert invite.address == email.address
    assert invite.groups == ["backend-team"]


def test_erp_account_uses_the_work_email(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    email = service.create_account(session, cid, candidate_id, "work_email", [])

    account = service.create_account(session, cid, candidate_id, "erp", ["accountant"])
    assert account.status == "created"
    assert account.address == email.address


def test_unknown_group_or_system_is_refused(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    service.create_account(session, cid, candidate_id, "work_email", [])

    with pytest.raises(HTTPException) as bad_group:
        service.create_account(session, cid, candidate_id, "github", ["made-up-team"])
    assert bad_group.value.status_code == 400

    with pytest.raises(HTTPException) as bad_system:
        service.create_account(session, cid, candidate_id, "salesforce", [])
    assert bad_system.value.status_code == 404


def test_ticket_is_created_once(client, company_a, session):
    cid = company_id(client, company_a)
    candidate_id = make_candidate(client, company_a)
    first = service.create_ticket(session, cid, candidate_id, "Laptop")
    again = service.create_ticket(session, cid, candidate_id, "Laptop")
    assert first.id == again.id


def test_contents_only_show_the_companys_own_data(client, company_a, company_b, session):
    candidate_id = make_candidate(client, company_a)
    service.create_account(session, company_id(client, company_a), candidate_id, "work_email", [])
    service.create_ticket(session, company_id(client, company_a), candidate_id, "Laptop")

    def totals(headers):
        contents = client.get("/systems/contents", headers=headers).json()
        return sum(len(s["accounts"]) + len(s["tickets"]) for s in contents)

    assert totals(company_a) == 2
    assert totals(company_b) == 0


def test_other_companys_candidate_is_refused(client, company_a, company_b, session):
    candidate_id = make_candidate(client, company_a)
    with pytest.raises(HTTPException) as error:
        service.create_account(session, company_id(client, company_b), candidate_id, "work_email", [])
    assert error.value.status_code == 404
