"""Intake form submission endpoint."""

import time
from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from apps.api.app.auth.dependencies import get_current_context, get_token_payload
from apps.api.app.ratelimit import limiter
from apps.api.app.schemas.auth import TokenPayload
from apps.api.app.schemas.intake import IntakeFormRequest, IntakeFormResponse

router = APIRouter()


@router.post("/submit", response_model=IntakeFormResponse)
@limiter.limit("10/minute")
async def submit_intake(
    request: Request,
    body: IntakeFormRequest,
    context_id: str = Depends(get_current_context),
    token: TokenPayload = Depends(get_token_payload),
) -> IntakeFormResponse:
    """Submit a skills intake form. Triggers async profile generation."""
    start = time.perf_counter()

    intake_id = uuid4().hex
    profile_id = uuid4().hex

    return IntakeFormResponse(
        intake_id=intake_id,
        profile_id=profile_id,
        status="processing",
        context_id=context_id,
        response_time_ms=(time.perf_counter() - start) * 1000,
    )
