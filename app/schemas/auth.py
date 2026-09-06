"""Schémas du module authentification."""
from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Page


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class RecoverRequest(BaseModel):
    email: EmailStr


class SessionInfo(BaseModel):
    id: str
    created_at: str
    expires_at: str
    revoked: bool
    ip_address: str = ""
    device_id: str = ""
    user_agent: str = ""