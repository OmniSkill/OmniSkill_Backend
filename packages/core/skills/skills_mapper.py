from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from math import sqrt
from random import randint
from re import sub

from .models import (
    CountryConfig,
    ESCOSkill,
    OccupationMatch,
    SkillCluster,
    WorkExperience,
)


class SkillsMapper:
    """Pure business-logic mapper for deriving occupation and skill signals."""

    _CLUSTER_ORDER = (
        "Technical",
        "Digital",
        "Communication",
        "Business",
        "Self-directed",
    )

    _KEYWORD_MAP: dict[str, tuple[str, ...]] = {
        "Technical": (
            "repair",
            "technician",
            "mechanic",
            "installation",
            "machine",
            "electrical",
            "engineering",
            "quality control",
            "maintenance",
            "tool",
        ),
        "Digital": (
            "software",
            "digital",
            "data",
            "computer",
            "coding",
            "programming",
            "it",
            "system",
            "network",
            "database",
        ),
        "Communication": (
            "communication",
            "facilitation",
            "writing",
            "translation",
            "language",
            "presentation",
            "customer",
            "negotiation",
            "public speaking",
        ),
        "Business": (
            "finance",
            "accounting",
            "sales",
            "management",
            "operations",
            "logistics",
            "strategy",
            "planning",
            "compliance",
            "marketing",
        ),
        "Self-directed": (
            "learning",
            "self",
            "initiative",
            "adapt",
            "problem solving",
            "independent",
            "mentoring",
            "leadership",
            "resilience",
        ),
    }

    def map_to_isco(
        self, experiences: list[WorkExperience], context: CountryConfig
    ) -> list[OccupationMatch]:
        """Return top ISCO-08 occupation matches using TF-IDF cosine similarity."""
        if not context.isco_occupations:
            return []

        profile_text = self._build_profile_text(experiences)
        profile_tfidf = self._tfidf_vector(
            profile_text, [occ.description for occ in context.isco_occupations]
        )

        normalized_education = self._normalize_education(experiences, context)

        scored: list[OccupationMatch] = []
        for occ in context.isco_occupations:
            occupation_tfidf = self._tfidf_vector(
                occ.description,
                [profile_text]
                + [
                    candidate.description
                    for candidate in context.isco_occupations
                    if candidate.isco_code != occ.isco_code
                ],
            )
            similarity = self._cosine_similarity(profile_tfidf, occupation_tfidf)
            scored.append(
                OccupationMatch(
                    isco_code=occ.isco_code,
                    title=occ.title,
                    confidence=round(similarity, 4),
                    normalized_education_level=normalized_education,
                )
            )

        scored.sort(key=lambda item: item.confidence, reverse=True)
        return scored[:3]

    def build_skill_clusters(
        self, isco_codes: list[str], esco_skills: list[ESCOSkill]
    ) -> list[SkillCluster]:
        """Group ESCO skills into fixed business clusters."""
        grouped: dict[str, list[ESCOSkill]] = {name: [] for name in self._CLUSTER_ORDER}
        isco_hint = " ".join(isco_codes)

        for skill in esco_skills:
            cluster_name = self._infer_cluster(skill, isco_hint)
            grouped[cluster_name].append(skill)

        clusters: list[SkillCluster] = []
        for cluster_name in self._CLUSTER_ORDER:
            skills = grouped[cluster_name]
            score = self._cluster_score(skills, isco_codes)
            clusters.append(
                SkillCluster(
                    name=cluster_name,
                    skills=skills,
                    proficiency_level=self._proficiency_from_score(score),
                    cluster_score=score,
                )
            )

        return clusters

    def generate_profile_id(self, country_code: str) -> str:
        """Generate profile ID in the required canonical format."""
        iso3 = sub(r"[^A-Za-z]", "", country_code.upper())[:3].ljust(3, "X")
        year = datetime.now(timezone.utc).year
        seq = randint(0, 99999)
        return f"UNMAPPED-{iso3}-{year}-{seq:05d}"

    def _build_profile_text(self, experiences: list[WorkExperience]) -> str:
        return " ".join(
            f"{exp.title} {exp.description} {exp.education_level}" for exp in experiences
        )

    def _normalize_education(
        self, experiences: list[WorkExperience], context: CountryConfig
    ) -> str:
        education_levels = [
            exp.education_level.strip().lower()
            for exp in experiences
            if exp.education_level.strip()
        ]
        if not education_levels:
            return ""
        mapped = [
            context.education_taxonomy.get(level, level.title())
            for level in education_levels
        ]
        return Counter(mapped).most_common(1)[0][0]

    def _tfidf_vector(self, document: str, corpus: list[str]) -> dict[str, float]:
        tokenized_doc = self._tokenize(document)
        if not tokenized_doc:
            return {}
        tokenized_corpus = [self._tokenize(text) for text in corpus]
        all_docs = tokenized_corpus + [tokenized_doc]
        n_docs = len(all_docs)

        term_freq = Counter(tokenized_doc)
        max_freq = max(term_freq.values())
        tfidf: dict[str, float] = {}
        for term, freq in term_freq.items():
            tf = freq / max_freq
            docs_with_term = sum(1 for doc in all_docs if term in doc)
            idf = 1.0 + (n_docs / (1 + docs_with_term))
            tfidf[term] = tf * idf
        return tfidf

    def _tokenize(self, text: str) -> list[str]:
        normalized = sub(r"[^a-z0-9\s]", " ", text.lower())
        return [token for token in normalized.split() if len(token) > 1]

    def _cosine_similarity(
        self, left: dict[str, float], right: dict[str, float]
    ) -> float:
        if not left or not right:
            return 0.0
        common_terms = set(left) & set(right)
        dot = sum(left[term] * right[term] for term in common_terms)
        left_norm = sqrt(sum(value * value for value in left.values()))
        right_norm = sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (left_norm * right_norm)))

    def _infer_cluster(self, skill: ESCOSkill, isco_hint: str) -> str:
        if skill.category:
            mapped = skill.category.strip().title()
            if mapped in self._CLUSTER_ORDER:
                return mapped
        if skill.is_digital:
            return "Digital"

        descriptor = f"{skill.name.lower()} {skill.category.lower()} {isco_hint.lower()}"
        for cluster_name, keywords in self._KEYWORD_MAP.items():
            if any(keyword in descriptor for keyword in keywords):
                return cluster_name
        return "Self-directed"

    def _cluster_score(self, skills: list[ESCOSkill], isco_codes: list[str]) -> float:
        if not skills:
            return 0.0
        base = min(1.0, len(skills) / 8.0)
        isco_factor = 0.15 if isco_codes else 0.0
        return round(min(1.0, base + isco_factor), 4)

    def _proficiency_from_score(self, score: float) -> str:
        if score >= 0.8:
            return "Advanced"
        if score >= 0.5:
            return "Intermediate"
        if score > 0.0:
            return "Basic"
        return "None"
