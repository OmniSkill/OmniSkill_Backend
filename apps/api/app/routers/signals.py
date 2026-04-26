"""Econometric signal endpoints."""

import time

from fastapi import APIRouter, Depends, Request

from apps.api.app.auth.dependencies import get_token_payload
from apps.api.app.ratelimit import limiter
from apps.api.app.schemas.auth import TokenPayload
from apps.api.app.schemas.signals import SignalsResponse

router = APIRouter()


@router.get("/{context_id}", response_model=SignalsResponse)
@limiter.limit("60/minute")
async def get_signals(
    request: Request,
    context_id: str,
    token: TokenPayload = Depends(get_token_payload),
) -> SignalsResponse:
    """Return econometric signals for a given country context."""
    start = time.perf_counter()

    # TODO: fetch signals from data pipeline output

    return SignalsResponse(
        context_id=context_id,
        signals=[],
        response_time_ms=(time.perf_counter() - start) * 1000,
    )
