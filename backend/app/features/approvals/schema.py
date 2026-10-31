from datetime import datetime

from pydantic import BaseModel


class ApprovalRead(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str
    job_id: int
    kind: str
    action: str
    reason: str
    status: str
    decision_note: str
    created_at: datetime
    decided_at: datetime | None


class Decision(BaseModel):
    approve: bool
    note: str = ""
