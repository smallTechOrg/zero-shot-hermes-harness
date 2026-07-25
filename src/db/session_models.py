"""
Session and upload metadata persistence.

Uses the same SQLite/SQLAlchemy database as RunRow so sessions
survive server restarts and can be queried by the frontend.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import TEXT, Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    default_data_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="cache"
    )
    table_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class UploadRecordRow(Base):
    __tablename__ = "upload_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(260), nullable=False)
    table_name: Mapped[str] = mapped_column(String(120), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False, default="text/csv")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")
    message: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
