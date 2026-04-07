"""Auth Pydantic schemas."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    nom: str
    email: EmailStr
    password: str
    role: str = "ANALYSTE"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
