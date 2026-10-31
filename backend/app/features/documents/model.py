from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    filename: str
    stored_name: str
    content_type: str = ""
    instructions: str = ""  # e.g. "Please sign at the end of each page". If set, the candidate sends it back.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateDocument(SQLModel, table=True):
    """A file a candidate sent back. status is received, valid or rejected."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    message_id: int
    filename: str
    stored_name: str
    content_type: str = ""
    status: str = "received"
    result: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
