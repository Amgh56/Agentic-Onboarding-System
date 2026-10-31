from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.jobs.model import DEFAULT_STAGES

JobStatus = Literal["onboarding", "closed"]
StartMode = Literal["auto", "notify", "ask_first"]


class JobCreate(BaseModel):
    title: str
    overview: str = ""
    description: str = ""
    status: JobStatus = "onboarding"
    start_mode: StartMode = "auto"
    procedure: str = ""
    stages: list[str] = Field(default_factory=lambda: list(DEFAULT_STAGES), min_length=1)


class JobRead(BaseModel):
    id: int
    title: str
    overview: str
    description: str
    status: JobStatus
    start_mode: StartMode
    procedure: str
    stages: list[str]
    created_at: datetime
