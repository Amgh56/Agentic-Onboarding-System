from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    actor: str  # "agent", "hr" or "system"
    title: str
    detail: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def log_event(
    session: Session, company_id: int, candidate_id: int, actor: str, title: str, detail: str = ""
) -> None:
    session.add(
        Event(company_id=company_id, candidate_id=candidate_id, actor=actor, title=title, detail=detail)
    )
