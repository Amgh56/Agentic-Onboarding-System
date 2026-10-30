from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class Candidate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    full_name_en: str
    full_name_ar: str
    phone: str
    email: str
    date_of_birth: date
    stage: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
