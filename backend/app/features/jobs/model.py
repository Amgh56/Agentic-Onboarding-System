from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

DEFAULT_STAGES = ["Invited", "Documents", "Contract", "Onboarded"]


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    title: str
    overview: str = ""
    description: str = ""
    status: str = "onboarding"
    start_mode: str = "auto"  # "auto", "notify" or "ask_first"
    procedure: str = ""
    stages: list = Field(default_factory=lambda: list(DEFAULT_STAGES), sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
