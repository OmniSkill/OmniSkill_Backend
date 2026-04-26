"""Authentication endpoints – anonymous sessions, registration, login, refresh."""

from fastapi import APIRouter, HTTPException, Request

from apps.api.app.schemas.auth import (
    AnonymousSessionResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from packages.core.exceptions import AuthenticationError

router = APIRouter()


def _auth_service(request: Request):
    return request.app.state.auth_service


@router.post("/anonymous", response_model=AnonymousSessionResponse)
async def create_anonymous_session(
    request: Request, context_id: str = ""
) -> AnonymousSessionResponse:
    """Create an anonymous session (no signup required). Default for mobile youth users."""
    svc = _auth_service(request)
    result = await svc.create_anonymous_session(context_id)
    return AnonymousSessionResponse(**result)


@router.post("/register", response_model=TokenResponse)
async def register(request: Request, body: RegisterRequest) -> TokenResponse:
    """Register a new user with email + password."""
    svc = _auth_service(request)
    try:
        result = await svc.register_user(
            body.email, body.password, body.role, body.context_id or ""
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TokenResponse(**result)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    """Authenticate with email + password."""
    svc = _auth_service(request)
    try:
        result = await svc.login(body.email, body.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(**result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, body: RefreshRequest) -> TokenResponse:
    """Exchange a refresh token for new access + refresh tokens."""
    svc = _auth_service(request)
    try:
        result = await svc.refresh_tokens(body.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(**result)
