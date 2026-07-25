"""DB routes — connection management and cache synchronization."""
from __future__ import annotations

import os
from pydantic import BaseModel

from fastapi import APIRouter

from src.api._common import api_error, ok
from src.db.cache_sync import refresh_cache, warmup_cache
from src.db.mssql_connector import (
    live_query,
    live_schema,
    test_connection,
)

router = APIRouter()


class ConnectRequest(BaseModel):
    connection_string: str


@router.post("/db/connect")
def connect_db(req: ConnectRequest) -> dict:
    """Set the MsSQL connection string for this runtime and test the connection."""
    os.environ["AGENT_MSSQL_CONNECTION_STRING"] = req.connection_string
    try:
        info = test_connection()
    except Exception as exc:
        raise api_error("db_connect_failed", str(exc), 500) from exc
    return ok(info)


@router.get("/db/test-connection")
def test_db() -> dict:
    try:
        info = test_connection()
    except Exception as exc:
        raise api_error("db_unavailable", str(exc), 503) from exc
    return ok(info)


@router.get("/db/schema")
def db_schema() -> dict:
    try:
        tables = live_schema()
    except Exception as exc:
        raise api_error("db_unavailable", str(exc), 503) from exc
    return ok({"tables": tables})


@router.post("/db/refresh-cache")
def refresh_cache_endpoint(session_id: str = "sess1") -> dict:
    """Synchronize all live MsSQL tables into the DuckDB cache for this session."""
    try:
        result = refresh_cache(session_id)
    except Exception as exc:
        raise api_error("cache_sync_failed", str(exc), 500) from exc
    return ok(result)


@router.post("/db/warmup")
def warmup_cache_endpoint(session_id: str = "sess1") -> dict:
    """Refresh cache and pre-create lightweight aggregate views for low-latency queries."""
    try:
        result = warmup_cache(session_id)
    except Exception as exc:
        raise api_error("cache_warmup_failed", str(exc), 500) from exc
    return ok(result)
