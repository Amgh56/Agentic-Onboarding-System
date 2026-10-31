def test_company_creates_several_jobs(client, company_a):
    for title in ["Driver", "Accountant"]:
        response = client.post("/jobs", json={"title": title}, headers=company_a)
        assert response.status_code == 201
    assert len(client.get("/jobs", headers=company_a).json()) == 2


def test_update_job_replaces_fields(client, company_a):
    job_id = client.post("/jobs", json={"title": "Driver", "overview": "old"}, headers=company_a).json()["id"]
    updated = client.put(f"/jobs/{job_id}", json={"title": "Senior Driver"}, headers=company_a)
    assert updated.json()["title"] == "Senior Driver"
    assert updated.json()["overview"] == ""


def test_other_company_cannot_see_or_update_job(client, company_a, company_b):
    job_id = client.post("/jobs", json={"title": "Driver"}, headers=company_a).json()["id"]
    assert client.get(f"/jobs/{job_id}", headers=company_b).status_code == 404
    assert client.put(f"/jobs/{job_id}", json={"title": "Hacked"}, headers=company_b).status_code == 404
    assert client.get("/jobs", headers=company_b).json() == []


def test_job_status_defaults_to_onboarding_and_rejects_unknown(client, company_a):
    created = client.post("/jobs", json={"title": "Driver"}, headers=company_a).json()
    assert created["status"] == "onboarding"
    assert client.post("/jobs", json={"title": "X", "status": "draft"}, headers=company_a).status_code == 422

    closed = client.post("/jobs", json={"title": "Old", "status": "closed"}, headers=company_a)
    assert closed.json()["status"] == "closed"

    bad = client.post("/jobs", json={"title": "X", "status": "paused"}, headers=company_a)
    assert bad.status_code == 422


def test_job_setup_fields_are_saved(client, company_a):
    created = client.post("/jobs", json={"title": "Driver"}, headers=company_a).json()
    assert created["stages"] == ["Invited", "Documents", "Contract", "Onboarded"]

    body = {"title": "Driver", "procedure": "Day one: ID check.", "stages": ["A", "B"]}
    updated = client.put(f"/jobs/{created['id']}", json=body, headers=company_a).json()
    assert updated["procedure"] == "Day one: ID check."
    assert updated["stages"] == ["A", "B"]


def test_job_needs_at_least_one_stage(client, company_a):
    response = client.post("/jobs", json={"title": "Driver", "stages": []}, headers=company_a)
    assert response.status_code == 422
