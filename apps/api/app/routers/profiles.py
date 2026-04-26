"""Profile generation and retrieval endpoints."""

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.app.auth.dependencies import get_current_context, get_token_payload
from apps.api.app.ratelimit import limiter
from apps.api.app.schemas.auth import TokenPayload
from apps.api.app.schemas.profiles import GenerateProfileRequest, ProfileResponse

router = APIRouter()


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    context_id: str = Depends(get_current_context),
    token: TokenPayload = Depends(get_token_payload),
) -> ProfileResponse:
    """Fetch a generated worker profile by ID."""
    raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")


@router.post("/generate", response_model=ProfileResponse)
@limiter.limit("5/minute")
async def generate_profile(
    request: Request,
    body: GenerateProfileRequest,
    context_id: str = Depends(get_current_context),
    token: TokenPayload = Depends(get_token_payload),
) -> ProfileResponse:
    """Trigger async profile generation from a submitted intake form."""
    start = time.perf_counter()

    profile_id = uuid4()

    # TODO: enqueue LangGraph agent via ARQ

    return ProfileResponse(
        profile_id=profile_id,
        created_at=datetime.now(UTC),
        context_id=context_id,
        response_time_ms=(time.perf_counter() - start) * 1000,
    )
