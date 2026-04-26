"""Gemini model factories via LangChain wrappers."""

from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from packages.llm.settings import LLMSettings


@lru_cache(maxsize=1)
def _settings() -> LLMSettings:
    return LLMSettings()


def get_gemini_pro() -> ChatGoogleGenerativeAI:
    """Return a LangChain-wrapped Gemini 1.5 Pro instance."""
    s = _settings()
    return ChatGoogleGenerativeAI(
        model=s.gemini_model_pro,
        google_api_key=s.google_api_key,
        temperature=s.llm_temperature,
        max_retries=s.llm_max_retries,
    )


def get_gemini_flash() -> ChatGoogleGenerativeAI:
    """Return a LangChain-wrapped Gemini 1.5 Flash instance (fast / cheap)."""
    s = _settings()
    return ChatGoogleGenerativeAI(
        model=s.gemini_model_flash,
        google_api_key=s.google_api_key,
        temperature=s.llm_temperature,
        max_retries=s.llm_max_retries,
    )
