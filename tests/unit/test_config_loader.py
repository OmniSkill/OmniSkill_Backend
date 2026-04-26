"""Unit tests for ConfigLoader (disk-only, no Redis)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.config.loader import ConfigLoader
from packages.config.models import CountryConfig
from packages.core.exceptions import ConfigValidationError


class TestConfigLoader:
    async def test_load_valid_config(self, config_loader: ConfigLoader) -> None:
        config = await config_loader.get("gha-urban-2024")
        assert isinstance(config, CountryConfig)
        assert config.context_id == "gha-urban-2024"
        assert config.country == "GHA"

    async def test_load_bgd_config(self, config_loader: ConfigLoader) -> None:
        config = await config_loader.get("bgd-rural-2024")
        assert config.country == "BGD"
        assert config.region_type == "rural_agricultural"

    async def test_missing_config_raises(self, config_loader: ConfigLoader) -> None:
        with pytest.raises(ConfigValidationError, match="not found"):
            await config_loader.get("zzz-missing-2024")

    async def test_invalid_json_raises(self, config_dir: Path) -> None:
        bad_file = config_dir / "bad-config-2024.json"
        bad_file.write_text("not json at all", encoding="utf-8")

        loader = ConfigLoader(config_dir=config_dir)
        with pytest.raises(ConfigValidationError, match="Invalid JSON"):
            await loader.get("bad-config-2024")

    async def test_validation_error_raises(self, config_dir: Path) -> None:
        bad_file = config_dir / "bad-schema-2024.json"
        bad_file.write_text(
            json.dumps({"context_id": "INVALID", "country": "X"}),
            encoding="utf-8",
        )

        loader = ConfigLoader(config_dir=config_dir)
        with pytest.raises(ConfigValidationError, match="Validation errors"):
            await loader.get("bad-schema-2024")

    async def test_list_available(self, config_loader: ConfigLoader) -> None:
        available = await config_loader.list_available()
        assert "gha-urban-2024" in available
        assert "bgd-rural-2024" in available

    async def test_invalidate_clears_cache(self, config_loader: ConfigLoader) -> None:
        await config_loader.get("gha-urban-2024")
        assert "gha-urban-2024" in config_loader._local_cache

        config_loader.invalidate("gha-urban-2024")
        assert "gha-urban-2024" not in config_loader._local_cache

    async def test_caches_after_first_load(self, config_loader: ConfigLoader) -> None:
        config1 = await config_loader.get("gha-urban-2024")
        config2 = await config_loader.get("gha-urban-2024")
        assert config1 is config2
