"""Configuration management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.config.models import CountryConfig
from packages.core.exceptions import ConfigValidationError

router = APIRouter()


def _loader(request: Request):
    return request.app.state.config_loader


@router.get("/contexts", response_model=list[str])
async def list_contexts(request: Request) -> list[str]:
    """List all available country context IDs."""
    loader = _loader(request)
    return await loader.list_available()


@router.get("/contexts/{context_id}", response_model=CountryConfig)
async def get_context(context_id: str, request: Request) -> CountryConfig:
    """Retrieve a validated country configuration."""
    loader = _loader(request)
    try:
        return await loader.get(context_id)
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/contexts/{context_id}/reload")
async def reload_context(context_id: str, request: Request) -> dict[str, str]:
    """Force-reload a country config from disk."""
    loader = _loader(request)
    loader.invalidate(context_id)
    try:
        await loader.get(context_id)
        return {"status": "reloaded", "context_id": context_id}
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
