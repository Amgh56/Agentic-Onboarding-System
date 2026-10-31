import pytest

from app.core import llm


def test_fast_and_strong_pick_the_model_from_env(monkeypatch):
    used = []
    monkeypatch.setattr(llm, "_openai", lambda model, prompt, system, file: used.append(model) or "ok")

    assert llm.complete("hi", model="fast") == "ok"
    llm.complete("hi", model="strong")
    assert used == ["test-fast", "test-strong"]


def test_unknown_model_size_is_rejected():
    with pytest.raises(ValueError):
        llm.complete("hi", model="huge")


def test_chat_uses_the_model_from_env(monkeypatch):
    used = []
    monkeypatch.setattr(
        llm, "_openai_chat", lambda model, messages, tools: used.append(model) or {"role": "assistant", "content": "hi"}
    )
    reply = llm.chat([{"role": "user", "content": "x"}], [], model="strong")
    assert reply["content"] == "hi"
    assert used == ["test-strong"]


def test_complete_json_reads_json_inside_code_fences(monkeypatch):
    monkeypatch.setattr(llm, "_openai", lambda model, prompt, system, file: '```json\n{"a": 1}\n```')
    assert llm.complete_json("x") == {"a": 1}


def test_complete_json_rejects_text_that_is_not_json(monkeypatch):
    monkeypatch.setattr(llm, "_openai", lambda model, prompt, system, file: "sorry, no")
    with pytest.raises(ValueError):
        llm.complete_json("x")
