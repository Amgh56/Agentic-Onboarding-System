from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.companies import service
from app.features.companies.schema import CompanyRead

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyRead)
def my_company(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.get_company(session, user.company_id)
