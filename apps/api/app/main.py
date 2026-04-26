"""UNMAPPED FastAPI gateway – the main entry point for the backend API."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from apps.api.app.routes import config as config_routes
from apps.api.app.routes import health
from packages.config.loader import ConfigLoader


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hooks."""
    logger.info("UNMAPPED API starting up")

    loader = ConfigLoader()
    app.state.config_loader = loader
    await loader.start_watching()

    yield

    await loader.stop_watching()
    logger.info("UNMAPPED API shut down")


app = FastAPI(
    title="UNMAPPED API",
    description="Labour-market intelligence platform for LMICs",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(config_routes.router, prefix="/api/v1/config", tags=["config"])
