"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "unmapped-api"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {"status": "ready"}
