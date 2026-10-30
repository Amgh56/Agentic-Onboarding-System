def make_job(client, headers):
    return client.post("/jobs", json={"title": "Driver"}, headers=headers).json()["id"]


def upload(client, headers, job_id, name="contract.pdf", content=b"hello"):
    return client.post(
        f"/jobs/{job_id}/documents", files={"file": (name, content, "application/pdf")}, headers=headers
    )


def test_upload_list_download_and_delete(client, company_a):
    job_id = make_job(client, company_a)
    created = upload(client, company_a, job_id)
    assert created.status_code == 201
    assert created.json()["filename"] == "contract.pdf"

    listed = client.get(f"/jobs/{job_id}/documents", headers=company_a).json()
    assert len(listed) == 1

    download = client.get(f"/documents/{listed[0]['id']}/download", headers=company_a)
    assert download.content == b"hello"

    assert client.delete(f"/documents/{listed[0]['id']}", headers=company_a).status_code == 204
    assert client.get(f"/jobs/{job_id}/documents", headers=company_a).json() == []


def test_other_company_cannot_touch_documents(client, company_a, company_b):
    job_id = make_job(client, company_a)
    document_id = upload(client, company_a, job_id).json()["id"]

    assert upload(client, company_b, job_id).status_code == 404
    assert client.get(f"/jobs/{job_id}/documents", headers=company_b).status_code == 404
    assert client.get(f"/documents/{document_id}/download", headers=company_b).status_code == 404
    assert client.delete(f"/documents/{document_id}", headers=company_b).status_code == 404
