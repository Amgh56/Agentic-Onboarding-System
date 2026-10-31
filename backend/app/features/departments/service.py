from fastapi import HTTPException
from sqlmodel import Session, func, select

# Every company has these. They are fixed on purpose: nobody has to set departments up.
DEFAULT_DEPARTMENTS = [
    ("IT", "it", "Laptops, equipment and system access"),
    ("Payroll", "payroll", "Salaries and bank details"),
    ("Finance", "finance", "Budgets, cost centres and expenses"),
    ("HR", "hr", "Contracts, policies and employee records"),
]

from app.features.departments.model import Department
from app.features.departments.schema import DepartmentCreate


def create_department(session: Session, company_id: int, data: DepartmentCreate) -> Department:
    department = Department(company_id=company_id, **data.model_dump())
    session.add(department)
    session.commit()
    session.refresh(department)
    return department


def list_departments(session: Session, company_id: int) -> list[Department]:
    query = select(Department).where(Department.company_id == company_id)
    return session.exec(query.order_by(Department.id)).all()


def get_department(session: Session, company_id: int, department_id: int) -> Department:
    department = session.get(Department, department_id)
    if not department or department.company_id != company_id:
        raise HTTPException(404, "Department not found")
    return department


def update_department(
    session: Session, company_id: int, department_id: int, data: DepartmentCreate
) -> Department:
    department = get_department(session, company_id, department_id)
    for field, value in data.model_dump().items():
        setattr(department, field, value)
    session.add(department)
    session.commit()
    session.refresh(department)
    return department


def delete_department(session: Session, company_id: int, department_id: int) -> None:
    department = get_department(session, company_id, department_id)
    session.delete(department)
    session.commit()


def ensure_defaults(session: Session, company_id: int, domain: str) -> None:
    """Add any of the four fixed departments the company does not have yet. Safe to run again."""
    existing = {d.name.lower() for d in list_departments(session, company_id)}
    for name, mailbox, handles in DEFAULT_DEPARTMENTS:
        if name.lower() not in existing:
            session.add(Department(company_id=company_id, name=name, email=f"{mailbox}@{domain}", handles=handles))
    session.commit()
