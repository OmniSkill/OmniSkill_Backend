"""Common response wrapper and shared schema components."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ContextMeta(BaseModel):
    """Metadata included in every API response."""

    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0


class ErrorDetail(BaseModel):
    """Structured error response body."""

    error: str
    detail: str
    request_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
