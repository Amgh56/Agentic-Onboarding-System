import base64
import json

from openai import OpenAI

from app.core.config import settings

# Running totals, read by the evaluation to report token cost.
usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


def _model_name(model: str) -> str:
    if model not in ("fast", "strong"):
        raise ValueError("model must be 'fast' or 'strong'")
    return settings.model_strong if model == "strong" else settings.model_fast


def complete(
    prompt: str, model: str = "fast", system: str | None = None, file: tuple[bytes, str, str] | None = None
) -> str:
    """The only place the app calls a model for text. file is (bytes, content type, filename): an image or a PDF."""
    return _openai(_model_name(model), prompt, system, file)


def complete_json(
    prompt: str, model: str = "fast", system: str | None = None, file: tuple[bytes, str, str] | None = None
) -> dict:
    """Like complete, but the reply must be JSON. Raises ValueError if it is not."""
    text = complete(prompt, model, system, file).strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def chat(messages: list[dict], tools: list[dict], model: str = "strong") -> dict:
    """One assistant turn with tools. Returns the assistant message, ready to append to messages."""
    return _openai_chat(_model_name(model), messages, tools)


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def _count(response) -> None:
    usage["calls"] += 1
    if response.usage:
        usage["input_tokens"] += response.usage.prompt_tokens
        usage["output_tokens"] += response.usage.completion_tokens


def _openai(model: str, prompt: str, system: str | None, file: tuple[bytes, str, str] | None) -> str:
    content: str | list = prompt
    if file:
        data, content_type, filename = file
        url = f"data:{content_type};base64,{base64.b64encode(data).decode()}"
        part = (
            {"type": "image_url", "image_url": {"url": url}}
            if content_type.startswith("image/")
            else {"type": "file", "file": {"filename": filename, "file_data": url}}
        )
        content = [{"type": "text", "text": prompt}, part]

    messages = [{"role": "user", "content": content}]
    if system:
        messages.insert(0, {"role": "system", "content": system})
    response = _client().chat.completions.create(model=model, messages=messages)
    _count(response)
    return response.choices[0].message.content


def _openai_chat(model: str, messages: list[dict], tools: list[dict]) -> dict:
    response = _client().chat.completions.create(model=model, messages=messages, tools=tools)
    _count(response)
    message = response.choices[0].message
    reply = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        reply["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in message.tool_calls
        ]
    return reply
