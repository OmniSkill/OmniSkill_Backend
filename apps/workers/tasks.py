"""ARQ async worker tasks – profile generation via LangGraph agent orchestrator."""

from __future__ import annotations

import json

from arq import cron
from loguru import logger
from redis.asyncio import Redis

from packages.llm.settings import LLMSettings

_PROFILE_RESULT_TTL = 86400  # 24h


async def run_profile_generation(
    ctx: dict,
    intake_data: dict,
    country_config: dict,
    profile_id: str,
    trace_id: str = "",
) -> dict:
    """Background task: run the full LangGraph analysis pipeline and store result in Redis."""
    logger.info("Worker: starting profile generation profile_id={}", profile_id[:8])

    redis: Redis = ctx.get("redis")

    await _publish_event(redis, profile_id, "started", {"step": "validate_intake"})

    try:
        from apps.agents.orchestrator import run_analysis_pipeline

        result = await run_analysis_pipeline(
            intake_data=intake_data,
            country_config=country_config,
            trace_id=trace_id,
            profile_id=profile_id,
        )

        profile_data = result.get("generated_profile", {})
        errors = result.get("errors", [])

        if redis:
            await redis.set(
                f"profile:{profile_id}",
                json.dumps(profile_data),
                ex=_PROFILE_RESULT_TTL,
            )

        await _publish_event(redis, profile_id, "completed", {
            "step": "generate_profile",
            "error_count": len(errors),
        })

        logger.info("Worker: profile generation complete profile_id={}", profile_id[:8])
        return {"profile_id": profile_id, "status": "completed", "errors": errors}

    except Exception as exc:
        logger.exception("Worker: profile generation failed profile_id={}", profile_id[:8])

        await _publish_event(redis, profile_id, "failed", {
            "step": "unknown",
            "error": str(exc),
        })

        if redis:
            await redis.set(
                f"profile:{profile_id}",
                json.dumps({"error": str(exc), "status": "failed"}),
                ex=_PROFILE_RESULT_TTL,
            )

        return {"profile_id": profile_id, "status": "failed", "error": str(exc)}


async def process_opportunity_indexing(ctx: dict, context_id: str = "default") -> dict:
    """Background task: re-index opportunities for a context into Qdrant."""
    logger.info("Re-indexing opportunities for context {}", context_id)
    return {"context_id": context_id, "indexed": 0}


async def _publish_event(
    redis: Redis | None,
    profile_id: str,
    event_type: str,
    data: dict,
) -> None:
    """Publish a node-completion event to Redis pubsub for WebSocket streaming."""
    if redis is None:
        return
    try:
        message = json.dumps({"event": event_type, "profile_id": profile_id, **data})
        await redis.publish(f"profile_events:{profile_id}", message)
    except Exception:
        logger.debug("Failed to publish event for profile {}", profile_id[:8])


async def startup(ctx: dict) -> None:
    """ARQ worker startup: init Redis connection."""
    logger.info("ARQ worker starting up")
    settings = LLMSettings()
    ctx["redis"] = Redis.from_url(settings.redis_url, decode_responses=True)


async def shutdown(ctx: dict) -> None:
    """ARQ worker shutdown: close Redis."""
    logger.info("ARQ worker shutting down")
    redis = ctx.get("redis")
    if redis:
        await redis.aclose()


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_profile_generation, process_opportunity_indexing]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = None
    cron_jobs = [
        cron(process_opportunity_indexing, hour=2, minute=0, run_at_startup=False),
    ]
