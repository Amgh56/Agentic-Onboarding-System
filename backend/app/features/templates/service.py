from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.templates.model import Template
from app.features.templates.schema import TemplateCreate


def create_template(session: Session, company_id: int, data: TemplateCreate) -> Template:
    template = Template(
        company_id=company_id,
        name=data.name,
        steps=[step.model_dump() for step in data.steps],
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def list_templates(session: Session, company_id: int) -> list[Template]:
    return session.exec(select(Template).where(Template.company_id == company_id)).all()


def get_template(session: Session, company_id: int, template_id: int) -> Template:
    template = session.get(Template, template_id)
    if not template or template.company_id != company_id:
        raise HTTPException(404, "Template not found")
    return template
