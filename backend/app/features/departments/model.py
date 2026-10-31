from sqlmodel import Field, SQLModel


class Department(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    name: str
    email: str
    handles: str
