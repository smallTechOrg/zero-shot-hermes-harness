"""
SQLAlchemy 2.0 declarative models (Mapped types).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import TIMESTAMP, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
 return str(uuid4())


def _now() -> datetime:
 return datetime.now(timezone.utc)


class Base(DeclarativeBase):
 pass


class RunRow(Base):
 """One agent run: input → output, with status + error for observability."""

 __tablename__ = "runs"

 id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
 status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
 input_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
 instruction: Mapped[str] = mapped_column(Text, nullable=False, default="")
 output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
 provider: Mapped[str | None] = mapped_column(Text, nullable=True)
 model: Mapped[str | None] = mapped_column(Text, nullable=True)
 latency_ms: Mapped[str | None] = mapped_column(Text, nullable=True)
 error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
 created_at: Mapped[datetime] = mapped_column(
 TIMESTAMP(timezone=True), nullable=False, default=_now
 )
 updated_at: Mapped[datetime] = mapped_column(
 TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now
 )
