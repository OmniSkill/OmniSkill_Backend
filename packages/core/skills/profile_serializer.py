from __future__ import annotations

from .models import SkillsProfile


class ProfileSerializer:
    def to_portable_json(self, profile: SkillsProfile) -> dict:
        return {
            "@context": {
                "isco": "https://isco.org/isco-08/schema#",
                "esco": "https://data.europa.eu/esco/model#",
                "profile": "https://unmapped.global/schema/skills-profile#",
            },
            "@type": "profile:SkillsProfile",
            "profile_id": profile.profile_id,
            "country_code": profile.country_code,
            "metadata": {
                "generated_at": profile.generated_at.isoformat(),
                "context_id": profile.context_id,
                "isco_version": profile.isco_version,
                "esco_version": profile.esco_version,
            },
            "occupation_matches": [
                {
                    "isco_code": match.isco_code,
                    "title": match.title,
                    "confidence": round(match.confidence, 4),
                    "normalized_education_level": match.normalized_education_level,
                }
                for match in profile.occupation_matches
            ],
            "skill_clusters": [
                {
                    "name": cluster.name,
                    "skills": [
                        {"id": skill.id, "name": skill.name, "category": skill.category}
                        for skill in cluster.skills
                    ],
                    "proficiency_level": cluster.proficiency_level,
                    "cluster_score": round(cluster.cluster_score, 4),
                }
                for cluster in profile.skill_clusters
            ],
            "languages": profile.languages,
            "recognition_countries_count": profile.recognition_countries_count,
        }

    def to_plain_language(self, profile: SkillsProfile, language: str) -> str:
        # Language switch is intentionally deterministic until localization tables are added.
        _ = language
        top_match = profile.occupation_matches[0] if profile.occupation_matches else None
        technical_cluster = next(
            (
                cluster
                for cluster in profile.skill_clusters
                if cluster.name.lower() == "technical"
            ),
            None,
        )
        self_directed_cluster = next(
            (
                cluster
                for cluster in profile.skill_clusters
                if cluster.name.lower() == "self-directed"
            ),
            None,
        )

        if top_match:
            skill_phrase = (
                "strong technical skills"
                if technical_cluster and technical_cluster.cluster_score >= 0.6
                else "practical work skills"
            )
            sentence_1 = (
                f"You have {skill_phrase} equivalent to {top_match.title} "
                f"(ISCO {top_match.isco_code})."
            )
        else:
            sentence_1 = "You have a growing skill profile with transferable work strengths."

        sentence_2 = (
            f"You speak {len(profile.languages)} languages and have demonstrated "
            f"{'self-directed learning' if self_directed_cluster else 'adaptability'}."
        )
        sentence_3 = (
            f"Your skills are recognized in {profile.recognition_countries_count}+ countries."
        )
        return " ".join([sentence_1, sentence_2, sentence_3])
