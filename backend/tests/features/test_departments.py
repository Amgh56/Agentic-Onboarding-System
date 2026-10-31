SALES = {"name": "Payroll", "email": "payroll@acme.com", "handles": "Salaries and bank details"}


def test_every_company_starts_with_the_same_four_departments(client, company_a, company_b):
    for headers, domain in ((company_a, "companya.example"), (company_b, "companyb.example")):
        departments = client.get("/departments", headers=headers).json()
        assert [d["name"] for d in departments] == ["IT", "Payroll", "Finance", "HR"]
        assert [d["email"] for d in departments] == [f"it@{domain}", f"payroll@{domain}", f"finance@{domain}", f"hr@{domain}"]
        assert all(d["handles"] for d in departments)


def test_department_crud(client, company_a):
    created = client.post("/departments", json=SALES, headers=company_a)
    assert created.status_code == 201

    department_id = created.json()["id"]
    assert len(client.get("/departments", headers=company_a).json()) == 5

    updated = client.put(f"/departments/{department_id}", json={**SALES, "name": "Legal"}, headers=company_a)
    assert updated.json()["name"] == "Legal"

    assert client.delete(f"/departments/{department_id}", headers=company_a).status_code == 204
    assert len(client.get("/departments", headers=company_a).json()) == 4


def test_department_needs_name_email_and_description(client, company_a):
    response = client.post("/departments", json={**SALES, "handles": ""}, headers=company_a)
    assert response.status_code == 422


def test_other_company_cannot_see_or_change_departments(client, company_a, company_b):
    department_id = client.post("/departments", json=SALES, headers=company_a).json()["id"]

    assert department_id not in [d["id"] for d in client.get("/departments", headers=company_b).json()]
    assert client.put(f"/departments/{department_id}", json=SALES, headers=company_b).status_code == 404
    assert client.delete(f"/departments/{department_id}", headers=company_b).status_code == 404
