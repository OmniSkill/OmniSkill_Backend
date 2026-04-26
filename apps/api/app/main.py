"""UNMAPPED FastAPI gateway – single entry point for all clients."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from redis.asyncio import Redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.app.auth.service import AuthService
from apps.api.app.auth.settings import AuthSettings
from apps.api.app.middleware.context import ContextResolverMiddleware
from apps.api.app.middleware.logging import StructuredLoggingMiddleware
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
from packages.core.exceptions import AgentError, ConfigNotFoundError, ConfigValidationError

_auth_settings = AuthSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hooks."""
    logger.info("UNMAPPED API starting up")

    redis = Redis.from_url(_auth_settings.redis_url, decode_responses=True)
    app.state.redis = redis

    loader = ConfigLoader(redis=redis)
    app.state.config_loader = loader
    await loader.start_watching()

    app.state.auth_service = AuthService(redis)

    logger.info("All services initialised")
    yield

    await loader.stop_watching()
    await redis.aclose()
    logger.info("UNMAPPED API shut down")


app = FastAPI(
    title="UNMAPPED API",
    description="Labour-market intelligence platform for LMICs",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware (order matters: outermost first) ---
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(ContextResolverMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_auth_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# --- OpenTelemetry auto-instrumentation ---
FastAPIInstrumentor.instrument_app(app)


# --- Global exception handlers ---


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "detail": exc.detail,
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


@app.exception_handler(ConfigNotFoundError)
async def config_not_found_handler(request: Request, exc: ConfigNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "config_not_found",
            "detail": str(exc),
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


@app.exception_handler(ConfigValidationError)
async def config_validation_handler(
    request: Request, exc: ConfigValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "config_validation_error",
            "detail": str(exc),
            "context_id": exc.context_id,
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
    logger.error("Agent error: {}", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "agent_error",
            "detail": str(exc),
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on {} {}", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred",
            "request_id": getattr(getattr(request, "state", None), "request_id", None),
        },
    )


# --- Routers ---
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(intake.router, prefix="/api/v1/intake", tags=["intake"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
