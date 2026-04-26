"""Schemas for econometric signal endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.app.schemas.profiles import EconSignal


class SignalsResponse(BaseModel):
    context_id: str
    signals: list[EconSignal] = Field(default_factory=list)
    data_vintage: int | None = None
    response_time_ms: float = 0.0
