"""Schemas for the skills intake flow."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class WorkExperience(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    sector: str = ""
    years: float = Field(ge=0, le=60, default=0)
    description: str = ""
    is_formal: bool = False


class LanguageEntry(BaseModel):
    language: str = Field(..., min_length=2, max_length=10, description="BCP-47 tag")
    proficiency: str = Field(
        default="conversational",
        pattern=r"^(basic|conversational|professional|native)$",
    )


class IntakeFormRequest(BaseModel):
    education_level: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=3)
    region_type: str = Field(..., min_length=1)
    work_experiences: list[WorkExperience] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(min_length=1)
    digital_skills: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list, max_length=10)
    connectivity: str = Field(
        default="moderate",
        pattern=r"^(none|low|moderate|high)$",
    )

    @field_validator("digital_skills")
    @classmethod
    def deduplicate_digital_skills(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


class IntakeFormResponse(BaseModel):
    intake_id: str
    profile_id: str
    status: str = "processing"
    context_id: str
    data_vintage: int | None = None
    response_time_ms: float = 0.0
