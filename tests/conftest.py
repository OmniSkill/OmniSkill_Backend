"""Shared test fixtures for the UNMAPPED test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.config.loader import ConfigLoader
from packages.config.models import CountryConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CONFIGS_DIR = Path(__file__).parent.parent / "configs" / "countries"


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Return a temp directory pre-populated with test config files."""
    import shutil

    for src in CONFIGS_DIR.glob("*.json"):
        shutil.copy(src, tmp_path / src.name)

    return tmp_path


@pytest.fixture
def config_loader(config_dir: Path) -> ConfigLoader:
    """Return a ConfigLoader pointing at the temp config dir (no Redis)."""
    return ConfigLoader(config_dir=config_dir, redis=None)


@pytest.fixture
def sample_gha_config() -> CountryConfig:
    """Return a pre-built Ghana urban config for unit tests."""
    return CountryConfig(
        context_id="gha-urban-2024",
        country="GHA",
        region_type="urban_informal",
        language="en",
        automation_calibration=0.35,
        opportunity_types=["informal_employment", "self_employment"],
        wage_vintage=2024,
        education_taxonomy={"primary": "ISCED-1", "shs": "ISCED-3"},
    )
