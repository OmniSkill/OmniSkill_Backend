"""Pydantic models for country-level configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from packages.core.enums import OpportunityType


class DataSourcesConfig(BaseModel):
    """Endpoint keys / URLs for international labour-market data sources."""

    ilostat: str = ""
    wdi: str = ""
    esco: str = ""
    wittgenstein: str = ""


class CountryConfig(BaseModel):
    """Full configuration for a single country context."""

    context_id: str = Field(
        ..., description="Unique identifier like 'gha-urban-2024'", pattern=r"^[a-z]{3}-\w+-\d{4}$"
    )
    country: str = Field(..., min_length=2, description="ISO-3166 alpha-3 or full country name")
    region_type: Literal["urban_formal", "urban_informal", "rural_agricultural", "custom"]
    language: str = Field(
        ..., description="BCP-47 language tag, e.g. 'en', 'bn', 'tw'"
    )
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)
    automation_calibration: float = Field(
        ge=0.0,
        le=1.0,
        description="LMIC adjustment multiplier for automation risk estimates",
    )
    opportunity_types: list[OpportunityType] = Field(
        min_length=1,
        description="Which opportunity types are relevant for this context",
    )
    wage_vintage: int = Field(
        ge=2000, le=2100, description="Reference year for wage data"
    )
    education_taxonomy: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of local education levels to ISCED codes",
    )

    @field_validator("language")
    @classmethod
    def validate_bcp47(cls, v: str) -> str:
        parts = v.split("-")
        if not (2 <= len(parts[0]) <= 3):
            raise ValueError(f"Primary language subtag must be 2-3 chars, got '{parts[0]}'")
        return v
