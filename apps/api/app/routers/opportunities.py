"""Opportunity listing and matching endpoints."""

import time

from fastapi import APIRouter, Depends, Query

from apps.api.app.auth.dependencies import get_current_context, get_token_payload
from apps.api.app.schemas.auth import TokenPayload
from apps.api.app.schemas.opportunities import OpportunityListResponse

router = APIRouter()


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    context_id: str = Depends(get_current_context),
    token: TokenPayload = Depends(get_token_payload),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OpportunityListResponse:
    """List matched opportunities for the current context."""
    start = time.perf_counter()

    # TODO: query database + vector store for matched opportunities

    return OpportunityListResponse(
        opportunities=[],
        total=0,
        context_id=context_id,
        response_time_ms=(time.perf_counter() - start) * 1000,
    )
