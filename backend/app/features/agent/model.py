from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ActionLog(SQLModel, table=True):
    """Every tool call the agent made: what it asked, what came back, and why."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    tool: str
    input: dict = Field(default_factory=dict, sa_column=Column(JSON))
    output: dict = Field(default_factory=dict, sa_column=Column(JSON))
    reason: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
