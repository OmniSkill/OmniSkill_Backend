"""Schemas for config endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class SwitchContextRequest(BaseModel):
    context_id: str


class SwitchContextResponse(BaseModel):
    context_id: str
    country: str
    region_type: str
    status: str = "active"
    response_time_ms: float = 0.0
