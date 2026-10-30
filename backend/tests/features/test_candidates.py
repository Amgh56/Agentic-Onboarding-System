APPLICANT = {
    "full_name_en": "Omar Abdullah",
    "full_name_ar": "عمر عبدالله",
    "phone": "0500000000",
    "email": "omar@example.com",
    "date_of_birth": "1995-04-12",
}

CSV = (
    "full_name_en,full_name_ar,phone,email,date_of_birth\n"
    "Sara Mohammed,سارة محمد,0511111111,sara@example.com,1998-01-02\n"
    "Khalid Ali,خالد علي,0522222222,khalid@example.com,1992-07-30\n"
)


def make_job(client, headers, **extra):
    return client.post("/jobs", json={"title": "Driver", **extra}, headers=headers).json()["id"]


def test_new_applicant_starts_in_first_stage(client, company_a):
    job_id = make_job(client, company_a, stages=["New", "Done"])
    created = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a)
    assert created.status_code == 201
    assert created.json()["stage"] == "New"
    assert len(client.get(f"/jobs/{job_id}/candidates", headers=company_a).json()) == 1


def test_applicant_needs_all_fields(client, company_a):
    job_id = make_job(client, company_a)
    bad = {**APPLICANT, "date_of_birth": "not a date"}
    assert client.post(f"/jobs/{job_id}/candidates", json=bad, headers=company_a).status_code == 422


def test_move_between_stages(client, company_a):
    job_id = make_job(client, company_a, stages=["New", "Done"])
    candidate = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()

    moved = client.put(f"/candidates/{candidate['id']}/stage", json={"stage": "Done"}, headers=company_a)
    assert moved.json()["stage"] == "Done"

    unknown = client.put(f"/candidates/{candidate['id']}/stage", json={"stage": "Nope"}, headers=company_a)
    assert unknown.status_code == 400


def test_csv_import(client, company_a):
    job_id = make_job(client, company_a)
    files = {"file": ("applicants.csv", CSV.encode("utf-8"), "text/csv")}
    response = client.post(f"/jobs/{job_id}/candidates/import", files=files, headers=company_a)
    assert response.status_code == 201
    assert [c["full_name_ar"] for c in response.json()] == ["سارة محمد", "خالد علي"]


def test_csv_with_bad_row_imports_nothing(client, company_a):
    job_id = make_job(client, company_a)
    bad_csv = CSV + "Broken,,0533333333,b@example.com,2000-01-01\n"
    files = {"file": ("applicants.csv", bad_csv.encode("utf-8"), "text/csv")}
    response = client.post(f"/jobs/{job_id}/candidates/import", files=files, headers=company_a)
    assert response.status_code == 400
    assert client.get(f"/jobs/{job_id}/candidates", headers=company_a).json() == []


def test_counts(client, company_a):
    job_id = make_job(client, company_a, stages=["New", "Done"])
    first = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()
    client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a)
    client.put(f"/candidates/{first['id']}/stage", json={"stage": "Done"}, headers=company_a)

    counts = client.get("/candidates/counts", headers=company_a).json()
    assert counts == [{"job_id": job_id, "applicants": 2, "in_progress": 1, "completed": 1}]


def test_other_company_cannot_touch_applicants(client, company_a, company_b):
    job_id = make_job(client, company_a)
    candidate = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()

    assert client.get(f"/jobs/{job_id}/candidates", headers=company_b).status_code == 404
    assert client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_b).status_code == 404
    moved = client.put(f"/candidates/{candidate['id']}/stage", json={"stage": "Documents"}, headers=company_b)
    assert moved.status_code == 404
    assert client.get("/candidates/counts", headers=company_b).json() == []


def test_candidate_profile_and_activity_log(client, company_a):
    job_id = make_job(client, company_a, stages=["New", "Done"])
    candidate = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()
    client.put(f"/candidates/{candidate['id']}/stage", json={"stage": "Done"}, headers=company_a)

    assert client.get(f"/candidates/{candidate['id']}", headers=company_a).json()["stage"] == "Done"
    events = client.get(f"/candidates/{candidate['id']}/events", headers=company_a).json()
    assert [e["title"] for e in events] == ["Moved to Done", "Applicant added"]
    assert events[0]["actor"] == "hr"


def test_other_company_cannot_read_profile_or_activity(client, company_a, company_b):
    job_id = make_job(client, company_a)
    candidate = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()
    assert client.get(f"/candidates/{candidate['id']}", headers=company_b).status_code == 404
    assert client.get(f"/candidates/{candidate['id']}/events", headers=company_b).status_code == 404
