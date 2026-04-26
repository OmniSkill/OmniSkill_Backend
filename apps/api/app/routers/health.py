"""Health-check and readiness endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "unmapped-api"}


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, str | bool]:
    redis_ok = False
    config_ok = False

    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        try:
            await redis.ping()
            redis_ok = True
        except Exception:
            pass

    loader = getattr(request.app.state, "config_loader", None)
    if loader is not None:
        try:
            available = await loader.list_available()
            config_ok = len(available) > 0
        except Exception:
            pass

    return {
        "status": "ready" if (redis_ok or redis is None) and config_ok else "degraded",
        "redis": redis_ok,
        "config_loader": config_ok,
    }
