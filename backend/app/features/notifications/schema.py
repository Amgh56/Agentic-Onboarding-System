from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class EmailRead(BaseModel):
    id: int
    candidate_id: int | None
    department_id: int | None
    to_address: str
    subject: str
    body: str
    reason: str
    attachments: list[str]
    created_at: datetime


class InboxRead(BaseModel):
    id: int
    candidate_id: int | None
    from_address: str
    subject: str
    attachments: list[dict]
    processed: bool
    created_at: datetime


class EmailSettingsSave(BaseModel):
    provider: Literal["smtp", "mock"] = "smtp"
    email_address: str = Field(min_length=3)
    password: str | None = None  # leave it out to keep the saved one
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    allowed_recipients: list[str] = Field(default_factory=list)


class EmailSettingsRead(BaseModel):
    provider: str
    email_address: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int
    allowed_recipients: list[str]
    has_password: bool


class ConnectionResult(BaseModel):
    ok: bool
    smtp: str
    imap: str


class SyncResult(BaseModel):
    new_messages: int
    matched: int
