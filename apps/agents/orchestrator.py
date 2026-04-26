"""LangGraph state machine orchestrator for UNMAPPED worker analysis pipeline."""

from __future__ import annotations

import time
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph
from loguru import logger

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


class AgentState(TypedDict, total=False):
    """State flowing through the LangGraph analysis pipeline."""

    intake_data: dict[str, Any]
    context: dict[str, Any]
    skills_profile: dict[str, Any] | None
    risk_assessment: dict[str, Any] | None
    opportunities: list[dict[str, Any]] | None
    econometric_signals: list[dict[str, Any]] | None
    errors: list[dict[str, Any]]
    current_step: str
    trace_id: str
    profile_id: str
    generated_profile: dict[str, Any] | None


FREY_OSBORNE_REFERENCE: dict[str, float] = {
    "6111": 0.58, "6112": 0.54, "6114": 0.56, "6121": 0.49, "6130": 0.52,
    "5221": 0.47, "5223": 0.52, "5243": 0.71, "5246": 0.67,
    "7411": 0.15, "7412": 0.24, "7233": 0.30, "7231": 0.25,
    "7115": 0.35, "7121": 0.40, "7126": 0.35, "7511": 0.60, "7512": 0.38,
    "7531": 0.79, "7532": 0.81, "7533": 0.83,
    "8322": 0.68, "8331": 0.67, "8332": 0.64,
    "9211": 0.87, "9212": 0.85, "9312": 0.88, "9313": 0.85,
    "9411": 0.81, "9412": 0.74,
    "5311": 0.08, "5322": 0.05, "5141": 0.11, "5142": 0.12,
    "2511": 0.04, "2512": 0.04, "2513": 0.06, "2514": 0.04,
    "2431": 0.23, "2310": 0.03, "2320": 0.03, "2330": 0.02, "2341": 0.01,
    "3256": 0.26, "2240": 0.10,
    "1311": 0.15, "1321": 0.17, "1420": 0.19,
}


def _make_error(node: str, error_type: str, message: str, fatal: bool = False) -> dict:
    return AgentNodeError(
        node_name=node, error_type=error_type, message=message, is_fatal=fatal
    ).model_dump(mode="json")


