"""Schemas for profile generation and retrieval."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OccupationMatch(BaseModel):
    isco_code: str
    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    esco_uri: str | None = None
    automation_risk: float = Field(ge=0.0, le=1.0, default=0.5)


class SkillCluster(BaseModel):
    cluster_name: str
    skills: list[str]
    proficiency_avg: float = Field(ge=0.0, le=5.0)
    source: str = "self_reported"
    esco_mapped: bool = False


class EconSignal(BaseModel):
    indicator: str
    value: float
    unit: str = ""
    source: str = ""
    vintage_year: int | None = None
    trend: str = Field(default="stable", pattern=r"^(growing|stable|declining)$")


class PortabilityMetadata(BaseModel):
    portable_skills_count: int = 0
    cross_sector_matches: int = 0
    regional_mobility_score: float = Field(ge=0.0, le=1.0, default=0.0)


class GenerateProfileRequest(BaseModel):
    intake_id: str
    context_id: str | None = None


class ProfileResponse(BaseModel):
    profile_id: UUID
    created_at: datetime
    occupation_matches: list[OccupationMatch] = Field(default_factory=list)
    skill_clusters: list[SkillCluster] = Field(default_factory=list)
    econometric_signals: list[EconSignal] = Field(default_factory=list)
    portability_metadata: PortabilityMetadata = Field(default_factory=PortabilityMetadata)
    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0
