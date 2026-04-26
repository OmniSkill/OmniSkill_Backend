"""Unit tests for core domain models."""

from __future__ import annotations

from packages.core.enums import OpportunityType, RegionType
from packages.core.models import Opportunity, SkillProfile, WorkerProfile


class TestCoreModels:
    def test_skill_profile_defaults(self) -> None:
        skill = SkillProfile(name="welding")
        assert skill.proficiency_level == 1
        assert skill.source == "self_reported"
        assert skill.esco_code is None

    def test_opportunity_creation(self) -> None:
        opp = Opportunity(
            title="Market trader",
            opportunity_type=OpportunityType.INFORMAL_EMPLOYMENT,
            automation_risk=0.2,
        )
        assert opp.title == "Market trader"
        assert opp.automation_risk == 0.2
        assert opp.id is not None

    def test_worker_profile(self) -> None:
        worker = WorkerProfile(
            name="Kwame Asante",
            country="GHA",
            skills=[SkillProfile(name="carpentry", proficiency_level=4)],
            preferred_opportunity_types=[OpportunityType.SELF_EMPLOYMENT],
        )
        assert len(worker.skills) == 1
        assert worker.skills[0].proficiency_level == 4

    def test_region_type_values(self) -> None:
        assert RegionType.URBAN_FORMAL == "urban_formal"
        assert RegionType.RURAL_AGRICULTURAL == "rural_agricultural"

    def test_opportunity_type_values(self) -> None:
        assert OpportunityType.GIG_WORK == "gig_work"
        assert OpportunityType.COOPERATIVE == "cooperative"
