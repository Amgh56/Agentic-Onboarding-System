from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    filename: str
    stored_name: str
    content_type: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
