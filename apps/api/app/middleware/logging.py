"""Structured logging middleware – logs method, path, status, duration, request_id."""

from __future__ import annotations

import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, duration_ms, and request_id."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        request_id = getattr(request.state, "request_id", "unknown")

        logger.info(
            "{method} {path} → {status} ({duration:.1f}ms) [rid={rid}]",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=duration_ms,
            rid=request_id,
        )

        return response