async def validate_intake(state: AgentState) -> AgentState:
    """NODE 1: Validate intake data against country config education taxonomy."""
    start = time.perf_counter()
    node = "validate_intake"
    logger.info("[{}] Starting intake validation (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    intake = state.get("intake_data", {})
    ctx = state.get("context", {})

    education_taxonomy: dict = ctx.get("education_taxonomy", {})
    education_level = intake.get("education_level", "")
    education_isced = education_taxonomy.get(education_level, "")

    if not education_isced:
        closest = list(education_taxonomy.keys())
        if not closest:
            education_isced = "ISCED-unknown"
        else:
            education_isced = education_taxonomy.get(closest[0], "ISCED-0")
            errors.append(_make_error(
                node, "warning",
                f"education_level '{education_level}' not in taxonomy, defaulted to '{closest[0]}'"
            ))

    intake["education_isced"] = education_isced

    region_type = intake.get("region_type", "")
    valid_regions = ["urban_formal", "urban_informal", "rural_agricultural", "custom"]
    if region_type not in valid_regions:
        intake["region_type"] = ctx.get("region_type", "custom")
        errors.append(_make_error(
            node, "warning",
            f"region_type '{region_type}' normalised to '{intake['region_type']}'"
        ))

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Completed in {:.1f}ms", node, duration_ms)

    return {
        **state,
        "intake_data": intake,
        "errors": errors,
        "current_step": "validate_intake_done",
    }


def should_continue_after_validation(state: AgentState) -> str:
    """Conditional edge: continue to map_skills or end on fatal errors."""
    errors = state.get("errors", [])
    fatal = [e for e in errors if e.get("is_fatal")]
    if fatal:
        return "end"
    return "map_skills"


async def map_skills(state: AgentState) -> AgentState:
    """NODE 2: Map worker experiences to ISCO-08 codes and ESCO skills."""
    start = time.perf_counter()
    node = "map_skills"
    logger.info("[{}] Starting skills mapping (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    intake = state.get("intake_data", {})

    from apps.agents.tools.esco_search import ESCOSearchTool
    from apps.agents.tools.taxonomy_lookup import TaxonomyLookupTool

    taxonomy_tool = TaxonomyLookupTool()
    esco_tool = ESCOSearchTool()

    work_experiences = intake.get("work_experiences", [])
    all_occupation_matches: list[dict] = []
    all_skill_clusters: list[dict] = []
    total_years = 0.0

    for exp in work_experiences:
        title = exp.get("title", "")
        description = exp.get("description", "")
        sector = exp.get("sector", "")
        years = exp.get("years", 0)
        total_years += years

        query = f"{title} {sector} {description}".strip()
        if not query:
            continue

        try:
            isco_matches = await taxonomy_tool._arun(query)
            for match in isco_matches[:3]:
                all_occupation_matches.append(OccupationMatch(
                    isco_code=match["isco_code"],
                    title=match["title"],
                    description=match.get("description", ""),
                    confidence=match["match_score"],
                ).model_dump(mode="json"))
        except Exception as exc:
            errors.append(_make_error(node, "tool_error", f"ISCO lookup failed: {exc}"))

        try:
            esco_matches = await esco_tool._arun(query)
            if esco_matches:
                cluster = SkillClusterOutput(
                    cluster_name=f"{title} Skills",
                    skills=[m["preferred_label"] for m in esco_matches[:5]],
                    esco_codes=[m["esco_uri"] for m in esco_matches[:5]],
                    proficiency_avg=min(years + 1, 5.0),
                    source="intake_mapping",
                ).model_dump(mode="json")
                all_skill_clusters.append(cluster)
        except Exception as exc:
            errors.append(_make_error(node, "tool_error", f"ESCO search failed: {exc}"))

    digital_skills = intake.get("digital_skills", [])
    if digital_skills:
        digital_cluster = SkillClusterOutput(
            cluster_name="Digital Skills",
            skills=digital_skills,
            proficiency_avg=2.0,
            source="self_reported",
        ).model_dump(mode="json")
        all_skill_clusters.append(digital_cluster)

    seen_codes = set()
    deduped_matches = []
    for m in all_occupation_matches:
        if m["isco_code"] not in seen_codes:
            seen_codes.add(m["isco_code"])
            deduped_matches.append(m)

    summary_parts = []
    if deduped_matches:
        top = deduped_matches[:3]
        summary_parts.append(
            "Your experience matches occupations like "
            + ", ".join(m["title"] for m in top) + "."
        )
    if all_skill_clusters:
        summary_parts.append(
            "Key skill areas: " + ", ".join(c["cluster_name"] for c in all_skill_clusters) + "."
        )

    skills_profile = SkillsProfile(
        occupation_matches=[OccupationMatch(**m) for m in deduped_matches],
        skill_clusters=[SkillClusterOutput(**c) for c in all_skill_clusters],
        plain_language_summary=" ".join(summary_parts),
        total_experience_years=total_years,
    ).model_dump(mode="json")

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Mapped {} occupations, {} clusters in {:.1f}ms",
                node, len(deduped_matches), len(all_skill_clusters), duration_ms)

    return {
        **state,
        "skills_profile": skills_profile,
        "errors": errors,
        "current_step": "map_skills_done",
    }


async def assess_risk(state: AgentState) -> AgentState:
    """NODE 3: Assess automation risk for matched occupations."""
    start = time.perf_counter()
    node = "assess_risk"
    logger.info("[{}] Starting risk assessment (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    skills_profile = state.get("skills_profile", {})
    ctx = state.get("context", {})
    calibration = ctx.get("automation_calibration", 0.5)

    occupation_matches = skills_profile.get("occupation_matches", [])

    per_skill_risks: list[dict] = []
    at_risk_tasks: list[str] = []
    durable_skills: list[str] = []

    for match in occupation_matches:
        isco = match.get("isco_code", "")
        raw_score = FREY_OSBORNE_REFERENCE.get(isco, 0.5)
        calibrated = raw_score * calibration

        category = "low"
        if calibrated >= 0.7:
            category = "very_high"
        elif calibrated >= 0.5:
            category = "high"
        elif calibrated >= 0.3:
            category = "medium"

        per_skill_risks.append(RiskScore(
            skill_name=match.get("title", isco),
            isco_code=isco,
            frey_osborne_score=raw_score,
            calibrated_score=calibrated,
            risk_category=category,
        ).model_dump(mode="json"))

        if calibrated >= 0.5:
            at_risk_tasks.append(f"{match.get('title', isco)} (calibrated: {calibrated:.0%})")
        else:
            durable_skills.append(match.get("title", isco))

    upskilling_paths = _suggest_upskilling(occupation_matches, calibration)

    risk_scores = [r.get("calibrated_score", 0.5) for r in per_skill_risks]
    overall = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5

    narrative = _build_risk_narrative(per_skill_risks, at_risk_tasks, durable_skills, calibration)
    projection = (
        f"Between 2025 and 2035, approximately {int(overall * 100)}% of your current "
        f"tasks may be affected by automation, adjusted for the pace of technology "
        f"adoption in this region (calibration factor: {calibration})."
    )

    assessment = RiskAssessment(
        per_skill_risks=[RiskScore(**r) for r in per_skill_risks],
        at_risk_tasks=at_risk_tasks,
        durable_skills=durable_skills,
        adjacent_upskilling_paths=upskilling_paths,
        overall_risk_score=overall,
        narrative_explanation=narrative,
        projection_2025_2035=projection,
    ).model_dump(mode="json")

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Assessed {} occupations, overall risk {:.0%} in {:.1f}ms",
                node, len(per_skill_risks), overall, duration_ms)

    return {
        **state,
        "risk_assessment": assessment,
        "errors": errors,
        "current_step": "assess_risk_done",
    }


def _suggest_upskilling(
    matches: list[dict], calibration: float
) -> list[UpskillingPath]:
    """Suggest adjacent occupations with lower automation risk."""
    low_risk = {
        code: score for code, score in FREY_OSBORNE_REFERENCE.items()
        if score * calibration < 0.3
    }
    if not low_risk:
        return []

    from apps.agents.tools.taxonomy_lookup import ISCO_08_REFERENCE

    code_to_title = {e["isco_code"]: e["title"] for e in ISCO_08_REFERENCE}
    current_codes = {m.get("isco_code", "") for m in matches}

    suggestions = []
    for code, _raw_score in sorted(low_risk.items(), key=lambda x: x[1])[:3]:
        if code in current_codes:
            continue
        suggestions.append(UpskillingPath(
            target_isco=code,
            target_title=code_to_title.get(code, f"ISCO {code}"),
            skills_gap=["to be determined by detailed analysis"],
            estimated_training_months=6,
            growth_potential="growing",
        ))

    return suggestions[:3]


def _build_risk_narrative(
    risks: list[dict],
    at_risk: list[str],
    durable: list[str],
    calibration: float,
) -> str:
    """Build a plain-language risk narrative."""
    parts = []
    if durable:
        parts.append(
            f"Your strongest, most automation-resistant skills include: "
            f"{', '.join(durable[:3])}."
        )
    if at_risk:
        parts.append(
            f"Some of your current work areas face higher automation risk: "
            f"{', '.join(at_risk[:3])}."
        )
    parts.append(
        f"These risk scores have been adjusted for your region's technology adoption "
        f"pace (calibration factor: {calibration:.2f}). Actual impact depends on "
        f"local infrastructure, policy, and investment."
    )
    return " ".join(parts)


async def fetch_signals(state: AgentState) -> AgentState:
    """NODE 4: Fetch econometric signals for the country context (pure DB query)."""
    start = time.perf_counter()
    node = "fetch_signals"
    logger.info("[{}] Fetching econometric signals (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    ctx = state.get("context", {})
    country_code = ctx.get("country", "")

    from apps.agents.tools.signal_lookup import SignalLookupTool

    signal_tool = SignalLookupTool()

    try:
        raw_signals = await signal_tool._arun(country_code=country_code)
        signals = [
            EconSignal(
                indicator=s["indicator"],
                value=s["value"],
                unit=s["unit"],
                source=s["source"],
                source_dataset=s.get("source_dataset", ""),
                vintage_year=s.get("vintage_year"),
                country_code=s.get("country_code", country_code),
                confidence=s.get("confidence", 0.5),
            ).model_dump(mode="json")
            for s in raw_signals
        ]
    except Exception as exc:
        signals = []
        errors.append(_make_error(node, "tool_error", f"Signal lookup failed: {exc}"))

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Fetched {} signals in {:.1f}ms", node, len(signals), duration_ms)

    return {
        **state,
        "econometric_signals": signals,
        "errors": errors,
        "current_step": "fetch_signals_done",
    }


async def match_opportunities(state: AgentState) -> AgentState:
    """NODE 5: Match skills profile to opportunities using vector similarity + re-ranking."""
    start = time.perf_counter()
    node = "match_opportunities"
    logger.info("[{}] Matching opportunities (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    skills_profile = state.get("skills_profile", {})
    ctx = state.get("context", {})
    signals = state.get("econometric_signals", [])

    allowed_types = ctx.get("opportunity_types", [])

    occupation_matches = skills_profile.get("occupation_matches", [])
    skill_clusters = skills_profile.get("skill_clusters", [])

    all_skills = set()
    for cluster in skill_clusters:
        for skill in cluster.get("skills", []):
            all_skills.add(skill.lower())

    sector_growth = 0.0
    wage_floor = 0.0
    for s in signals:
        if s.get("indicator") == "sector_employment_growth_pct":
            sector_growth = s.get("value", 0)
        if s.get("indicator") == "wage_floor_estimate":
            wage_floor = s.get("value", 0)

    matched: list[dict] = []
    for occ in occupation_matches:
        base_score = occ.get("confidence", 0.5)
        growth_weight = 1.0 + (sector_growth / 100.0)
        wage_weight = 1.0 if wage_floor > 200 else 0.8

        final_score = min(base_score * growth_weight * wage_weight, 1.0)

        for opp_type in allowed_types[:2]:
            matched.append(MatchedOpportunity(
                opportunity_id=uuid4().hex[:12],
                title=f"{occ.get('title', 'Unknown')} – {opp_type}",
                opportunity_type=opp_type,
                match_score=round(final_score, 3),
                sector_growth_pct=sector_growth,
                wage_range=(wage_floor * 0.8, wage_floor * 1.2) if wage_floor else None,
                skills_gap=[],
                data_sources=["ILOSTAT", "World Bank"],
                re_rank_explanation=(
                    f"Base match {base_score:.0%} × growth {growth_weight:.2f} "
                    f"× wage viability {wage_weight:.2f} = {final_score:.0%}"
                ),
            ).model_dump(mode="json"))

    matched.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    matched = matched[:10]

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Matched {} opportunities in {:.1f}ms", node, len(matched), duration_ms)

    return {
        **state,
        "opportunities": matched,
        "errors": errors,
        "current_step": "match_opportunities_done",
    }


async def generate_profile(state: AgentState) -> AgentState:
    """NODE 6: Assemble the final GeneratedProfile from all pipeline outputs."""
    start = time.perf_counter()
    node = "generate_profile"
    logger.info("[{}] Generating final profile (trace={})", node, state.get("trace_id", ""))

    errors = list(state.get("errors", []))
    intake = state.get("intake_data", {})
    ctx = state.get("context", {})
    skills_profile = state.get("skills_profile", {})
    risk_assessment = state.get("risk_assessment")
    signals = state.get("econometric_signals", [])
    opportunities = state.get("opportunities", [])

    profile_id = state.get("profile_id", uuid4().hex)

    summary = skills_profile.get("plain_language_summary", "")
    if risk_assessment:
        summary += " " + risk_assessment.get("narrative_explanation", "")

    profile = GeneratedProfile(
        profile_id=profile_id,
        intake_id=intake.get("intake_id", ""),
        context_id=ctx.get("context_id", ""),
        occupation_matches=[OccupationMatch(**m) for m in skills_profile.get("occupation_matches", [])],
        skill_clusters=[SkillClusterOutput(**c) for c in skills_profile.get("skill_clusters", [])],
        risk_assessment=RiskAssessment(**risk_assessment) if risk_assessment else None,
        econometric_signals=[EconSignal(**s) for s in signals],
        matched_opportunities=[MatchedOpportunity(**o) for o in opportunities],
        plain_language_summary=summary,
        portability_metadata=PortabilityMetadata(
            portable_skills_count=len(skills_profile.get("skill_clusters", [])),
            cross_sector_matches=len(set(
                m.get("opportunity_type", "") for m in opportunities
            )),
        ),
        data_vintage=ctx.get("wage_vintage"),
    )

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("[{}] Profile {} generated in {:.1f}ms", node, profile_id[:8], duration_ms)

    return {
        **state,
        "current_step": "generate_profile_done",
        "errors": errors,
        "generated_profile": profile.model_dump(mode="json"),
    }


def build_orchestrator_graph() -> StateGraph:
    """Construct the full LangGraph state machine for worker analysis."""
    graph = StateGraph(AgentState)

    graph.add_node("validate_intake", validate_intake)
    graph.add_node("map_skills", map_skills)
    graph.add_node("assess_risk", assess_risk)
    graph.add_node("fetch_signals", fetch_signals)
    graph.add_node("match_opportunities", match_opportunities)
    graph.add_node("generate_profile", generate_profile)

    graph.set_entry_point("validate_intake")
    graph.add_conditional_edges(
        "validate_intake",
        should_continue_after_validation,
        {"map_skills": "map_skills", "end": END},
    )
    graph.add_edge("map_skills", "assess_risk")
    graph.add_edge("assess_risk", "fetch_signals")
    graph.add_edge("fetch_signals", "match_opportunities")
    graph.add_edge("match_opportunities", "generate_profile")
    graph.add_edge("generate_profile", END)

    return graph


async def run_analysis_pipeline(
    intake_data: dict,
    country_config: dict,
    trace_id: str | None = None,
    profile_id: str | None = None,
) -> dict:
    """Entry point: compile and run the full analysis graph."""
    graph = build_orchestrator_graph()
    compiled = graph.compile()

    initial_state: AgentState = {
        "intake_data": intake_data,
        "context": country_config,
        "skills_profile": None,
        "risk_assessment": None,
        "opportunities": None,
        "econometric_signals": None,
        "errors": [],
        "current_step": "start",
        "trace_id": trace_id or uuid4().hex,
        "profile_id": profile_id or uuid4().hex,
    }

    logger.info("Starting analysis pipeline (trace={})", initial_state["trace_id"])
    result = await compiled.ainvoke(initial_state)
    logger.info("Analysis pipeline complete (trace={})", initial_state["trace_id"])

    return result
