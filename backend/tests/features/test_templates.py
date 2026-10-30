STEPS = [
    {"id": "info", "type": "info", "title": "Your details"},
    {"id": "id", "type": "document", "title": "National ID", "depends_on": ["info"]},
]


def test_create_and_read_template(client, company_a):
    created = client.post("/templates", json={"name": "Standard", "steps": STEPS}, headers=company_a)
    assert created.status_code == 201
    assert created.json()["steps"][1]["autonomy"] == "auto"

    template_id = created.json()["id"]
    assert client.get(f"/templates/{template_id}", headers=company_a).status_code == 200
    assert len(client.get("/templates", headers=company_a).json()) == 1


def test_unknown_step_type_is_rejected(client, company_a):
    bad = [{"id": "x", "type": "teleport", "title": "Nope"}]
    response = client.post("/templates", json={"name": "Bad", "steps": bad}, headers=company_a)
    assert response.status_code == 422


def test_other_company_cannot_see_template(client, company_a, company_b):
    template_id = client.post("/templates", json={"name": "T", "steps": STEPS}, headers=company_a).json()["id"]
    assert client.get(f"/templates/{template_id}", headers=company_b).status_code == 404
    assert client.get("/templates", headers=company_b).json() == []
