"""High-level auth service: session management, user registration, login."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from loguru import logger
from redis.asyncio import Redis

from apps.api.app.auth.jwt import (
    create_access_token,
    create_anonymous_token,
    create_refresh_token,
    decode_token,
)
from apps.api.app.auth.passwords import hash_password, verify_password
from apps.api.app.auth.settings import AuthSettings
from packages.core.exceptions import AuthenticationError

_settings = AuthSettings()


class AuthService:
    """Manages authentication, sessions, and token lifecycle."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def create_anonymous_session(self, context_id: str = "") -> dict:
        """Create an anonymous session with a 24h JWT."""
        token, session_id, user_id = create_anonymous_token(context_id)

        await self._redis.set(
            f"session:{session_id}",
            f"{user_id}|anonymous|{context_id}",
            ex=int(timedelta(hours=_settings.anonymous_token_expire_hours).total_seconds()),
        )

        logger.info("Anonymous session created: {}", session_id[:8])
        return {
            "session_id": session_id,
            "access_token": token,
            "token_type": "bearer",
            "expires_in": _settings.anonymous_token_expire_hours * 3600,
        }

    async def register_user(
        self, email: str, password: str, role: str = "youth", context_id: str = ""
    ) -> dict:
        """Register a new user with email + password."""
        existing = await self._redis.get(f"user:{email}")
        if existing is not None:
            raise AuthenticationError("Email already registered")

        hashed = hash_password(password)
        user_id = f"user-{email}"

        user_data = f"{hashed}|{role}|{context_id}|{datetime.now(UTC).isoformat()}"
        await self._redis.set(f"user:{email}", user_data)

        return await self._issue_tokens(user_id, role, context_id)

    async def login(self, email: str, password: str) -> dict:
        """Authenticate a registered user."""
        raw = await self._redis.get(f"user:{email}")
        if raw is None:
            raise AuthenticationError("Invalid email or password")

        parts = raw.decode() if isinstance(raw, bytes) else raw
        stored_hash, role, context_id, _created = parts.split("|", 3)

        if not verify_password(password, stored_hash):
            raise AuthenticationError("Invalid email or password")

        user_id = f"user-{email}"
        return await self._issue_tokens(user_id, role, context_id)

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Issue new access + refresh tokens from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise AuthenticationError("Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError("Token is not a refresh token")

        revoked = await self._redis.get(f"revoked:{refresh_token[:32]}")
        if revoked is not None:
            raise AuthenticationError("Refresh token has been revoked")

        await self._redis.set(
            f"revoked:{refresh_token[:32]}", "1", ex=int(timedelta(days=31).total_seconds())
        )

        session_data = await self._redis.get(f"session:{payload['session_id']}")
        role = "youth"
        context_id = ""
        if session_data:
            parts = (session_data.decode() if isinstance(session_data, bytes) else session_data)
            _uid, role, context_id = parts.split("|", 2)

        return await self._issue_tokens(payload["sub"], role, context_id)

    async def revoke_session(self, session_id: str) -> None:
        """Revoke a session (logout)."""
        await self._redis.delete(f"session:{session_id}")

    async def validate_session(self, session_id: str) -> bool:
        """Check if a session is still active in Redis."""
        return await self._redis.exists(f"session:{session_id}") > 0

    async def _issue_tokens(self, user_id: str, role: str, context_id: str) -> dict:
        """Create access + refresh tokens and persist the session."""
        import uuid

        session_id = uuid.uuid4().hex
        access = create_access_token(user_id, session_id, context_id, role)
        refresh = create_refresh_token(user_id, session_id)

        await self._redis.set(
            f"session:{session_id}",
            f"{user_id}|{role}|{context_id}",
            ex=int(timedelta(days=_settings.refresh_token_expire_days).total_seconds()),
        )

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": _settings.access_token_expire_minutes * 60,
            "role": role,
        }
