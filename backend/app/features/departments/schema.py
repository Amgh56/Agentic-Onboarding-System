from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    handles: str = Field(min_length=1)


class DepartmentRead(BaseModel):
    id: int
    name: str
    email: str
    handles: str
