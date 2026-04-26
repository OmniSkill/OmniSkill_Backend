"""ConfigLoader: reads, validates, caches, and hot-reloads country configs."""

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import ValidationError
from redis.asyncio import Redis

from packages.config.models import CountryConfig
from packages.core.exceptions import ConfigValidationError

_DEFAULT_CONFIG_DIR = Path("configs/countries")
_DEFAULT_REDIS_TTL = 300  # 5 minutes


class ConfigLoader:
    """Loads country configs from JSON files with Redis caching and hot-reload."""

    def __init__(
        self,
        config_dir: str | Path = _DEFAULT_CONFIG_DIR,
        redis: Redis | None = None,
        redis_ttl: int = _DEFAULT_REDIS_TTL,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._redis = redis
        self._redis_ttl = redis_ttl
        self._local_cache: dict[str, CountryConfig] = {}
        self._watch_task: asyncio.Task[None] | None = None

    def _redis_key(self, context_id: str) -> str:
        return f"unmapped:config:{context_id}"

    def _config_path(self, context_id: str) -> Path:
        return self._config_dir / f"{context_id}.json"

    async def get(self, context_id: str) -> CountryConfig:
        """Return a validated CountryConfig, checking local cache → Redis → disk."""
        if context_id in self._local_cache:
            return self._local_cache[context_id]

        if self._redis is not None:
            cached = await self._redis.get(self._redis_key(context_id))
            if cached is not None:
                config = CountryConfig.model_validate_json(cached)
                self._local_cache[context_id] = config
                return config

        config = await self._load_from_disk(context_id)
        self._local_cache[context_id] = config

        if self._redis is not None:
            await self._redis.set(
                self._redis_key(context_id),
                config.model_dump_json(),
                ex=self._redis_ttl,
            )

        return config

    async def _load_from_disk(self, context_id: str) -> CountryConfig:
        """Read and validate a config file from disk."""
        path = self._config_path(context_id)
        if not path.exists():
            raise ConfigValidationError(
                context_id, f"Config file not found: {path}"
            )

        raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(context_id, f"Invalid JSON: {exc}") from exc

        try:
            return CountryConfig.model_validate(data)
        except ValidationError as exc:
            raise ConfigValidationError(
                context_id, f"Validation errors:\n{exc}"
            ) from exc

    async def list_available(self) -> list[str]:
        """Return context_ids for all JSON files in the config directory."""
        if not self._config_dir.exists():
            return []
        files = await asyncio.to_thread(
            lambda: list(self._config_dir.glob("*.json"))
        )
        return [f.stem for f in sorted(files)]

    def invalidate(self, context_id: str) -> None:
        """Remove a context_id from the local in-memory cache."""
        self._local_cache.pop(context_id, None)

    async def invalidate_all(self) -> None:
        """Clear both local and Redis caches."""
        self._local_cache.clear()
        if self._redis is not None:
            keys = [
                self._redis_key(cid)
                for cid in await self.list_available()
            ]
            if keys:
                await self._redis.delete(*keys)

    async def start_watching(self) -> None:
        """Start a background task that watches for config file changes."""
        if self._watch_task is not None:
            return

        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info("Config hot-reload watcher started for {}", self._config_dir)

    async def stop_watching(self) -> None:
        """Stop the background file watcher."""
        if self._watch_task is not None:
            self._watch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watch_task
            self._watch_task = None
            logger.info("Config hot-reload watcher stopped")

    async def _watch_loop(self) -> None:
        """Watch the config directory for changes and invalidate caches."""
        from watchfiles import awatch

        async for changes in awatch(self._config_dir):
            for _change_type, path_str in changes:
                path = Path(path_str)
                if path.suffix != ".json":
                    continue
                context_id = path.stem
                logger.info("Config file changed: {} – invalidating cache", context_id)
                self.invalidate(context_id)
                if self._redis is not None:
                    await self._redis.delete(self._redis_key(context_id))
                try:
                    config = await self._load_from_disk(context_id)
                    self._local_cache[context_id] = config
                    logger.info("Config reloaded successfully: {}", context_id)
                except ConfigValidationError as exc:
                    logger.error("Hot-reload validation failed: {}", exc)
