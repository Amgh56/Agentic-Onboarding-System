from datetime import datetime

from pydantic import BaseModel


class CompanyRead(BaseModel):
    id: int
    name: str
    created_at: datetime
