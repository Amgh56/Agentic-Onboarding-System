from pydantic import BaseModel


class SignupRequest(BaseModel):
    company_name: str
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    company_id: int
    full_name: str
    email: str
