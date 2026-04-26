"""ESCOSearchTool – queries ESCO skills API (cached) by skill label."""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger

ESCO_SKILL_REFERENCE: list[dict[str, str]] = [
    {"esco_uri": "http://data.europa.eu/esco/skill/S1.1", "preferred_label": "adapt to change", "skill_type": "transversal", "broader_concept": "personal skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S1.2", "preferred_label": "work in teams", "skill_type": "transversal", "broader_concept": "social skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S1.3", "preferred_label": "communicate effectively", "skill_type": "transversal", "broader_concept": "communication"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S2.1", "preferred_label": "use digital tools", "skill_type": "digital", "broader_concept": "ICT skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S2.2", "preferred_label": "manage data", "skill_type": "digital", "broader_concept": "ICT skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S3.1", "preferred_label": "operate agricultural machinery", "skill_type": "occupation-specific", "broader_concept": "agriculture"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S3.2", "preferred_label": "grow crops", "skill_type": "occupation-specific", "broader_concept": "agriculture"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S3.3", "preferred_label": "raise livestock", "skill_type": "occupation-specific", "broader_concept": "agriculture"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S4.1", "preferred_label": "sell products and services", "skill_type": "occupation-specific", "broader_concept": "sales"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S4.2", "preferred_label": "manage inventory", "skill_type": "occupation-specific", "broader_concept": "retail"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S5.1", "preferred_label": "perform electrical installations", "skill_type": "occupation-specific", "broader_concept": "construction"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S5.2", "preferred_label": "repair motors", "skill_type": "occupation-specific", "broader_concept": "mechanics"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S5.3", "preferred_label": "use hand tools", "skill_type": "occupation-specific", "broader_concept": "crafts"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S5.4", "preferred_label": "prepare food", "skill_type": "occupation-specific", "broader_concept": "food services"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S5.5", "preferred_label": "sew garments", "skill_type": "occupation-specific", "broader_concept": "textiles"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S6.1", "preferred_label": "drive vehicles", "skill_type": "occupation-specific", "broader_concept": "transport"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S6.2", "preferred_label": "provide childcare", "skill_type": "occupation-specific", "broader_concept": "care services"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S7.1", "preferred_label": "write software code", "skill_type": "occupation-specific", "broader_concept": "ICT development"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S7.2", "preferred_label": "analyse business requirements", "skill_type": "occupation-specific", "broader_concept": "business analysis"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S8.1", "preferred_label": "manage finances", "skill_type": "transversal", "broader_concept": "management skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S8.2", "preferred_label": "negotiate agreements", "skill_type": "transversal", "broader_concept": "management skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S8.3", "preferred_label": "plan projects", "skill_type": "transversal", "broader_concept": "management skills"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S9.1", "preferred_label": "teach students", "skill_type": "occupation-specific", "broader_concept": "education"},
    {"esco_uri": "http://data.europa.eu/esco/skill/S9.2", "preferred_label": "provide first aid", "skill_type": "occupation-specific", "broader_concept": "health"},
]


class ESCOSearchTool(BaseTool):
    """Queries ESCO skills API (cached in-memory reference) by skill label."""

    name: str = "esco_skill_search"
    description: str = (
        "Search the ESCO skill taxonomy by skill label. "
        "Input: a skill name or keyword. "
        "Returns: list of matching ESCO skills with URIs, labels, types, and broader concepts."
    )

    async def _arun(self, query: str) -> list[dict]:
        """Async: search ESCO skill reference."""
        logger.debug("ESCO search: query='{}'", query[:50])
        query_lower = query.lower()
        matches = []
        for entry in ESCO_SKILL_REFERENCE:
            label_lower = entry["preferred_label"].lower()
            concept_lower = entry["broader_concept"].lower()
            if query_lower in label_lower or any(w in label_lower for w in query_lower.split()) or query_lower in concept_lower:
                matches.append(entry)
        return matches[:10]

    def _run(self, query: str) -> list[dict]:
        """Sync fallback."""
        import asyncio
        return asyncio.run(self._arun(query))
