"""SQLAlchemy ORM models (async-first)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class OpportunityRecord(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="")
    wage_min_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    wage_max_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    automation_risk: Mapped[float] = mapped_column(Float, default=0.5)
    skills_required: Mapped[dict] = mapped_column(JSONB, default=dict)
    context_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class WorkerRecord(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    country: Mapped[str] = mapped_column(String(10), nullable=False)
    region: Mapped[str] = mapped_column(String(200), default="")
    education_level: Mapped[str] = mapped_column(String(100), default="")
    years_experience: Mapped[int] = mapped_column(default=0)
    skills: Mapped[dict] = mapped_column(JSONB, default=dict)
    preferred_types: Mapped[list] = mapped_column(ARRAY(String), default=list)
    context_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
