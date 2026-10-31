import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")

UPLOADS_DIR = APP_DIR.parent / "uploads"

REQUIRED = [
    "DATABASE_URL",
    "JWT_SECRET",
    "ENCRYPTION_KEY",
    "LLM_PROVIDER",
    "MODEL_STRONG",
    "MODEL_FAST",
    "OPENAI_API_KEY",
    "APP_BASE_URL",
]


@dataclass
class Settings:
    database_url: str
    jwt_secret: str
    encryption_key: str
    llm_provider: str
    model_strong: str
    model_fast: str
    openai_api_key: str
    app_base_url: str


def load_settings(env: Mapping[str, str]) -> Settings:
    missing = [name for name in REQUIRED if not env.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing values in .env: {', '.join(missing)}. Copy .env.example and fill them in."
        )
    if env["LLM_PROVIDER"] != "openai":
        raise RuntimeError("LLM_PROVIDER must be 'openai'.")
    return Settings(
        database_url=env["DATABASE_URL"],
        jwt_secret=env["JWT_SECRET"],
        encryption_key=env["ENCRYPTION_KEY"],
        llm_provider=env["LLM_PROVIDER"],
        model_strong=env["MODEL_STRONG"],
        model_fast=env["MODEL_FAST"],
        openai_api_key=env["OPENAI_API_KEY"],
        app_base_url=env["APP_BASE_URL"].rstrip("/"),
    )


settings = load_settings(os.environ)

DATABASE_URL = settings.database_url
JWT_SECRET = settings.jwt_secret
