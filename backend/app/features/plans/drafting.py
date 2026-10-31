from fastapi import HTTPException
from pydantic import ValidationError

from app.core import llm
from app.features.plans.schema import Draft

SYSTEM = """You turn a company's onboarding procedure into a short, ordered plan for an onboarding agent.
Follow the procedure. Do not add steps it does not ask for, and do not drop steps it asks for.
Keep the steps few. Each step has a title of two to four words in sentence case, like "Create work email",
and one or two short sentences of details, like "Issue the company address first. Every other account uses it."
Use the department and system names given, written for people (for example "Work email", "GitHub", "IT desk").
Telling departments is one step, titled "Tell departments": name them in the order the procedure gives.
Sending something and collecting it back are two steps, like "Send documents" and "Collect documents".
A sending step is done once it is sent: do not mention what the person does with it in that step's details.
A condition stays inside its step: "if the role is unclear, ask HR" belongs to the accounts step.

Reply with JSON only, in this shape:
{"steps": [{"title": "short title", "details": "what to do and when it is done"}]}"""


def draft(job, departments, systems) -> list[dict]:
    department_lines = "\n".join(f"- {d.name}: {d.handles}" for d in departments) or "- none listed"
    system_lines = "\n".join(
        f"- {s.key} ({s.name}, {s.kind}): {s.description} Groups: {', '.join(g.name for g in s.groups) or 'none'}"
        for s in systems
    )
    prompt = f"""Job title: {job.title}
Job description:
{job.description or "(none)"}

Onboarding procedure:
{job.procedure}

Departments:
{department_lines}

Systems:
{system_lines}"""

    try:
        result = Draft(**llm.complete_json(prompt, model="strong", system=SYSTEM))
    except (ValueError, TypeError, ValidationError):
        raise HTTPException(502, "The model returned a plan that could not be read. Try again.")
    return [
        {"id": f"step-{number}", "title": step.title, "details": step.details}
        for number, step in enumerate(result.steps, start=1)
    ]
