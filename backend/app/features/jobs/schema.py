from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.jobs.model import DEFAULT_STAGES

JobStatus = Literal["draft", "onboarding", "closed"]


class JobCreate(BaseModel):
    title: str
    overview: str = ""
    description: str = ""
    template_id: int | None = None
    status: JobStatus = "draft"
    procedure: str = ""
    stages: list[str] = Field(default_factory=lambda: list(DEFAULT_STAGES), min_length=1)


class JobRead(BaseModel):
    id: int
    template_id: int | None
    title: str
    overview: str
    description: str
    status: JobStatus
    procedure: str
    stages: list[str]
    created_at: datetime
