from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.departments import service
from app.features.departments.schema import DepartmentCreate, DepartmentRead

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("", response_model=DepartmentRead, status_code=201)
def create_department(
    data: DepartmentCreate, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.create_department(session, user.company_id, data)


@router.get("", response_model=list[DepartmentRead])
def list_departments(user=Depends(get_current_user), session: Session = Depends(get_session)):
    return service.list_departments(session, user.company_id)


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    data: DepartmentCreate,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.update_department(session, user.company_id, department_id, data)


@router.delete("/{department_id}", status_code=204)
def delete_department(
    department_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    service.delete_department(session, user.company_id, department_id)
    return Response(status_code=204)
