from datetime import datetime

from pydantic import BaseModel, Field


class DraftStep(BaseModel):
    title: str = Field(min_length=1)
    details: str = ""


class DraftDepartment(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    handles: str = ""


class Draft(BaseModel):
    steps: list[DraftStep] = Field(min_length=1)


class PlanStep(BaseModel):
    id: str
    title: str
    details: str


class PlanRead(BaseModel):
    id: int
    job_id: int
    steps: list[PlanStep]
    departments: list[DraftDepartment]
    approved: bool
    created_at: datetime
