from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import create_token, hash_password, read_token, verify_password
from app.features.auth.model import User
from app.features.auth.schema import LoginRequest, SignupRequest, TokenResponse
from app.features.companies import service as companies_service
from app.features.departments import service as departments_service
from app.features.systems import service as systems_service

bearer = HTTPBearer()


def signup(session: Session, data: SignupRequest) -> TokenResponse:
    if session.exec(select(User).where(User.email == data.email)).first():
        raise HTTPException(400, "Email already registered")
    company = companies_service.create_company(session, data.company_name)
    domain = systems_service.seed_defaults(session, company.id, company.name)
    departments_service.ensure_defaults(session, company.id, domain)
    user = User(
        company_id=company.id,
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return TokenResponse(access_token=create_token(user.id))


def login(session: Session, data: LoginRequest) -> TokenResponse:
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return TokenResponse(access_token=create_token(user.id))


def get_current_user(
    credentials=Depends(bearer), session: Session = Depends(get_session)
) -> User:
    user_id = read_token(credentials.credentials)
    user = session.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user
