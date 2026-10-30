from sqlmodel import Session

from app.features.companies.model import Company


def create_company(session: Session, name: str) -> Company:
    company = Company(name=name)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def get_company(session: Session, company_id: int) -> Company:
    return session.get(Company, company_id)
