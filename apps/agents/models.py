"""Pydantic output models for agent nodes – used with Gemini structured output."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntakeFormData(BaseModel):
    """Validated intake data flowing into the agent graph."""

    intake_id: str
    education_level: str
    education_isced: str = ""
    country: str
    region_type: str
    work_experiences: list[WorkExperienceEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    digital_skills: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    connectivity: str = "moderate"


class WorkExperienceEntry(BaseModel):
    title: str
    sector: str = ""
    years: float = 0
    description: str = ""
    is_formal: bool = False


class LanguageEntry(BaseModel):
    language: str
    proficiency: str = "conversational"


# Re-declare IntakeFormData after WorkExperienceEntry is defined
IntakeFormData.model_rebuild()


class OccupationMatch(BaseModel):
    """An ISCO-08 occupation match from the skills mapping agent."""

    isco_code: str
    title: str
    description: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    esco_uri: str | None = None
    automation_risk: float = Field(ge=0.0, le=1.0, default=0.5)


class SkillClusterOutput(BaseModel):
    """A cluster of related skills identified by the mapping agent."""

    cluster_name: str
    skills: list[str] = Field(default_factory=list)
    proficiency_avg: float = Field(ge=0.0, le=5.0, default=1.0)
    esco_codes: list[str] = Field(default_factory=list)
    source: str = "self_reported"


class SkillsProfile(BaseModel):
    """Complete skills profile output from the map_skills node."""

    occupation_matches: list[OccupationMatch] = Field(default_factory=list)
    skill_clusters: list[SkillClusterOutput] = Field(default_factory=list)
    plain_language_summary: str = ""
    total_experience_years: float = 0


class RiskScore(BaseModel):
    """Per-skill automation risk breakdown."""

    skill_name: str
    isco_code: str = ""
    frey_osborne_score: float = Field(ge=0.0, le=1.0, default=0.5)
    calibrated_score: float = Field(ge=0.0, le=1.0, default=0.5)
    risk_category: str = Field(
        default="medium", pattern=r"^(low|medium|high|very_high)$"
    )


class UpskillingPath(BaseModel):
    """An adjacent occupation reachable through targeted upskilling."""

    target_isco: str
    target_title: str
    skills_gap: list[str] = Field(default_factory=list)
    estimated_training_months: int = 0
    growth_potential: str = "stable"


class RiskAssessment(BaseModel):
    """Output from the risk analysis agent."""

    per_skill_risks: list[RiskScore] = Field(default_factory=list)
    at_risk_tasks: list[str] = Field(default_factory=list)
    durable_skills: list[str] = Field(default_factory=list)
    adjacent_upskilling_paths: list[UpskillingPath] = Field(default_factory=list)
    overall_risk_score: float = Field(ge=0.0, le=1.0, default=0.5)
    narrative_explanation: str = ""
    projection_2025_2035: str = ""


class EconSignal(BaseModel):
    """A single econometric signal from the data pipeline."""

    indicator: str
    value: float
    unit: str = ""
    source: str = ""
    source_dataset: str = ""
    vintage_year: int | None = None
    country_code: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    trend: str = "stable"


class MatchedOpportunity(BaseModel):
    """A matched opportunity from vector search + re-ranking."""

    opportunity_id: str
    title: str
    organization: str = ""
    opportunity_type: str
    wage_range: tuple[float, float] | None = None
    sector_growth_pct: float | None = None
    match_score: float = Field(ge=0.0, le=1.0, default=0.0)
    skills_gap: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    re_rank_explanation: str = ""


class PortabilityMetadata(BaseModel):
    """Metadata about the generated profile's standards compliance."""

    isco_version: str = "ISCO-08"
    esco_version: str = "1.1.1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    portable_skills_count: int = 0
    cross_sector_matches: int = 0
    regional_mobility_score: float = Field(ge=0.0, le=1.0, default=0.0)


class GeneratedProfile(BaseModel):
    """The complete profile output assembled by the generate_profile node."""

    profile_id: UUID = Field(default_factory=uuid4)
    intake_id: str = ""
    context_id: str = ""
    occupation_matches: list[OccupationMatch] = Field(default_factory=list)
    skill_clusters: list[SkillClusterOutput] = Field(default_factory=list)
    risk_assessment: RiskAssessment | None = None
    econometric_signals: list[EconSignal] = Field(default_factory=list)
    matched_opportunities: list[MatchedOpportunity] = Field(default_factory=list)
    plain_language_summary: str = ""
    portability_metadata: PortabilityMetadata = Field(default_factory=PortabilityMetadata)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_vintage: int | None = None


class AgentNodeError(BaseModel):
    """Structured error emitted by a failed agent node."""

    node_name: str
    error_type: str
    message: str
    is_fatal: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
