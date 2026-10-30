import os

os.environ.update(
    DATABASE_URL="sqlite://",
    JWT_SECRET="test-secret",
    ENCRYPTION_KEY="test-key",
    LLM_PROVIDER="openai",
    MODEL_STRONG="test-strong",
    MODEL_FAST="test-fast",
    OPENAI_API_KEY="test-openai-key",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.features.documents import storage
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOADS_DIR", tmp_path)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def signup(client, company="Acme", email="hr@acme.com"):
    response = client.post(
        "/auth/signup",
        json={"company_name": company, "full_name": "HR User", "email": email, "password": "secret"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def company_a(client):
    return signup(client, "Company A", "a@a.com")


@pytest.fixture
def company_b(client):
    return signup(client, "Company B", "b@b.com")
