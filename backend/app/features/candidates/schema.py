from datetime import date, datetime

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    full_name_en: str = Field(min_length=1)
    full_name_ar: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    email: str = Field(min_length=1)
    date_of_birth: date


class CandidateRead(BaseModel):
    id: int
    job_id: int
    full_name_en: str
    full_name_ar: str
    phone: str
    email: str
    date_of_birth: date
    stage: str
    created_at: datetime


class EventRead(BaseModel):
    id: int
    actor: str
    title: str
    detail: str
    created_at: datetime


class StageUpdate(BaseModel):
    stage: str


class JobCounts(BaseModel):
    job_id: int
    applicants: int
    in_progress: int
    completed: int
