def test_signup_login_and_me(client):
    signup = client.post(
        "/auth/signup",
        json={"company_name": "Acme", "full_name": "Mona", "email": "m@acme.com", "password": "pw"},
    )
    assert signup.status_code == 201

    login = client.post("/auth/login", json={"email": "m@acme.com", "password": "pw"})
    assert login.status_code == 200

    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = client.get("/auth/me", headers=headers)
    assert me.json()["full_name"] == "Mona"
    assert client.get("/companies/me", headers=headers).json()["name"] == "Acme"


def test_wrong_password_is_rejected(client):
    client.post(
        "/auth/signup",
        json={"company_name": "Acme", "full_name": "Mona", "email": "m@acme.com", "password": "pw"},
    )
    response = client.post("/auth/login", json={"email": "m@acme.com", "password": "nope"})
    assert response.status_code == 401


def test_me_needs_a_token(client):
    assert client.get("/auth/me").status_code in (401, 403)
