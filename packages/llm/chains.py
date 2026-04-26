"""Reusable LangChain chains for common UNMAPPED tasks."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from packages.llm.gemini import get_gemini_flash, get_gemini_pro

SKILL_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert labour-market analyst specialising in LMICs. "
            "Extract structured skill profiles from the worker description below. "
            "Return valid JSON array of objects with keys: name, esco_code (nullable), "
            "proficiency_level (1-5).",
        ),
        ("human", "{worker_description}"),
    ]
)

OPPORTUNITY_MATCHING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an LMIC labour-market matching engine. Given a worker skill profile "
            "and a list of opportunities, rank the top matches. Consider automation risk "
            "calibrated by factor {calibration}. Return JSON array of {{opportunity_id, "
            "match_score, rationale}}.",
        ),
        ("human", "Worker skills: {skills}\n\nOpportunities: {opportunities}"),
    ]
)


def skill_extraction_chain():
    """Chain that extracts skills from a free-text worker description."""
    return SKILL_EXTRACTION_PROMPT | get_gemini_flash() | StrOutputParser()


def opportunity_matching_chain():
    """Chain that matches a worker profile to opportunities."""
    return OPPORTUNITY_MATCHING_PROMPT | get_gemini_pro() | StrOutputParser()
