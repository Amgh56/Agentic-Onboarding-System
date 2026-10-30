from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StepType = Literal[
    "info",
    "document",
    "policy",
    "external_check",
    "contract",
    "department_task",
    "id_card",
    "notification",
    "approval",
    "custom_form",
    "custom_document",
    "custom_task",
    "custom_approval",
]


class Step(BaseModel):
    id: str
    type: StepType
    title: str
    config: dict = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    autonomy: Literal["auto", "notify", "ask_first"] = "auto"


class TemplateCreate(BaseModel):
    name: str
    steps: list[Step] = Field(default_factory=list)


class TemplateRead(BaseModel):
    id: int
    name: str
    steps: list[Step]
    created_at: datetime
