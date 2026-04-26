"""JWT token creation and verification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from apps.api.app.auth.settings import AuthSettings

_settings = AuthSettings()


def create_access_token(
    user_id: str,
    session_id: str,
    context_id: str = "",
    role: str = "youth",
    *,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=_settings.access_token_expire_minutes))
    payload = {
        "sub": user_id,
        "session_id": session_id,
        "context_id": context_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, _settings.jwt_secret_key, algorithm=_settings.jwt_algorithm)


def create_refresh_token(
    user_id: str,
    session_id: str,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(days=_settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "session_id": session_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, _settings.jwt_secret_key, algorithm=_settings.jwt_algorithm)


def create_anonymous_token(context_id: str = "") -> tuple[str, str, str]:
    """Create an anonymous session. Returns (access_token, session_id, user_id)."""
    user_id = f"anon-{uuid4().hex[:16]}"
    session_id = uuid4().hex
    token = create_access_token(
        user_id,
        session_id,
        context_id=context_id,
        role="youth",
        expires_delta=timedelta(hours=_settings.anonymous_token_expire_hours),
    )
    return token, session_id, user_id


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, _settings.jwt_secret_key, algorithms=[_settings.jwt_algorithm])
