# Agentic Onboarding System

A multi-company platform where HR writes an onboarding procedure in plain text and an AI agent runs each new hire's onboarding.

## How it works

1. **Plan.** HR writes the procedure. One model call turns it into a numbered plan, and HR approves it.
2. **Agent.** The agent follows the plan one step at a time by calling 11 tools (request documents, read inbox, validate document, send email, create account, create ticket, escalate, and so on). It is a plain tool-calling loop with no framework.
3. **Verifier.** A separate model call checks the agent's work:
   - each document is read twice, by two different models, and the results are compared by code;
   - risky actions (accounts, emails the agent writes) are reviewed before they run;
   - each plan step is checked against what actually happened before it counts as done.
4. **Code rules.** Some rules are enforced in code, not left to a model. For example, no account is created until every document is valid, and steps must go in order.
5. **HR.** When a case is unclear or disputed, the agent escalates. HR answers on the applicant's page, and the answer wakes the agent.

Every action is saved with a one-sentence reason, so HR can read what the agent did and why.

## Technologies

- **Backend:** Python, FastAPI, SQLModel, SQLite
- **AI:** OpenAI (`gpt-5.4` for the agent and verifier, `gpt-5.4-mini` for the first document reading), through one wrapper in `backend/app/core/llm.py`
- **Frontend:** Next.js, React, TypeScript (English and Arabic)
- **Tests:** pytest, with a fake model so tests run offline

## Setup

You need Python 3.11+, Node.js 20+ and an OpenAI API key.

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp app/.env.example app/.env
```

Fill in `backend/app/.env`:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `sqlite:///./onboarding.db` |
| `JWT_SECRET` | any long random string |
| `ENCRYPTION_KEY` | a Fernet key (see below) |
| `LLM_PROVIDER` | `openai` |
| `MODEL_STRONG` | `gpt-5.4` |
| `MODEL_FAST` | `gpt-5.4-mini` |
| `OPENAI_API_KEY` | your key |
| `APP_BASE_URL` | `http://localhost:8000` |

Generate an encryption key:

```bash
.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The server refuses to start if any value is missing. Secrets live only in `backend/app/.env`, which is not committed.

### Frontend

```bash
cd frontend
npm install
```

## Run

Start the API (from `backend/`):

```bash
.venv/bin/uvicorn app.main:app --port 8000
```

Start the frontend (from `frontend/`):

```bash
npm run dev
```

Open http://localhost:3000. The frontend expects the API on port 8000, and the API only accepts requests from `http://localhost:3000`.

The API does not auto-reload. Restart it after changing backend code.

## Try the demo

The demo sets up a company, a job with a procedure, and three applicants:

| Applicant | Scenario |
|---|---|
| Yousef | Clean documents. The agent finishes the whole onboarding by itself. |
| Abdulaziz | An unclear role ("Growth Lead"). The agent asks HR and waits. |
| Omar | Wrong documents in round 1 (one missing, one unsigned, one in a different name), corrected in round 2. |

From `backend/`:

```bash
.venv/bin/python -m scripts.seed_demo            # create the demo data
.venv/bin/python -m scripts.seed_demo --reset    # start the demo over
```

Log in as `hr@demo.com` with password `demo1234`. Open the job, press **Run agent**, then open an applicant and use **Reply email** to send their signed files.

The demo needs the blank and signed PDFs in `demo_files/`. That folder is git-ignored, so it is not in the repository. Without it, the seed script and its tests cannot run.

## Test

```bash
cd backend
.venv/bin/python -m pytest
```

The tests use a fake model, so they run offline and cost nothing.

## Evaluation

The evaluation replays scenarios against the real model on a throwaway database and saves the results in `backend/eval/results/`. It uses the OpenAI API and costs money.

```bash
cd backend
.venv/bin/python -m eval.run --variant rules          # fixed checklist baseline, no model, free
.venv/bin/python -m eval.run --variant agent          # the agent without the verifier
.venv/bin/python -m eval.run --variant full           # the agent with the verifier
.venv/bin/python -m eval.run --variant full --runs 1 --cases demo_yousef demo_abdulaziz demo_omar
```

The three demo cases only run when named.

## Project layout

```
backend/
  app/
    core/        config, database, auth, model wrapper (never imports from features/)
    features/    agent, plans, documents, candidates, jobs, systems, approvals, ...
  eval/          evaluation cases and runner
  scripts/       demo seed and helpers
  tests/
frontend/        Next.js app
spec.md          the original specification
```

Each feature folder has `controller.py`, `service.py`, `model.py` and `schema.py`. Features talk to each other only through `service.py`, and every table has a `company_id`, so one company can never see another's data.
