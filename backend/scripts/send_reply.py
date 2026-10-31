"""Play an applicant: reply to the last email the agent sent them, with their signed documents attached.

Run from backend/:

    python -m scripts.send_reply --persona omar [--round 1]

The reply goes through the same steps as "Check for replies": it is matched to the applicant, stored,
and the agent wakes up to read it.
"""

import argparse
from pathlib import Path

from sqlmodel import Session

from app.core.database import engine
from app.features.agent import service as agent_service
from app.features.candidates import service as candidates_service
from app.features.jobs import service as jobs_service
from app.features.notifications import service as notifications_service
from scripts import seed_demo

DEMO_FILES = Path(__file__).resolve().parents[2] / "demo_files"
DEFAULT_BODY = "Hi, please find the signed documents attached."


def find_applicant(session: Session, company_id: int, persona: str):
    """The applicant whose first name is the persona, e.g. "omar" for Omar Ateeq Alghamdi."""
    for job in jobs_service.list_jobs(session, company_id):
        for candidate in candidates_service.list_candidates(session, company_id, job.id):
            if candidate.full_name_en.split()[0].lower() == persona.lower():
                return candidate
    raise SystemExit(f"No applicant called {persona}")


def files_for(persona: str, round_number: int | None) -> list[Path]:
    """The PDFs in demo_files/<persona>/round<N>/ when that folder exists, otherwise demo_files/<persona>/."""
    folder = DEMO_FILES / persona.lower()
    if round_number is not None and (folder / f"round{round_number}").is_dir():
        folder = folder / f"round{round_number}"
    return sorted(folder.glob("*.pdf"))


def send(session: Session, company_id: int, persona: str, round_number: int | None = None, body: str = DEFAULT_BODY) -> str:
    candidate = find_applicant(session, company_id, persona)
    sent = [e for e in notifications_service.list_for_candidate(session, company_id, candidate.id) if e.candidate_id == candidate.id]
    if not sent:
        raise SystemExit(f"The agent has not emailed {candidate.full_name_en} yet")
    last = sent[-1]

    files = [(path.name, "application/pdf", path.read_bytes()) for path in files_for(persona, round_number)]
    if not files:
        raise SystemExit(f"No PDFs found for {persona} in {DEMO_FILES}")
    message = notifications_service.drop_message(
        session, company_id, candidate.email, f"Re: {last.subject}", body, files, in_reply_to=f"<onb-email-{last.id}@demo.local>"
    )
    agent_service.receive(session, company_id, [message])
    return f"{candidate.full_name_en} replied with {len(files)} files" + (f" (round {round_number})" if round_number else "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", required=True)
    parser.add_argument("--round", type=int, dest="round_number")
    args = parser.parse_args()
    with Session(engine) as session:
        print(send(session, seed_demo.demo_company_id(session), args.persona, args.round_number))
