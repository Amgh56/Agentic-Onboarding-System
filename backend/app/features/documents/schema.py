from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    job_id: int
    filename: str
    content_type: str
    created_at: datetime
