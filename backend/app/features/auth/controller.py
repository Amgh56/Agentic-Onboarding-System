from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth import service
from app.features.auth.schema import LoginRequest, SignupRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    return service.signup(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    return service.login(session, data)


@router.get("/me", response_model=UserRead)
def me(user=Depends(service.get_current_user)):
    return user
