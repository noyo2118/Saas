"""Auth request / response models."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class OTPRequestIn(BaseModel):
    email: EmailStr


class OTPVerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str


class MeOut(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    is_verified: bool
    is_admin: bool
