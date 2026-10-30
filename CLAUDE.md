# Onboarding Agent

Multi-company AI onboarding agent for a hackathon. Read `docs/spec.md` before doing any work.

## Stack
- Backend: Python, FastAPI, SQLModel, SQLite. Model calls go through ONE wrapper (`app/core/llm.py`), provider and model names come from `.env`.
- Frontend (built last): React + TypeScript.
- No agent framework. The agent is a plain loop.

## Structure
Feature-based. Each feature folder has `controller.py`, `service.py`, `model.py`, `schema.py`.
- Features talk to each other only through `service.py`.
- `core/` never imports from `features/`.
- Every table has `company_id`. Every query filters by the logged-in user's company. Another company's data returns 404.

## Rules
- Simple, readable code. No over-engineering, no extra checks or features I did not ask for.
- Do only the milestone I name. Do not build ahead.
- Write the tests for a milestone first, then the code.
- Secrets only in `.env`. Never print or commit keys. `.env.example` has empty values.
- Fail at startup with a clear message if a required `.env` value is missing.

## Commands
- Run API: `uvicorn app.main:app --reload` (from `backend/`)
- Tests: `pytest`
- Evaluation: `python -m eval.run`

## Done means
Tests pass, evaluation run saved, short summary of what changed. Commit after each milestone.
