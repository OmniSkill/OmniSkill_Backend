"""Integration tests for the FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from packages.config.loader import ConfigLoader


def _build_test_app() -> FastAPI:
    """Build a test app with a synchronous lifespan that skips file watching."""
    from apps.api.app.routes import config as config_routes
    from apps.api.app.routes import health

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.config_loader = ConfigLoader()
        yield

    test_app = FastAPI(lifespan=lifespan)
    test_app.include_router(health.router, tags=["health"])
    test_app.include_router(config_routes.router, prefix="/api/v1/config", tags=["config"])
    return test_app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    test_app = _build_test_app()
    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Manually trigger lifespan startup
        test_app.state.config_loader = ConfigLoader()
        yield ac


class TestHealthEndpoints:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    async def test_readiness(self, client: AsyncClient) -> None:
        resp = await client.get("/ready")
        assert resp.status_code == 200


class TestConfigEndpoints:
    async def test_list_contexts(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts")
        assert resp.status_code == 200
        contexts = resp.json()
        assert isinstance(contexts, list)

    async def test_get_context(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts/gha-urban-2024")
        assert resp.status_code == 200
        data = resp.json()
        assert data["context_id"] == "gha-urban-2024"

    async def test_get_missing_context(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/config/contexts/zzz-missing-2024")
        assert resp.status_code == 422
