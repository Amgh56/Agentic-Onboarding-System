from datetime import datetime, timezone

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class CompanySystem(SQLModel, table=True):
    """A system the company uses. kind is mailbox, account, invite or tickets."""

    __table_args__ = (UniqueConstraint("company_id", "key"),)

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    key: str
    name: str
    name_ar: str
    kind: str
    description: str
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))


class SystemGroup(SQLModel, table=True):
    """A role, team or channel that exists in a system. The agent can only pick from these."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    system_key: str
    name: str
    description: str


class Account(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("candidate_id", "system_key"),)

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    system_key: str
    display_name: str
    address: str
    groups: list = Field(default_factory=list, sa_column=Column(JSON))
    status: str  # "created" or "invited"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Ticket(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("candidate_id", "item"),)

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    system_key: str
    requester: str
    item: str
    status: str = "created"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
