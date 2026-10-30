from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.templates import service
from app.features.templates.schema import TemplateCreate, TemplateRead

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateRead, status_code=201)
def create_template(
    data: TemplateCreate, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.create_template(session, user.company_id, data)


@router.get("", response_model=list[TemplateRead])
def list_templates(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_templates(session, user.company_id)


@router.get("/{template_id}", response_model=TemplateRead)
def get_template(
    template_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.get_template(session, user.company_id, template_id)
