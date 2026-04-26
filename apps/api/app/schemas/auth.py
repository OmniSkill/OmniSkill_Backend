"""Schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AnonymousSessionResponse(BaseModel):
    session_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="youth", pattern=r"^(youth|policy|admin)$")
    context_id: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    session_id: str
    context_id: str = ""
    role: str = "youth"
    iat: int
    exp: int
