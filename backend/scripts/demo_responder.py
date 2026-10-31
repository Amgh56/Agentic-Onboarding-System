"""Play the applicants during the demo, so nobody has to click.

Run from backend/, while the API is running and the company's email is in test mode:

    python -m scripts.demo_responder --delay 10 --interval 2

Every --interval seconds it looks at the emails the agent has stored for applicants that have a folder
in demo_files/. When an applicant still owes documents, it replies with their files: --delay seconds
after the first email, --retry-delay seconds after each later one (so HR can see the problem email first).
"""

import argparse
import time
from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.core.database import engine
from app.features.candidates import service as candidates_service
from app.features.documents import service as documents_service
from app.features.notifications import service as notifications_service
from scripts import seed_demo, send_reply

FIRST_BODY = "Hi, please find the signed documents attached."
LATER_BODY = "Sorry about that, here are the corrected documents."


class RealClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def require_test_mode(session: Session, company_id: int) -> None:
    settings = notifications_service.find_settings(session, company_id)
    if not settings or settings.provider != "mock":
        raise SystemExit("The demo responder only runs when the company's email is in test mode. Change it in Email settings.")


def as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


class Responder:
    def __init__(self, company_id: int, clock, delay: int, retry_delay: int, baseline: int):
        self.company_id, self.clock, self.delay, self.retry_delay = company_id, clock, delay, retry_delay
        self.baseline = baseline  # only emails after this id were created since the responder started
        self.seen: set[int] = set()
        self.pending: dict[int, tuple[str, int, datetime, datetime]] = {}  # email id -> persona, candidate, due, sent at
        self.replies: dict[str, int] = {}

    def owes_documents(self, session: Session, candidate_id: int) -> bool:
        requested = notifications_service.latest_requested_documents(session, self.company_id, candidate_id)
        return bool(requested) and bool(documents_service.still_missing(session, self.company_id, candidate_id, requested))

    def watch_new_emails(self, session: Session) -> None:
        personas = {folder.name for folder in send_reply.DEMO_FILES.iterdir() if folder.is_dir()}
        for email in reversed(notifications_service.list_outbox(session, self.company_id)):
            if email.id <= self.baseline or email.id in self.seen or not email.candidate_id:
                continue
            self.seen.add(email.id)
            candidate = candidates_service.get_candidate(session, self.company_id, email.candidate_id)
            persona = candidate.full_name_en.split()[0].lower()
            if persona not in personas or not self.owes_documents(session, candidate.id):
                continue
            wait = self.retry_delay if self.replies.get(persona) else self.delay
            sent_at = as_utc(email.created_at)
            self.pending[email.id] = (persona, candidate.id, sent_at + timedelta(seconds=wait), sent_at)

    def tick(self, session: Session) -> list[str]:
        """One look at the emails. Returns a line for each reply it sent."""
        self.watch_new_emails(session)
        lines = []
        for email_id, (persona, candidate_id, due, sent_at) in sorted(self.pending.items()):
            now = self.clock.now()
            if now < due:
                continue
            del self.pending[email_id]
            if not self.owes_documents(session, candidate_id):
                continue
            round_number = self.replies.get(persona, 0) + 1
            body = FIRST_BODY if round_number == 1 else LATER_BODY
            send_reply.send(session, self.company_id, persona, round_number, body)
            self.replies[persona] = round_number
            lines.append(f"{persona.title()} replied (round {round_number}) after {int((now - sent_at).total_seconds())}s")
        return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=int, default=10, help="seconds before the first reply")
    parser.add_argument("--retry-delay", type=int, default=30, help="seconds before a reply to a later email")
    parser.add_argument("--interval", type=int, default=2, help="seconds between looks at the emails")
    args = parser.parse_args()

    with Session(engine) as session:
        company_id = seed_demo.demo_company_id(session)
        require_test_mode(session, company_id)
        baseline = max([e.id for e in notifications_service.list_outbox(session, company_id)], default=0)
    responder = Responder(company_id, RealClock(), args.delay, args.retry_delay, baseline)
    print(f"Demo responder running (first reply after {args.delay}s, later ones after {args.retry_delay}s). Ctrl+C to stop.")
    while True:
        with Session(engine) as session:
            for line in responder.tick(session):
                print(line, flush=True)
        time.sleep(args.interval)
