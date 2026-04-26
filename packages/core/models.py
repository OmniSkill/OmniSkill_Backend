"""Shared domain models for the UNMAPPED platform."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from packages.core.enums import OpportunityType


class DataSourcesConfig(BaseModel):
    """Endpoint keys for international data sources."""

    ilostat: str = ""
    wdi: str = ""
    esco: str = ""
    wittgenstein: str = ""


class SkillProfile(BaseModel):
    """A normalised skill with optional ESCO mapping."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    esco_code: str | None = None
    proficiency_level: int = Field(ge=1, le=5, default=1)
    source: str = "self_reported"


class Opportunity(BaseModel):
    """A labour-market opportunity surfaced by the platform."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = ""
    opportunity_type: OpportunityType
    skills_required: list[SkillProfile] = Field(default_factory=list)
    location: str = ""
    wage_range_usd: tuple[float, float] | None = None
    automation_risk: float = Field(ge=0.0, le=1.0, default=0.5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkerProfile(BaseModel):
    """Profile of a worker / job-seeker on the platform."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    country: str
    region: str = ""
    skills: list[SkillProfile] = Field(default_factory=list)
    education_level: str = ""
    years_experience: int = 0
    preferred_opportunity_types: list[OpportunityType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
