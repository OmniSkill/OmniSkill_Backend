"""LangGraph agent definitions for UNMAPPED labour-market analysis."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema for the UNMAPPED analysis agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    context_id: str
    worker_description: str
    extracted_skills: list[dict]
    matched_opportunities: list[dict]
    analysis_complete: bool


async def extract_skills(state: AgentState) -> AgentState:
    """Node: extract skills from worker description using Gemini Flash."""
    from packages.llm.chains import skill_extraction_chain

    chain = skill_extraction_chain()
    result = await chain.ainvoke({"worker_description": state["worker_description"]})

    import json

    try:
        skills = json.loads(result)
    except json.JSONDecodeError:
        skills = []

    return {**state, "extracted_skills": skills}


async def match_opportunities(state: AgentState) -> AgentState:
    """Node: match extracted skills to available opportunities."""
    from packages.llm.chains import opportunity_matching_chain

    chain = opportunity_matching_chain()
    result = await chain.ainvoke(
        {
            "skills": str(state["extracted_skills"]),
            "opportunities": "[]",
            "calibration": "0.6",
        }
    )

    import json

    try:
        matches = json.loads(result)
    except json.JSONDecodeError:
        matches = []

    return {**state, "matched_opportunities": matches, "analysis_complete": True}


def build_analysis_graph() -> StateGraph:
    """Construct the LangGraph state graph for worker analysis."""
    graph = StateGraph(AgentState)

    graph.add_node("extract_skills", extract_skills)
    graph.add_node("match_opportunities", match_opportunities)

    graph.set_entry_point("extract_skills")
    graph.add_edge("extract_skills", "match_opportunities")
    graph.add_edge("match_opportunities", END)

    return graph
