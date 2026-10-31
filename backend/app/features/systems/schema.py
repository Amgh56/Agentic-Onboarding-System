from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str


class SystemRead(BaseModel):
    key: str
    name: str
    name_ar: str
    kind: str
    description: str
    groups: list[GroupRead]


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    system_key: str
    candidate_id: int
    display_name: str
    address: str
    groups: list[str]
    status: str
    created_at: datetime


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    requester: str
    item: str
    status: str
    created_at: datetime


class SystemContents(BaseModel):
    key: str
    name: str
    name_ar: str
    kind: str
    accounts: list[AccountRead]
    tickets: list[TicketRead]


class CandidateAccounts(BaseModel):
    accounts: list[AccountRead]
    tickets: list[TicketRead]
