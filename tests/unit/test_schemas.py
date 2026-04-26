"""Unit tests for API request/response schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from apps.api.app.schemas.intake import IntakeFormRequest, LanguageEntry, WorkExperience
from apps.api.app.schemas.opportunities import OpportunityResponse
from apps.api.app.schemas.profiles import EconSignal, OccupationMatch, SkillCluster


class TestIntakeSchemas:
    def test_valid_intake_form(self) -> None:
        form = IntakeFormRequest(
            education_level="secondary",
            country="GHA",
            region_type="urban_informal",
            languages=[LanguageEntry(language="en", proficiency="native")],
        )
        assert form.country == "GHA"
        assert form.connectivity == "moderate"

    def test_intake_requires_language(self) -> None:
        with pytest.raises(ValidationError):
            IntakeFormRequest(
                education_level="secondary",
                country="GHA",
                region_type="urban_informal",
                languages=[],
            )

    def test_digital_skills_deduplicated(self) -> None:
        form = IntakeFormRequest(
            education_level="primary",
            country="BGD",
            region_type="rural_agricultural",
            languages=[LanguageEntry(language="bn")],
            digital_skills=["email", "email", "spreadsheets"],
        )
        assert form.digital_skills == ["email", "spreadsheets"]

    def test_work_experience_validation(self) -> None:
        exp = WorkExperience(title="Farmer", sector="agriculture", years=5)
        assert exp.is_formal is False

    def test_connectivity_pattern(self) -> None:
        with pytest.raises(ValidationError):
            IntakeFormRequest(
                education_level="secondary",
                country="GHA",
                region_type="urban_informal",
                languages=[LanguageEntry(language="en")],
                connectivity="super_fast",
            )


class TestProfileSchemas:
    def test_occupation_match(self) -> None:
        match = OccupationMatch(isco_code="9211", title="Farm worker", confidence=0.85)
        assert match.automation_risk == 0.5

    def test_skill_cluster(self) -> None:
        cluster = SkillCluster(
            cluster_name="Digital Basics", skills=["email", "web"], proficiency_avg=2.5
        )
        assert cluster.esco_mapped is False

    def test_econ_signal(self) -> None:
        signal = EconSignal(indicator="unemployment_rate", value=12.5, unit="%", source="ILO")
        assert signal.trend == "stable"


class TestOpportunitySchemas:
    def test_opportunity_response(self) -> None:
        opp = OpportunityResponse(
            opportunity_id="opp-1",
            title="Market trader",
            opportunity_type="informal_employment",
            skills_match_score=0.75,
            context_id="gha-urban-2024",
        )
        assert opp.skills_gap == []
        assert opp.data_sources == []
