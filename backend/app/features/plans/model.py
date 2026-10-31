from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Plan(SQLModel, table=True):
    """The steps drafted from a job's procedure. The agent only runs once HR approves it."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    job_id: int = Field(foreign_key="job.id", unique=True)
    steps: list = Field(default_factory=list, sa_column=Column(JSON))
    departments: list = Field(default_factory=list, sa_column=Column(JSON))  # as found in the procedure
    approved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
