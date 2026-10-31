from app.features.agent import service as agent_service
from app.features.candidates import service as candidates_service
from tests.helpers import APPLICANT, PLAN_JSON, approve_plan, company_id, make_candidate, make_job


def job_with_plan(client, headers, fake_llm):
    job_id = make_job(client, headers)
    fake_llm.say(PLAN_JSON)
    client.post(f"/jobs/{job_id}/plan/draft", headers=headers)
    return job_id


def test_adding_an_applicant_to_a_job_with_a_procedure_starts_onboarding(client, company_a, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    fake_llm.finish("Waiting for documents.")

    candidate = client.post(f"/jobs/{job_id}/candidates", json=APPLICANT, headers=company_a).json()
    assert len(fake_llm.chat_calls) == 1
    assert "onboarding starts now" in fake_llm.chat_calls[0]["messages"][1]["content"]
    assert client.get(f"/candidates/{candidate['id']}", headers=company_a).json()["status"] == "invited"


def test_several_applicants_are_added_at_once_and_all_start(client, company_a, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    fake_llm.finish("Waiting.")
    fake_llm.finish("Waiting.")

    body = [APPLICANT, {**APPLICANT, "full_name_en": "Sara Ali", "email": "sara@gmail.com"}]
    created = client.post(f"/jobs/{job_id}/candidates/bulk", json=body, headers=company_a)
    assert created.status_code == 201 and len(created.json()) == 2
    assert len(fake_llm.chat_calls) == 2


def test_csv_import_starts_onboarding_too(client, company_a, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    fake_llm.finish("Waiting.")
    csv = "full_name_en,full_name_ar,phone,email,date_of_birth\nSara Ali,سارة علي,0511,sara@gmail.com,1998-01-02\n"
    client.post(f"/jobs/{job_id}/candidates/import", files={"file": ("a.csv", csv.encode(), "text/csv")}, headers=company_a)
    assert len(fake_llm.chat_calls) == 1


def test_without_a_procedure_applicants_wait_and_saving_it_starts_them(client, company_a, fake_llm, monkeypatch):
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    job_id = make_job(client, company_a, procedure="")
    candidate_id = make_candidate(client, company_a, job_id)
    assert fake_llm.chat_calls == []
    assert client.get(f"/candidates/{candidate_id}", headers=company_a).json()["status"] == "draft"

    job = client.get(f"/jobs/{job_id}", headers=company_a).json()
    client.put(f"/jobs/{job_id}", json={**job, "procedure": "Collect the ID."}, headers=company_a)
    fake_llm.say(PLAN_JSON)
    fake_llm.finish("Waiting.")
    client.post(f"/jobs/{job_id}/plan/draft", headers=company_a)
    assert len(fake_llm.chat_calls) == 1
    assert client.get(f"/candidates/{candidate_id}", headers=company_a).json()["status"] == "invited"


def test_an_applicant_is_never_started_twice(client, company_a, session, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    fake_llm.finish("Waiting.")
    candidate_id = make_candidate(client, company_a, job_id)

    again = client.post(f"/candidates/{candidate_id}/start", headers=company_a).json()
    assert again == {"steps": 0, "summary": "Onboarding already started."}
    agent_service.start_waiting(session.get_bind(), company_id(client, company_a), job_id)
    assert len(fake_llm.chat_calls) == 1


def test_a_failed_agent_run_is_shown_to_hr_instead_of_crashing(client, company_a, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    candidate_id = make_candidate(client, company_a, job_id)  # the fake model has no reply queued, so the run fails

    titles = [e["title"] for e in client.get(f"/candidates/{candidate_id}/events", headers=company_a).json()]
    assert "The agent could not run" in titles


def test_start_agent_starts_the_waiting_applicants_without_redrafting_the_plan(client, company_a, fake_llm, monkeypatch):
    job_id = job_with_plan(client, company_a, fake_llm)
    a = make_candidate(client, company_a, job_id)
    b = make_candidate(client, company_a, job_id, full_name_en="Sara Ali", email="sara@gmail.com")
    monkeypatch.setattr(agent_service, "AUTO_START", True)
    fake_llm.finish("Waiting.")
    fake_llm.finish("Waiting.")
    plan_calls = len(fake_llm.text_calls)

    assert client.post(f"/jobs/{job_id}/start", headers=company_a).status_code == 202

    assert len(fake_llm.chat_calls) == 2 and len(fake_llm.text_calls) == plan_calls
    assert {client.get(f"/candidates/{i}", headers=company_a).json()["status"] for i in (a, b)} == {"invited"}
    assert client.post(f"/jobs/{job_id}/start", headers=company_a).status_code == 202
    assert len(fake_llm.chat_calls) == 2  # nobody is waiting any more, so nothing runs twice


def test_start_agent_needs_a_plan_and_stays_inside_the_company(client, company_a, company_b, fake_llm, monkeypatch):
    job_id = make_job(client, company_a)
    assert client.post(f"/jobs/{job_id}/start", headers=company_a).status_code == 400
    approve_plan(client, company_a, job_id, fake_llm)
    assert client.post(f"/jobs/{job_id}/start", headers=company_b).status_code == 404
