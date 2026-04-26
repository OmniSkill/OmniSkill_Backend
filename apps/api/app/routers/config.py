"""Configuration management endpoints."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.app.auth.dependencies import get_token_payload
from apps.api.app.schemas.auth import TokenPayload
from apps.api.app.schemas.config import SwitchContextRequest, SwitchContextResponse
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


@router.post("/switch", response_model=SwitchContextResponse)
async def switch_context(
    request: Request,
    body: SwitchContextRequest,
    token: TokenPayload = Depends(get_token_payload),
) -> SwitchContextResponse:
    """Switch the active country context for this session."""
    start = time.perf_counter()
    loader = _loader(request)
    try:
        config = await loader.get(body.context_id)
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SwitchContextResponse(
        context_id=config.context_id,
        country=config.country,
        region_type=config.region_type,
        status="active",
        response_time_ms=(time.perf_counter() - start) * 1000,
    )


@router.get("/contexts/{context_id}", response_model=CountryConfig)
async def get_context(context_id: str, request: Request) -> CountryConfig:
    """Retrieve a validated country configuration."""
    loader = _loader(request)
    try:
        return await loader.get(context_id)
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
