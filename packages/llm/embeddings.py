"""Gemini text embedding support for vector search."""

from __future__ import annotations

import google.generativeai as genai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from packages.llm.settings import LLMSettings


def _configure() -> str:
    s = LLMSettings()
    if s.google_api_key:
        genai.configure(api_key=s.google_api_key)
    return s.gemini_embedding_model


@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    reraise=True,
)
async def embed_text(text: str) -> list[float]:
    """Embed a single text string using Gemini text-embedding-004."""
    import asyncio

    model = _configure()
    result = await asyncio.to_thread(
        genai.embed_content,
        model=model,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    reraise=True,
)
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in batch."""
    import asyncio

    model = _configure()
    result = await asyncio.to_thread(
        genai.embed_content,
        model=model,
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]
