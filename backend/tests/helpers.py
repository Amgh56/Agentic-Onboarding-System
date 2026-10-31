PLAN_JSON = (
    '{"steps": ['
    '{"title": "Collect documents", "details": "Ask for the national ID."},'
    '{"title": "Create accounts", "details": "Work email first, then the rest by role."}'
    "]}"
)

APPLICANT = {
    "full_name_en": "Omar Abdullah",
    "full_name_ar": "عمر عبدالله",
    "phone": "0500000000",
    "email": "omar@gmail.com",
    "date_of_birth": "1995-04-12",
}


def company_id(client, headers):
    return client.get("/companies/me", headers=headers).json()["id"]


def make_job(client, headers, procedure="Collect the national ID, then create accounts by role."):
    body = {"title": "Backend Developer", "description": "Builds our APIs.", "procedure": procedure}
    return client.post("/jobs", json=body, headers=headers).json()["id"]


def make_candidate(client, headers, job_id, **changes):
    body = {**APPLICANT, **changes}
    return client.post(f"/jobs/{job_id}/candidates", json=body, headers=headers).json()["id"]


def approve_plan(client, headers, job_id, fake_llm):
    fake_llm.say(PLAN_JSON)
    client.post(f"/jobs/{job_id}/plan/draft", headers=headers)
    client.post(f"/jobs/{job_id}/plan/approve", headers=headers)


def ready_candidate(client, headers, fake_llm, **changes):
    """A candidate whose job has an approved plan, so the agent can run."""
    job_id = make_job(client, headers)
    approve_plan(client, headers, job_id, fake_llm)
    return make_candidate(client, headers, job_id, **changes)


def department_id(client, headers, name):
    """Every company starts with IT, Payroll, Finance and HR."""
    return next(d["id"] for d in client.get("/departments", headers=headers).json() if d["name"] == name)
