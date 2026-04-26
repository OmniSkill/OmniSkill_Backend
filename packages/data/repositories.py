"""Async repository implementations backed by SQLAlchemy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.data.models import OpportunityRecord, WorkerRecord


class OpportunitySQLRepository:
    """Async CRUD for opportunities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> OpportunityRecord | None:
        return await self._session.get(OpportunityRecord, id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[OpportunityRecord]:
        stmt = select(OpportunityRecord).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, record: OpportunityRecord) -> OpportunityRecord:
        self._session.add(record)
        await self._session.flush()
        return record

    async def search_by_context(
        self, context_id: str, *, limit: int = 20
    ) -> list[OpportunityRecord]:
        stmt = (
            select(OpportunityRecord)
            .where(OpportunityRecord.context_id == context_id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, id: UUID) -> bool:
        record = await self.get(id)
        if record is None:
            return False
        await self._session.delete(record)
        return True


class WorkerSQLRepository:
    """Async CRUD for worker profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> WorkerRecord | None:
        return await self._session.get(WorkerRecord, id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[WorkerRecord]:
        stmt = select(WorkerRecord).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, record: WorkerRecord) -> WorkerRecord:
        self._session.add(record)
        await self._session.flush()
        return record

    async def delete(self, id: UUID) -> bool:
        record = await self.get(id)
        if record is None:
            return False
        await self._session.delete(record)
        return True
