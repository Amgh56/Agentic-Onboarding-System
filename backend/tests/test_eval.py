import json

from eval import cases, run
from eval.world import World

DEV = ["business_valid", "developer_valid", "expired_document", "missing_past_deadline"]


def only(name):
    return next(c for c in cases.ALL if c.name == name)


DEMO = ["demo_yousef", "demo_abdulaziz", "demo_omar"]


def test_the_five_cases_exist_and_only_the_last_is_held_out():
    assert [c.name for c in cases.ALL if c.split == "dev"] == DEV
    assert [c.name for c in cases.ALL if c.split == "held_out"] == ["unknown_role_second_company"]


def test_the_demo_cases_are_a_separate_group_that_the_default_run_skips(tmp_path, fake_llm):
    assert [c.name for c in cases.ALL if c.split == "demo"] == DEMO
    normal = run.run_all("rules", runs=1, out_dir=tmp_path)
    assert not {c["name"] for c in normal["cases"]} & set(DEMO)


def world(**changes):
    done = {
        "candidate_status": "completed", "steps_done": 7, "steps_total": 7, "documents": ["valid"] * 3,
        "accounts": [{"system": s, "address": "a@demo.com"} for s in ("work_email", "slack", "teams", "github")],
        "tickets": ["Developer laptop"], "approvals": [],
    }
    return World(**{**done, **changes})


def test_yousef_passes_with_developer_accounts_and_a_developer_laptop():
    assert run.evaluate(only("demo_yousef"), world())["passed"]
    wrong = run.evaluate(only("demo_yousef"), world(tickets=["Standard laptop"]))
    assert wrong["passed"] is False and wrong["wrong_actions"] == 1


def test_abdulaziz_must_not_get_accounts_before_hr_answers():
    before = World(documents=["valid"] * 3, accounts=[{"system": "work_email"}], approvals=[{"kind": "escalation"}])
    after = dict(
        accounts=[{"system": s} for s in ("work_email", "erp", "slack", "teams")], tickets=["Standard laptop"],
        steps_done=7, steps_total=7, candidate_status="completed",
    )
    assert run.evaluate(only("demo_abdulaziz"), world(**after, checkpoint=before))["passed"]

    early = World(documents=["valid"] * 3, accounts=[{"system": "work_email"}, {"system": "erp"}], approvals=[{"kind": "escalation"}])
    guessed = run.evaluate(only("demo_abdulaziz"), world(**after, checkpoint=early))
    assert guessed["passed"] is False and guessed["wrong_actions"] == 1


def test_omar_gets_one_chase_email_naming_all_three_problems_and_no_accounts_yet():
    request = {"to_candidate": True, "department": None, "subject": "Documents needed", "body": "Please send them."}
    chase = {
        "to_candidate": True, "department": None, "subject": "Still needed",
        "body": "Missing: Cybersecurity Policy. The NDA is not signed. The Employment Contract is in another name.",
    }
    round_one = World(emails=[request, chase])
    final = dict(
        accounts=[{"system": s} for s in ("work_email", "erp", "slack", "teams")], tickets=["Standard laptop"],
        steps_done=7, steps_total=7, candidate_status="completed",
    )
    assert run.evaluate(only("demo_omar"), world(**final, checkpoint=round_one))["passed"]

    two_chases = World(emails=[request, chase, {**chase, "subject": "Reminder"}])
    assert run.evaluate(only("demo_omar"), world(**final, checkpoint=two_chases))["passed"] is False
    early_account = World(emails=[request, chase], accounts=[{"system": "work_email"}])
    assert run.evaluate(only("demo_omar"), world(**final, checkpoint=early_account))["wrong_actions"] == 1


def test_the_rules_baseline_plays_the_demo_cases_through_the_reply_script_without_a_model(tmp_path, fake_llm):
    results = run.run_all("rules", runs=1, names=DEMO, out_dir=tmp_path)

    assert [c["name"] for c in results["cases"]] == DEMO
    assert all("error" not in r for c in results["cases"] for r in c["runs"])
    assert results["summary"]["model_calls"] == 0
    assert fake_llm.chat_calls == [] and fake_llm.text_calls == []


def test_rules_baseline_passes_its_home_cases_without_calling_a_model(fake_llm):
    for name in DEV:
        result = run.run_case(only(name), "rules")
        assert result["passed"], (name, [c for c in result["checks"] if not c["ok"]])
        assert result["wrong_actions"] == 0
        assert result["tokens"]["calls"] == 0
    assert fake_llm.text_calls == [] and fake_llm.chat_calls == []


def test_rules_baseline_cannot_follow_another_companys_procedure(fake_llm):
    result = run.run_case(only("unknown_role_second_company"), "rules")
    assert result["passed"] is False
    assert result["escalated"] is False
    missed = {c["label"] for c in result["checks"] if not c["ok"]}
    assert "asked for the Iqama, as this company's procedure says" in missed
    assert "used the upload link, as this company's procedure says" in missed


def test_checks_count_wrong_actions_and_escalations():
    case = only("developer_valid")
    world = World(
        candidate_status="completed", accounts=[{"system": "work_email"}, {"system": "github"}, {"system": "erp"}],
        tickets=["Laptop"], emails=[], approvals=[{"kind": "escalation"}], documents=[], tool_calls=7,
    )
    outcome = run.evaluate(case, world)
    assert outcome["passed"] is False
    assert outcome["wrong_actions"] == 1  # the ERP account a developer must not get
    assert outcome["escalated"] is True


def test_run_all_saves_a_results_file_with_pass_counts(tmp_path, fake_llm):
    results = run.run_all("rules", runs=2, names=["business_valid", "developer_valid"], out_dir=tmp_path)
    saved = json.loads(open(results["file"]).read())

    assert saved["variant"] == "rules"
    assert [c["name"] for c in saved["cases"]] == ["business_valid", "developer_valid"]
    assert saved["cases"][0]["passed_runs"] == 2 and saved["cases"][0]["runs_total"] == 2
    assert saved["summary"]["runs_passed"] == 4 and saved["summary"]["runs_total"] == 4


def test_held_out_case_runs_only_with_final(tmp_path, fake_llm):
    normal = run.run_all("rules", runs=1, out_dir=tmp_path)
    assert "unknown_role_second_company" not in [c["name"] for c in normal["cases"]]

    final = run.run_all("rules", runs=1, final=True, out_dir=tmp_path)
    assert "unknown_role_second_company" in [c["name"] for c in final["cases"]]


def test_a_changed_prompt_is_recorded_in_the_results(tmp_path, fake_llm):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("You are a test prompt.")
    from app.features.agent import prompts
    original = prompts.SYSTEM_PROMPT
    try:
        results = run.run_all("rules", runs=1, names=["business_valid"], out_dir=tmp_path, prompt_file=str(prompt))
        assert results["prompt_file"] == str(prompt)
        assert results["prompt_sha"] != run.prompt_sha(original)
    finally:
        prompts.SYSTEM_PROMPT = original
