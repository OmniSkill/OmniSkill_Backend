"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.data.settings import DataSettings

_settings = DataSettings()

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.echo_sql,
    pool_size=_settings.pool_size,
    max_overflow=_settings.max_overflow,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency-injectable async session generator."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
