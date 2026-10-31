from datetime import datetime

from pydantic import BaseModel


class DeadlineCheck(BaseModel):
    now: datetime | None = None  # pretend it is this time, to test deadlines without waiting


class DeadlineResult(BaseModel):
    woken: int


class RunResult(BaseModel):
    steps: int
    summary: str
