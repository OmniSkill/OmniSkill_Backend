"""Unit tests for agent tools – taxonomy, ESCO, and signal lookup."""

import pytest

from apps.agents.tools.esco_search import ESCOSearchTool
from apps.agents.tools.signal_lookup import SignalLookupTool
from apps.agents.tools.taxonomy_lookup import TaxonomyLookupTool


class TestTaxonomyLookupTool:
    @pytest.fixture
    def tool(self) -> TaxonomyLookupTool:
        return TaxonomyLookupTool()

    async def test_lookup_farming(self, tool: TaxonomyLookupTool) -> None:
        results = await tool._arun("farming crops rice")
        assert len(results) > 0
        codes = [r["isco_code"] for r in results]
        assert any(c.startswith("6") or c.startswith("9") for c in codes)

    async def test_lookup_driving(self, tool: TaxonomyLookupTool) -> None:
        results = await tool._arun("driving taxi car")
        assert len(results) > 0
        assert any(r["isco_code"].startswith("8") for r in results)

    async def test_lookup_construction(self, tool: TaxonomyLookupTool) -> None:
        results = await tool._arun("building construction")
        assert len(results) > 0

    async def test_lookup_no_match(self, tool: TaxonomyLookupTool) -> None:
        results = await tool._arun("xyzzynonexistent")
        assert results == []

    async def test_results_capped_at_10(self, tool: TaxonomyLookupTool) -> None:
        results = await tool._arun("workers labourers")
        assert len(results) <= 10


class TestESCOSearchTool:
    @pytest.fixture
    def tool(self) -> ESCOSearchTool:
        return ESCOSearchTool()

    async def test_search_digital(self, tool: ESCOSearchTool) -> None:
        results = await tool._arun("digital tools")
        assert len(results) > 0
        labels = [r["preferred_label"] for r in results]
        assert any("digital" in label for label in labels)

    async def test_search_agriculture(self, tool: ESCOSearchTool) -> None:
        results = await tool._arun("agriculture")
        assert len(results) > 0

    async def test_search_no_match(self, tool: ESCOSearchTool) -> None:
        results = await tool._arun("quantumphysics")
        assert results == []


class TestSignalLookupTool:
    @pytest.fixture
    def tool(self) -> SignalLookupTool:
        return SignalLookupTool()

    async def test_lookup_ghana(self, tool: SignalLookupTool) -> None:
        results = await tool._arun(country_code="GHA")
        assert len(results) >= 5
        indicators = [r["indicator"] for r in results]
        assert "sector_employment_growth_pct" in indicators
        assert "wage_floor_estimate" in indicators

    async def test_lookup_bangladesh(self, tool: SignalLookupTool) -> None:
        results = await tool._arun(country_code="BGD")
        assert len(results) >= 5

    async def test_lookup_filtered(self, tool: SignalLookupTool) -> None:
        results = await tool._arun(
            country_code="GHA", signal_type="youth_unemployment_rate"
        )
        assert len(results) == 1
        assert results[0]["value"] == 7.8

    async def test_lookup_unknown_country(self, tool: SignalLookupTool) -> None:
        results = await tool._arun(country_code="ZZZ")
        assert results == []
