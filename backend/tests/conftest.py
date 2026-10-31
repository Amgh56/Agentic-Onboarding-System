import os

from cryptography.fernet import Fernet

os.environ.update(
    DATABASE_URL="sqlite://",
    JWT_SECRET="test-secret-that-is-long-enough-for-hs256",
    ENCRYPTION_KEY=Fernet.generate_key().decode(),
    APP_BASE_URL="http://testserver",
    LLM_PROVIDER="openai",
    MODEL_STRONG="test-strong",
    MODEL_FAST="test-fast",
    OPENAI_API_KEY="test-openai-key",
)

import copy
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core import llm
from app.core.database import get_session
from app.features.documents import storage
from app.main import app


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOADS_DIR", tmp_path)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine):
    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


def signup(client, company="Acme", email="hr@acme.com", with_email=True):
    response = client.post(
        "/auth/signup",
        json={"company_name": company, "full_name": "HR User", "email": email, "password": "secret"},
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    if with_email:
        settings = {"provider": "mock", "email_address": f"onboarding@{email.split('@')[1]}"}
        client.put("/email-settings", json=settings, headers=headers)
    return headers


@pytest.fixture
def company_a(client):
    return signup(client, "Company A", "a@a.com")


@pytest.fixture
def company_b(client):
    return signup(client, "Company B", "b@b.com")


class FakeLLM:
    """Stands in for the model. Queue replies with say(), act() and finish()."""

    def __init__(self):
        self.text_replies = []
        self.chat_replies = []
        self.text_calls = []
        self.chat_calls = []

    def say(self, text):
        self.text_replies.append(text)

    def act(self, *calls):
        tool_calls = [
            {
                "id": f"call-{len(self.chat_replies)}-{i}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
            for i, (name, args) in enumerate(calls)
        ]
        self.chat_replies.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

    def finish(self, text):
        self.chat_replies.append({"role": "assistant", "content": text})

    def text(self, model, prompt, system, file):
        self.text_calls.append({"model": model, "prompt": prompt, "system": system, "file": file})
        return self.text_replies.pop(0)

    def chat(self, model, messages, tools):
        self.chat_calls.append({"model": model, "messages": copy.deepcopy(messages), "tools": tools})
        return self.chat_replies.pop(0)


@pytest.fixture
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(llm, "_openai", fake.text)
    monkeypatch.setattr(llm, "_openai_chat", fake.chat)
    return fake


@pytest.fixture(autouse=True)
def verifier_off(monkeypatch):
    """Most tests script the model call by call, so the verifier is off unless a test turns it on."""
    from app.features.agent import verifier
    monkeypatch.setattr(verifier, "ENABLED", False)


@pytest.fixture(autouse=True)
def auto_start_off(monkeypatch):
    """Adding applicants starts the agent on its own. Most tests start it by hand, so it is off unless turned on."""
    from app.features.agent import service as agent_service
    monkeypatch.setattr(agent_service, "AUTO_START", False)
