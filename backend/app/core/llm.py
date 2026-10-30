from openai import OpenAI

from app.core.config import settings


def complete(prompt: str, model: str = "fast", system: str | None = None) -> str:
    """The only place the app calls a model. model is "fast" or "strong"."""
    if model not in ("fast", "strong"):
        raise ValueError("model must be 'fast' or 'strong'")
    name = settings.model_strong if model == "strong" else settings.model_fast
    return _openai(name, prompt, system)


def _openai(model: str, prompt: str, system: str | None) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
