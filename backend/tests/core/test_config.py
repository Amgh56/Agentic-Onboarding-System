import pytest

from app.core.config import load_settings

VALID = {
    "DATABASE_URL": "sqlite://",
    "JWT_SECRET": "secret",
    "ENCRYPTION_KEY": "key",
    "LLM_PROVIDER": "openai",
    "MODEL_STRONG": "strong-model",
    "MODEL_FAST": "fast-model",
    "OPENAI_API_KEY": "sk-test",
}


def test_valid_env_loads():
    settings = load_settings(VALID)
    assert settings.model_strong == "strong-model"
    assert settings.model_fast == "fast-model"
    assert settings.openai_api_key == "sk-test"


def test_missing_values_are_all_named_in_the_error():
    env = {**VALID, "JWT_SECRET": "", "OPENAI_API_KEY": ""}
    del env["MODEL_FAST"]
    with pytest.raises(RuntimeError) as error:
        load_settings(env)
    message = str(error.value)
    assert "JWT_SECRET" in message
    assert "OPENAI_API_KEY" in message
    assert "MODEL_FAST" in message


def test_unknown_provider_is_rejected():
    with pytest.raises(RuntimeError, match="LLM_PROVIDER"):
        load_settings({**VALID, "LLM_PROVIDER": "other"})
