"""Unit tests for the LangGraph orchestrator nodes and pipeline."""


from apps.agents.orchestrator import (
    AgentState,
    assess_risk,
    build_orchestrator_graph,
    fetch_signals,
    generate_profile,
    map_skills,
    match_opportunities,
    run_analysis_pipeline,
    should_continue_after_validation,
    validate_intake,
)


def _base_state() -> AgentState:
    return {
        "intake_data": {
            "intake_id": "test-intake-1",
            "education_level": "shs",
            "country": "GHA",
            "region_type": "urban_informal",
            "work_experiences": [
                {"title": "Market trader", "sector": "retail", "years": 3, "description": "Selling goods at Makola Market", "is_formal": False},
                {"title": "Mobile money agent", "sector": "finance", "years": 1, "description": "Processing mobile money transactions", "is_formal": False},
            ],
            "languages": [{"language": "en", "proficiency": "native"}],
            "digital_skills": ["mobile money", "social media"],
            "goals": ["formal employment"],
            "connectivity": "moderate",
        },
        "context": {
            "context_id": "gha-urban-2024",
            "country": "GHA",
            "region_type": "urban_informal",
            "language": "en",
            "automation_calibration": 0.35,
            "opportunity_types": ["informal_employment", "self_employment", "micro_enterprise"],
            "wage_vintage": 2024,
            "education_taxonomy": {
                "no_formal": "ISCED-0",
                "primary": "ISCED-1",
                "jhs": "ISCED-2",
                "shs": "ISCED-3",
                "tvet": "ISCED-4",
                "tertiary": "ISCED-6",
            },
        },
        "skills_profile": None,
        "risk_assessment": None,
        "opportunities": None,
        "econometric_signals": None,
        "errors": [],
        "current_step": "start",
        "trace_id": "test-trace-1",
        "profile_id": "a1b2c3d4e5f6a7b8a1b2c3d4e5f6a7b8",
    }


class TestValidateIntake:
    async def test_validates_known_education_level(self) -> None:
        state = _base_state()
        result = await validate_intake(state)
        assert result["intake_data"]["education_isced"] == "ISCED-3"
        assert result["current_step"] == "validate_intake_done"

    async def test_warns_on_unknown_education_level(self) -> None:
        state = _base_state()
        state["intake_data"]["education_level"] = "unknown_level"
        result = await validate_intake(state)
        assert result["intake_data"]["education_isced"] != ""
        warnings = [e for e in result["errors"] if e.get("error_type") == "warning"]
        assert len(warnings) > 0

    async def test_normalises_invalid_region_type(self) -> None:
        state = _base_state()
        state["intake_data"]["region_type"] = "invalid_region"
        result = await validate_intake(state)
        assert result["intake_data"]["region_type"] == "urban_informal"

    def test_should_continue_after_validation(self) -> None:
        state = _base_state()
        state["errors"] = []
        assert should_continue_after_validation(state) == "map_skills"

    def test_should_stop_on_fatal_error(self) -> None:
        state = _base_state()
        state["errors"] = [{"is_fatal": True, "message": "bad data"}]
        assert should_continue_after_validation(state) == "end"


class TestMapSkills:
    async def test_maps_work_experiences(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        result = await map_skills(state)
        profile = result["skills_profile"]
        assert profile is not None
        assert len(profile["occupation_matches"]) > 0
        assert len(profile["skill_clusters"]) > 0
        assert result["current_step"] == "map_skills_done"

    async def test_includes_digital_skills_cluster(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        result = await map_skills(state)
        cluster_names = [c["cluster_name"] for c in result["skills_profile"]["skill_clusters"]]
        assert "Digital Skills" in cluster_names

    async def test_generates_summary(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        result = await map_skills(state)
        assert len(result["skills_profile"]["plain_language_summary"]) > 0


class TestAssessRisk:
    async def test_produces_risk_scores(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        state = await map_skills(state)
        result = await assess_risk(state)
        assessment = result["risk_assessment"]
        assert assessment is not None
        assert len(assessment["per_skill_risks"]) > 0
        assert 0 <= assessment["overall_risk_score"] <= 1

    async def test_applies_calibration(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        state = await map_skills(state)
        result = await assess_risk(state)
        for risk in result["risk_assessment"]["per_skill_risks"]:
            assert risk["calibrated_score"] <= risk["frey_osborne_score"]


class TestFetchSignals:
    async def test_fetches_ghana_signals(self) -> None:
        state = _base_state()
        result = await fetch_signals(state)
        signals = result["econometric_signals"]
        assert len(signals) >= 5
        indicators = [s["indicator"] for s in signals]
        assert "sector_employment_growth_pct" in indicators
        assert "wage_floor_estimate" in indicators


class TestMatchOpportunities:
    async def test_matches_opportunities(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        state = await map_skills(state)
        state = await fetch_signals(state)
        result = await match_opportunities(state)
        opportunities = result["opportunities"]
        assert len(opportunities) > 0
        for opp in opportunities:
            assert 0 <= opp["match_score"] <= 1

    async def test_respects_allowed_types(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        state = await map_skills(state)
        state = await fetch_signals(state)
        result = await match_opportunities(state)
        allowed = state["context"]["opportunity_types"]
        for opp in result["opportunities"]:
            assert opp["opportunity_type"] in allowed


class TestGenerateProfile:
    async def test_generates_complete_profile(self) -> None:
        state = _base_state()
        state = await validate_intake(state)
        state = await map_skills(state)
        state = await assess_risk(state)
        state = await fetch_signals(state)
        state = await match_opportunities(state)
        result = await generate_profile(state)
        profile = result.get("generated_profile")
        assert profile is not None
        assert profile["profile_id"] is not None
        assert profile["context_id"] == "gha-urban-2024"
        assert len(profile["occupation_matches"]) > 0
        assert len(profile["matched_opportunities"]) > 0


class TestBuildGraph:
    def test_graph_builds(self) -> None:
        graph = build_orchestrator_graph()
        assert graph is not None
        compiled = graph.compile()
        assert compiled is not None


class TestFullPipeline:
    async def test_run_analysis_pipeline(self) -> None:
        state = _base_state()
        result = await run_analysis_pipeline(
            intake_data=state["intake_data"],
            country_config=state["context"],
            trace_id="test-trace",
            profile_id="a1b2c3d4e5f6a7b8a1b2c3d4e5f6a7b8",
        )
        assert result["current_step"] == "generate_profile_done"
        profile = result.get("generated_profile")
        assert profile is not None
        assert profile["context_id"] == "gha-urban-2024"
