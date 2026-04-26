from __future__ import annotations

import re
from datetime import datetime

from packages.core.skills.models import (
    CountryConfig,
    ESCOSkill,
    OccupationMatch,
    OccupationReference,
    SkillCluster,
    SkillsProfile,
    WorkExperience,
)
from packages.core.skills.profile_serializer import ProfileSerializer
from packages.core.skills.skills_mapper import SkillsMapper


def _make_context() -> CountryConfig:
    return CountryConfig(
        country_code="gha",
        education_taxonomy={
            "secondary school": "Upper Secondary",
            "high school": "Upper Secondary",
            "diploma": "Post-secondary non-tertiary",
        },
        isco_occupations=[
            OccupationReference(
                isco_code="7421",
                title="Electronics mechanics and servicers",
                description=(
                    "Install repair and maintain electronic equipment, diagnostic tools, "
                    "circuit boards, and communication devices."
                ),
            ),
            OccupationReference(
                isco_code="2512",
                title="Software developers",
                description=(
                    "Design code and test software applications, collaborate in agile teams, "
                    "use version control and debugging practices."
                ),
            ),
            OccupationReference(
                isco_code="5249",
                title="Sales workers not elsewhere classified",
                description=(
                    "Support customers, process transactions, and communicate product value."
                ),
            ),
            OccupationReference(
                isco_code="3322",
                title="Commercial sales representatives",
                description="Negotiate contracts, business development, and account management.",
            ),
        ],
        context_id="context-ghana-2026",
    )


def test_map_to_isco_returns_top_three_ranked_matches() -> None:
    mapper = SkillsMapper()
    context = _make_context()
    experiences = [
        WorkExperience(
            title="Electronics repair apprentice",
            description=(
                "I repair communication devices, diagnose board issues, and maintain "
                "electronic equipment."
            ),
            years=2.0,
            education_level="secondary school",
        )
    ]

    matches = mapper.map_to_isco(experiences, context)

    assert len(matches) == 3
    assert matches[0].isco_code == "7421"
    assert 0.0 <= matches[0].confidence <= 1.0
    assert matches[0].normalized_education_level == "Upper Secondary"
    assert matches[0].confidence >= matches[1].confidence >= matches[2].confidence


def test_build_skill_clusters_groups_all_expected_categories() -> None:
    mapper = SkillsMapper()
    skills = [
        ESCOSkill(id="s1", name="Electrical troubleshooting", category="technical"),
        ESCOSkill(id="s2", name="Spreadsheet analysis", is_digital=True),
        ESCOSkill(id="s3", name="Client communication", category="communication"),
        ESCOSkill(id="s4", name="Budget planning", category="business"),
        ESCOSkill(id="s5", name="Independent learning", category="self-directed"),
    ]

    clusters = mapper.build_skill_clusters(["7421", "2512"], skills)
    by_name: dict[str, SkillCluster] = {c.name: c for c in clusters}

    assert set(by_name) == {
        "Technical",
        "Digital",
        "Communication",
        "Business",
        "Self-directed",
    }
    assert by_name["Digital"].skills[0].id == "s2"
    assert all(0.0 <= c.cluster_score <= 1.0 for c in clusters)
    assert all(c.proficiency_level for c in clusters)


def test_generate_profile_id_matches_spec_format() -> None:
    mapper = SkillsMapper()

    profile_id = mapper.generate_profile_id("gha")

    assert re.fullmatch(r"UNMAPPED-GHA-\d{4}-\d{5}", profile_id)


def test_profile_serializer_outputs_json_ld_and_plain_language() -> None:
    serializer = ProfileSerializer()
    profile = SkillsProfile(
        profile_id="UNMAPPED-GHA-2026-08441",
        country_code="GHA",
        generated_at=datetime(2026, 1, 15, 10, 30, 0),
        context_id="context-ghana-2026",
        occupation_matches=[
            OccupationMatch(
                isco_code="7421",
                title="Electronics mechanics and servicers",
                confidence=0.91,
                normalized_education_level="Upper Secondary",
            )
        ],
        skill_clusters=[
            SkillCluster(
                name="Technical",
                skills=[ESCOSkill(id="s1", name="Diagnostics")],
                proficiency_level="Advanced",
                cluster_score=0.86,
            ),
            SkillCluster(
                name="Self-directed",
                skills=[ESCOSkill(id="s5", name="Independent learning")],
                proficiency_level="Intermediate",
                cluster_score=0.62,
            ),
        ],
        languages=["English", "Twi", "French"],
        recognition_countries_count=42,
    )

    payload = serializer.to_portable_json(profile)
    text = serializer.to_plain_language(profile, "en")

    assert payload["@context"]["isco"] == "https://isco.org/isco-08/schema#"
    assert payload["metadata"]["isco_version"] == "ISCO-08"
    assert payload["metadata"]["esco_version"] == "ESCO v1.1.2"
    assert payload["metadata"]["context_id"] == "context-ghana-2026"
    assert len([s for s in text.split(". ") if s.strip()]) == 3
    assert "ISCO 7421" in text
