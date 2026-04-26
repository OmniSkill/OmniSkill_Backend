"""Unit tests for JWT token creation and password hashing."""

from __future__ import annotations

import jwt
import pytest

from apps.api.app.auth.jwt import (
    create_access_token,
    create_anonymous_token,
    create_refresh_token,
    decode_token,
)
from apps.api.app.auth.passwords import hash_password, verify_password


class TestJWT:
    def test_create_and_decode_access_token(self) -> None:
        token = create_access_token("user-1", "session-1", "gha-urban-2024", "youth")
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["session_id"] == "session-1"
        assert payload["context_id"] == "gha-urban-2024"
        assert payload["role"] == "youth"
        assert "iat" in payload
        assert "exp" in payload

    def test_create_anonymous_token(self) -> None:
        token, session_id, user_id = create_anonymous_token("bgd-rural-2024")
        assert session_id
        assert user_id.startswith("anon-")
        payload = decode_token(token)
        assert payload["context_id"] == "bgd-rural-2024"
        assert payload["role"] == "youth"

    def test_create_refresh_token(self) -> None:
        token = create_refresh_token("user-1", "session-1")
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises(self) -> None:
        with pytest.raises(jwt.PyJWTError):
            decode_token("invalid.token.here")

    def test_jwt_payload_fields(self) -> None:
        token = create_access_token("u", "s", "ctx", "admin")
        payload = decode_token(token)
        assert set(payload.keys()) >= {"sub", "session_id", "context_id", "role", "iat", "exp"}


class TestPasswords:
    def test_hash_and_verify(self) -> None:
        hashed = hash_password("my-secret-password")
        assert hashed != "my-secret-password"
        assert verify_password("my-secret-password", hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)
