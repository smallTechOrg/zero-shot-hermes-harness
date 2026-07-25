"""
Session domain models for analyst workspaces.

A session groups a chat thread with one or more CSV uploads and an
optional live DB connection so analysts can switch data sources.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    cache = "cache"
    live = "live"
    hybrid = "hybrid"


class SessionState(str, Enum):
    active = "active"
    archived = "archived"


class SessionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    default_data_source: DataSource = DataSource.cache


class SessionSummary(BaseModel):
    session_id: str
    name: str
    state: SessionState
    default_data_source: DataSource
    table_count: int = 0
    last_activity: str | None = None
