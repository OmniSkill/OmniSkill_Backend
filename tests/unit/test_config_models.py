"""Unit tests for country config Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.config.models import CountryConfig


class TestCountryConfig:
    def test_valid_config(self, sample_gha_config: CountryConfig) -> None:
        assert sample_gha_config.context_id == "gha-urban-2024"
        assert sample_gha_config.country == "GHA"
        assert sample_gha_config.automation_calibration == 0.35

    def test_context_id_pattern_rejects_bad_format(self) -> None:
        with pytest.raises(ValidationError, match="context_id"):
            CountryConfig(
                context_id="INVALID",
                country="GHA",
                region_type="urban_informal",
                language="en",
                automation_calibration=0.5,
                opportunity_types=["self_employment"],
                wage_vintage=2024,
            )

    def test_automation_calibration_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CountryConfig(
                context_id="gha-urban-2024",
                country="GHA",
                region_type="urban_informal",
                language="en",
                automation_calibration=1.5,
                opportunity_types=["self_employment"],
                wage_vintage=2024,
            )

    def test_opportunity_types_must_be_nonempty(self) -> None:
        with pytest.raises(ValidationError):
            CountryConfig(
                context_id="gha-urban-2024",
                country="GHA",
                region_type="urban_informal",
                language="en",
                automation_calibration=0.5,
                opportunity_types=[],
                wage_vintage=2024,
            )

    def test_language_validation(self) -> None:
        with pytest.raises(ValidationError, match="language"):
            CountryConfig(
                context_id="gha-urban-2024",
                country="GHA",
                region_type="urban_informal",
                language="x",
                automation_calibration=0.5,
                opportunity_types=["self_employment"],
                wage_vintage=2024,
            )

    def test_region_type_literal(self) -> None:
        with pytest.raises(ValidationError):
            CountryConfig(
                context_id="gha-urban-2024",
                country="GHA",
                region_type="invalid_type",
                language="en",
                automation_calibration=0.5,
                opportunity_types=["self_employment"],
                wage_vintage=2024,
            )
