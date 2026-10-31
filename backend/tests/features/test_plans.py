from tests.helpers import PLAN_JSON, make_job


def test_draft_plan_from_the_procedure(client, company_a, fake_llm):
    job_id = make_job(client, company_a, procedure="Ask for the Iqama. IT prepares a laptop.")
    fake_llm.say(PLAN_JSON)

    drafted = client.post(f"/jobs/{job_id}/plan/draft", headers=company_a)
    assert drafted.status_code == 201
    plan = drafted.json()
    assert [s["id"] for s in plan["steps"]] == ["step-1", "step-2"]
    assert plan["steps"][0]["title"] == "Collect documents"
    assert plan["approved"] is True

    prompt = fake_llm.text_calls[0]["prompt"]
    assert "Ask for the Iqama" in prompt
    assert "IT:" in prompt and "Payroll:" in prompt and "backend-team" in prompt
    assert [d["name"] for d in plan["departments"]] == ["IT", "Payroll", "Finance", "HR"]
    assert fake_llm.text_calls[0]["model"] == "test-strong"
    system = fake_llm.text_calls[0]["system"]
    assert "two to four words" in system and "Telling departments is one step" in system
    assert "A condition stays inside its step" in system and "collecting it back are two steps" in system
    assert "A sending step is done once it is sent" in " ".join(system.split())
    assert client.get(f"/jobs/{job_id}/plan", headers=company_a).json() == plan


def test_draft_needs_a_procedure(client, company_a, fake_llm):
    job_id = make_job(client, company_a, procedure="")
    assert client.post(f"/jobs/{job_id}/plan/draft", headers=company_a).status_code == 400
    assert fake_llm.text_calls == []


def test_redrafting_replaces_the_plan_in_use(client, company_a, fake_llm):
    job_id = make_job(client, company_a)
    fake_llm.say(PLAN_JSON)
    first = client.post(f"/jobs/{job_id}/plan/draft", headers=company_a).json()

    fake_llm.say(PLAN_JSON.replace("Collect documents", "Ask for the Iqama"))
    second = client.post(f"/jobs/{job_id}/plan/draft", headers=company_a).json()
    assert second["id"] == first["id"] and second["approved"] is True
    assert second["steps"][0]["title"] == "Ask for the Iqama"


def test_unreadable_model_reply_is_rejected(client, company_a, fake_llm):
    job_id = make_job(client, company_a)
    fake_llm.say("Here is your plan: step one...")
    assert client.post(f"/jobs/{job_id}/plan/draft", headers=company_a).status_code == 502
    assert client.get(f"/jobs/{job_id}/plan", headers=company_a).status_code == 404


def test_other_company_cannot_draft_read_or_approve(client, company_a, company_b, fake_llm):
    job_id = make_job(client, company_a)
    fake_llm.say(PLAN_JSON)
    client.post(f"/jobs/{job_id}/plan/draft", headers=company_a)

    assert client.post(f"/jobs/{job_id}/plan/draft", headers=company_b).status_code == 404
    assert client.get(f"/jobs/{job_id}/plan", headers=company_b).status_code == 404
    assert client.post(f"/jobs/{job_id}/plan/approve", headers=company_b).status_code == 404
