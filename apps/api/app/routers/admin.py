"""Admin-only endpoints."""

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from apps.api.app.auth.dependencies import require_role
from apps.api.app.schemas.admin import PipelineStatusResponse
from apps.api.app.schemas.auth import TokenPayload

router = APIRouter()


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
async def pipeline_status(
    context_id: str = "default",
    token: TokenPayload = Depends(require_role("admin")),
) -> PipelineStatusResponse:
    """Return the status of the most recent pipeline run (admin only)."""
    start = time.perf_counter()

    # TODO: query Prefect API for pipeline run status

    return PipelineStatusResponse(
        pipeline_name="unmapped-data-pipeline",
        status="unknown",
        last_run=datetime.now(UTC),
        records_processed=0,
        context_id=context_id,
        response_time_ms=(time.perf_counter() - start) * 1000,
    )
