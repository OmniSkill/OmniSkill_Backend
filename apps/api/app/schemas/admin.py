"""Schemas for admin endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PipelineStatusResponse(BaseModel):
    pipeline_name: str
    status: str = Field(default="unknown", pattern=r"^(running|completed|failed|pending|unknown)$")
    last_run: datetime | None = None
    records_processed: int = 0
    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0
