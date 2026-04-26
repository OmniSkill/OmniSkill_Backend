from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class WorkExperience:
    title: str
    description: str
    years: float = 0.0
    education_level: str = ""


@dataclass(frozen=True)
class OccupationReference:
    isco_code: str
    title: str
    description: str


@dataclass(frozen=True)
class OccupationMatch:
    isco_code: str
    title: str
    confidence: float
    normalized_education_level: str = ""


@dataclass(frozen=True)
class ESCOSkill:
    id: str
    name: str
    category: str = ""
    is_digital: bool = False


@dataclass(frozen=True)
class SkillCluster:
    name: str
    skills: list[ESCOSkill]
    proficiency_level: str
    cluster_score: float


@dataclass(frozen=True)
class CountryConfig:
    country_code: str
    education_taxonomy: dict[str, str]
    isco_occupations: list[OccupationReference]
    context_id: str = ""
    isco_version: str = "ISCO-08"
    esco_version: str = "ESCO v1.1.2"


@dataclass(frozen=True)
class SkillsProfile:
    profile_id: str
    country_code: str
    generated_at: datetime
    context_id: str
    occupation_matches: list[OccupationMatch] = field(default_factory=list)
    skill_clusters: list[SkillCluster] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    recognition_countries_count: int = 0
    isco_version: str = "ISCO-08"
    esco_version: str = "ESCO v1.1.2"
