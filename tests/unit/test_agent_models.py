"""Unit tests for agent output Pydantic models."""

from apps.agents.models import (
    AgentNodeError,
    EconSignal,
    GeneratedProfile,
    MatchedOpportunity,
    OccupationMatch,
    PortabilityMetadata,
    RiskAssessment,
    RiskScore,
    SkillClusterOutput,
    SkillsProfile,
    UpskillingPath,
)


class TestAgentModels:
    def test_occupation_match(self) -> None:
        match = OccupationMatch(
            isco_code="5221", title="Shopkeepers", confidence=0.85
        )
        assert match.automation_risk == 0.5
        assert match.esco_uri is None

    def test_skills_profile(self) -> None:
        profile = SkillsProfile(
            occupation_matches=[
                OccupationMatch(isco_code="5221", title="Shopkeepers", confidence=0.8)
            ],
            skill_clusters=[
                SkillClusterOutput(
                    cluster_name="Market Trading",
                    skills=["sell products", "manage inventory"],
                    proficiency_avg=3.0,
                )
            ],
            plain_language_summary="You have market trading skills.",
            total_experience_years=5.0,
        )
        assert len(profile.occupation_matches) == 1
        assert len(profile.skill_clusters) == 1
        assert profile.total_experience_years == 5.0

    def test_risk_score(self) -> None:
        score = RiskScore(
            skill_name="Shopkeeper",
            isco_code="5221",
            frey_osborne_score=0.47,
            calibrated_score=0.16,
            risk_category="low",
        )
        assert score.risk_category == "low"

    def test_risk_assessment(self) -> None:
        assessment = RiskAssessment(
            per_skill_risks=[
                RiskScore(
                    skill_name="Shopkeeper", isco_code="5221",
                    frey_osborne_score=0.47, calibrated_score=0.16,
                    risk_category="low",
                )
            ],
            durable_skills=["Shopkeeper"],
            overall_risk_score=0.16,
            narrative_explanation="Your skills are relatively safe from automation.",
        )
        assert len(assessment.durable_skills) == 1

    def test_upskilling_path(self) -> None:
        path = UpskillingPath(
            target_isco="2512",
            target_title="Software Developers",
            skills_gap=["write software code"],
            estimated_training_months=12,
        )
        assert path.growth_potential == "stable"

    def test_econ_signal(self) -> None:
        signal = EconSignal(
            indicator="youth_unemployment_rate",
            value=7.8,
            unit="%",
            source="ILO",
            country_code="GHA",
        )
        assert signal.trend == "stable"

    def test_matched_opportunity(self) -> None:
        opp = MatchedOpportunity(
            opportunity_id="abc123",
            title="Market trader – informal",
            opportunity_type="informal_employment",
            match_score=0.72,
        )
        assert opp.skills_gap == []

    def test_generated_profile(self) -> None:
        profile = GeneratedProfile(
            intake_id="intake-1",
            context_id="gha-urban-2024",
            plain_language_summary="Your profile is ready.",
        )
        assert profile.profile_id is not None
        assert profile.context_id == "gha-urban-2024"

    def test_portability_metadata(self) -> None:
        meta = PortabilityMetadata()
        assert meta.isco_version == "ISCO-08"
        assert meta.esco_version == "1.1.1"

    def test_agent_node_error(self) -> None:
        err = AgentNodeError(
            node_name="map_skills",
            error_type="tool_error",
            message="ISCO lookup timed out",
        )
        assert not err.is_fatal
