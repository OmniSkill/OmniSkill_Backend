"""Integration tests for the FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient

from apps.api.app.auth.service import AuthService
from apps.api.app.middleware.request_id import RequestIDMiddleware
from apps.api.app.ratelimit import limiter
from apps.api.app.routers import (
    admin,
    auth,
    config,
    health,
    intake,
    opportunities,
    profiles,
    signals,
)
from packages.config.loader import ConfigLoader


def _build_test_app() -> FastAPI:
    """Build a test app wired like the real app but without Redis/OTel."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.config_loader = ConfigLoader()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.ping = AsyncMock(return_value=True)
        app.state.redis = mock_redis

        app.state.auth_service = AuthService(mock_redis)
        yield

    test_app = FastAPI(lifespan=lifespan)
    test_app.state.limiter = limiter
    test_app.add_middleware(RequestIDMiddleware)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    test_app.include_router(health.router, tags=["health"])
    test_app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    test_app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
    test_app.include_router(intake.router, prefix="/api/v1/intake", tags=["intake"])
    test_app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
    test_app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
    test_app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
    test_app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    return test_app


@pytest.fixture
async def test_app() -> FastAPI:
    return _build_test_app()


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        test_app.state.config_loader = ConfigLoader()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.ping = AsyncMock(return_value=True)
        test_app.state.redis = mock_redis
        test_app.state.auth_service = AuthService(mock_redis)
        yield ac


async def _get_anon_token(client: AsyncClient) -> str:
    """Helper: create an anonymous session and return the access token."""
    resp = await client.post(
        "/api/v1/auth/anonymous", params={"context_id": "gha-urban-2024"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestHealthEndpoints:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "unmapped-api"

    async def test_readiness(self, client: AsyncClient) -> None:
        resp = await client.get("/ready")
        assert resp.status_code == 200

    async def test_request_id_header(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers


class TestAuthEndpoints:
    async def test_anonymous_session(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/anonymous", params={"context_id": "gha-urban-2024"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "session_id" in data

    async def test_register_and_login(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@unmapped.org",
                "password": "securepass123",
                "role": "youth",
                "context_id": "gha-urban-2024",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "youth"


class TestConfigEndpoints:
    async def test_list_contexts(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts")
        assert resp.status_code == 200
        contexts = resp.json()
        assert isinstance(contexts, list)
        assert "gha-urban-2024" in contexts

    async def test_get_context(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts/gha-urban-2024")
        assert resp.status_code == 200
        data = resp.json()
        assert data["context_id"] == "gha-urban-2024"

    async def test_get_missing_context(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts/zzz-missing-2024")
        assert resp.status_code == 422


class TestAuthenticatedEndpoints:
    async def test_intake_submit_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/intake/submit", json={})
        assert resp.status_code == 401

    async def test_opportunities_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/opportunities")
        assert resp.status_code == 401

    async def test_signals_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/signals/gha-urban-2024")
        assert resp.status_code == 401

    async def test_intake_submit_with_token(self, client: AsyncClient) -> None:
        token = await _get_anon_token(client)
        resp = await client.post(
            "/api/v1/intake/submit",
            json={
                "education_level": "secondary",
                "country": "GHA",
                "region_type": "urban_informal",
                "languages": [{"language": "en", "proficiency": "native"}],
                "work_experiences": [],
                "digital_skills": ["email"],
                "goals": ["employment"],
                "connectivity": "moderate",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Context-Id": "gha-urban-2024",
            },
        )
        assert resp.status_code == 200, f"Response: {resp.json()}"
        data = resp.json()
        assert data["status"] == "processing"
        assert "intake_id" in data
        assert data["context_id"] == "gha-urban-2024"

    async def test_opportunities_with_token(self, client: AsyncClient) -> None:
        token = await _get_anon_token(client)
        resp = await client.get(
            "/api/v1/opportunities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "opportunities" in data
        assert data["context_id"] == "gha-urban-2024"

    async def test_signals_with_token(self, client: AsyncClient) -> None:
        token = await _get_anon_token(client)
        resp = await client.get(
            "/api/v1/signals/gha-urban-2024",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["context_id"] == "gha-urban-2024"

    async def test_admin_requires_admin_role(self, client: AsyncClient) -> None:
        token = await _get_anon_token(client)
        resp = await client.get(
            "/api/v1/admin/pipeline/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
