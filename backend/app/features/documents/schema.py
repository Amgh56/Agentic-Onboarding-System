from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    job_id: int
    filename: str
    content_type: str
    instructions: str
    created_at: datetime


class DocumentInstructions(BaseModel):
    instructions: str = ""


class CandidateDocumentRead(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    reason: str
    created_at: datetime
