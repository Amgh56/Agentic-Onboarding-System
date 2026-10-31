from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Approval(SQLModel, table=True):
    """An item in the HR queue.

    kind "escalation": the agent needs HR. kind "approval": an action waiting for HR (start mode ask_first).
    kind "notice": an action the agent already took (start mode notify). status: pending, approved, declined, done.
    """

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    kind: str
    action: str = ""
    reason: str
    status: str = "pending"
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))  # the action to run once HR approves
    decision_note: str = ""
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
