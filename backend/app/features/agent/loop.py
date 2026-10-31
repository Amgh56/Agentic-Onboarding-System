import json

from sqlmodel import Session

from app.core import llm
from app.core.events import log_event
from app.features.agent import prompts, tools
from app.features.approvals import service as approvals_service

MAX_STEPS = 25


def run_loop(session: Session, company_id: int, candidate, event: str) -> dict:
    """A plain loop: the model picks tools, we run them and hand back the results,
    until it stops calling tools or reaches the step limit."""
    messages = [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {"role": "user", "content": prompts.build_context(session, company_id, candidate, event)},
    ]

    for step in range(1, MAX_STEPS + 1):
        reply = llm.chat(messages, tools.SCHEMAS, model="strong")
        messages.append(reply)
        calls = reply.get("tool_calls")
        if not calls:
            summary = reply.get("content") or "Done."
            break
        for call in calls:
            try:
                args = json.loads(call["function"]["arguments"])
            except ValueError:
                args = None
            result = tools.execute(session, company_id, candidate, call["function"]["name"], args)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
    else:
        summary = "Stopped after reaching the step limit."
        approvals_service.create_approval(
            session, company_id, candidate.id, "escalation", "", "The agent reached its step limit and stopped."
        )

    log_event(session, company_id, candidate.id, "agent", "Run finished", summary)
    session.commit()
    return {"steps": step, "summary": summary}
