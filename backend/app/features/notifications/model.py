from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Email(SQLModel, table=True):
    """An email the agent sent. Exactly one of candidate_id or department_id is set."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int | None = Field(default=None, foreign_key="candidate.id", index=True)
    department_id: int | None = Field(default=None, foreign_key="department.id")
    regarding_candidate_id: int | None = Field(default=None, foreign_key="candidate.id")  # a department email about this new hire
    to_address: str
    subject: str
    body: str
    reason: str
    kind: str = "general"  # "general" or "documents_request"
    documents: list = Field(default_factory=list, sa_column=Column(JSON))
    attachments: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InboxMessage(SQLModel, table=True):
    """A reply that arrived. candidate_id is set when we could tell who sent it."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    candidate_id: int | None = Field(default=None, foreign_key="candidate.id", index=True)
    from_address: str
    subject: str
    body: str = ""
    attachments: list = Field(default_factory=list, sa_column=Column(JSON))
    external_id: str | None = Field(default=None, index=True)  # the email's Message-ID, so a reply is stored once
    in_reply_to: str | None = None  # the Message-ID of the email this answers
    processed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailSettings(SQLModel, table=True):
    """The mailbox a company sends from and reads replies from. provider "mock" is test mode."""

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", unique=True)
    provider: str = "smtp"
    email_address: str
    password_encrypted: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    allowed_recipients: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
