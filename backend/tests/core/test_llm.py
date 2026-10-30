from app.core import llm


def test_fast_and_strong_pick_the_model_from_env(monkeypatch):
    used = []
    monkeypatch.setattr(llm, "_openai", lambda model, prompt, system: used.append(model) or "ok")

    assert llm.complete("hi", model="fast") == "ok"
    llm.complete("hi", model="strong")
    assert used == ["test-fast", "test-strong"]


def test_unknown_model_size_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        llm.complete("hi", model="huge")
