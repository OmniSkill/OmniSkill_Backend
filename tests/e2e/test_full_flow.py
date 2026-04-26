"""End-to-end test stubs – require running infrastructure."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="E2E tests require running Docker infrastructure")


class TestFullPipelineFlow:
    async def test_config_load_to_pipeline(self) -> None:
        """Verify config loading → pipeline trigger → data storage."""

    async def test_worker_analysis_flow(self) -> None:
        """Verify worker description → skill extraction → opportunity matching."""
