"""ARQ async worker tasks for background processing."""

from __future__ import annotations

from arq import cron
from loguru import logger


async def process_skill_extraction(ctx: dict, worker_id: str, description: str) -> dict:
    """Background task: extract skills from worker description."""
    logger.info("Processing skill extraction for worker {}", worker_id)

    from packages.llm.chains import skill_extraction_chain

    chain = skill_extraction_chain()
    result = await chain.ainvoke({"worker_description": description})

    import json

    try:
        skills = json.loads(result)
    except json.JSONDecodeError:
        skills = []

    logger.info("Extracted {} skills for worker {}", len(skills), worker_id)
    return {"worker_id": worker_id, "skills": skills}


async def process_opportunity_indexing(ctx: dict, context_id: str) -> dict:
    """Background task: re-index opportunities for a context into Qdrant."""
    logger.info("Re-indexing opportunities for context {}", context_id)
    return {"context_id": context_id, "indexed": 0}


async def startup(ctx: dict) -> None:
    """ARQ worker startup hook."""
    logger.info("ARQ worker starting up")


async def shutdown(ctx: dict) -> None:
    """ARQ worker shutdown hook."""
    logger.info("ARQ worker shutting down")


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [process_skill_extraction, process_opportunity_indexing]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = None  # configured via REDIS_URL env var at runtime
    cron_jobs = [
        cron(process_opportunity_indexing, hour=2, minute=0, run_at_startup=False),
    ]
