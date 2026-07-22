"""Query audit log for Phase 3."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import TEXT, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class QueryAuditLog(Base):
    __tablename__ = "query_audit_log"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    user: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    action: Mapped[str] = mapped_column(TEXT, nullable=False, default="query")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
