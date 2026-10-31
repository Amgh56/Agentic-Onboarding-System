from sqlmodel import select

from app.features.notifications import mail_client
from app.features.notifications.model import EmailSettings
from tests.conftest import signup

GMAIL = {"provider": "smtp", "email_address": "hr@gmail.com", "password": "abcd efgh ijkl mnop"}


def test_settings_are_saved_and_the_password_is_never_returned(client, session):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    assert client.get("/email-settings", headers=headers).status_code == 404

    saved = client.put("/email-settings", json={**GMAIL, "allowed_recipients": ["Omar@Gmail.com", "@gulf.com"]}, headers=headers)
    assert saved.status_code == 200
    body = saved.json()
    assert "password" not in body and "password_encrypted" not in body
    assert body["has_password"] is True
    assert body["smtp_host"] == "smtp.gmail.com" and body["imap_port"] == 993
    assert body["allowed_recipients"] == ["omar@gmail.com", "@gulf.com"]

    stored = session.exec(select(EmailSettings)).all()[-1]
    assert stored.password_encrypted and "abcd" not in stored.password_encrypted


def test_saving_again_without_a_password_keeps_the_old_one(client, session):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    client.put("/email-settings", json=GMAIL, headers=headers)
    before = session.exec(select(EmailSettings)).all()[-1].password_encrypted

    updated = client.put("/email-settings", json={"provider": "smtp", "email_address": "hr@gmail.com", "smtp_port": 465}, headers=headers)
    assert updated.json()["smtp_port"] == 465
    session.expire_all()
    assert session.exec(select(EmailSettings)).all()[-1].password_encrypted == before


def test_real_email_needs_a_password(client):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    response = client.put("/email-settings", json={"provider": "smtp", "email_address": "hr@gmail.com"}, headers=headers)
    assert response.status_code == 400


def test_each_company_has_its_own_settings(client, company_a):
    other = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    assert client.get("/email-settings", headers=company_a).json()["email_address"] == "onboarding@a.com"
    assert client.get("/email-settings", headers=other).status_code == 404


def test_connection_in_test_mode_needs_no_network(client, company_a):
    result = client.post("/email-settings/test", headers=company_a).json()
    assert result["ok"] is True


def test_connection_uses_the_decrypted_password(client, monkeypatch):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    client.put("/email-settings", json=GMAIL, headers=headers)
    sent, logins = [], []
    monkeypatch.setattr(mail_client, "send", lambda settings, password, to, subject, body, files: sent.append((password, to)))
    monkeypatch.setattr(mail_client, "check_login", lambda settings, password: logins.append(password))

    result = client.post("/email-settings/test", headers=headers).json()
    assert result["ok"] is True
    assert sent == [("abcd efgh ijkl mnop", "hr@gmail.com")]
    assert logins == ["abcd efgh ijkl mnop"]


def test_connection_failure_is_reported_not_crashed(client, monkeypatch):
    headers = signup(client, "Gulf Co", "hr@gulf.com", with_email=False)
    client.put("/email-settings", json=GMAIL, headers=headers)

    def refuse(*args):
        raise OSError("Username and Password not accepted")

    monkeypatch.setattr(mail_client, "send", refuse)
    monkeypatch.setattr(mail_client, "check_login", refuse)
    result = client.post("/email-settings/test", headers=headers).json()
    assert result["ok"] is False
    assert "not accepted" in result["smtp"]
