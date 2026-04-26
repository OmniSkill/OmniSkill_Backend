"""Schemas for opportunity listing and matching."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OpportunityResponse(BaseModel):
    opportunity_id: str
    title: str
    organization: str = ""
    opportunity_type: str
    wage_range: tuple[float, float] | None = None
    sector_growth_pct: float | None = None
    skills_match_score: float = Field(ge=0.0, le=1.0, default=0.0)
    skills_gap: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0


class OpportunityListResponse(BaseModel):
    opportunities: list[OpportunityResponse] = Field(default_factory=list)
    total: int = 0
    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0
