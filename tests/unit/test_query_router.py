"""QueryRouter unit tests — cache-first, live fallback, latency/audit."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.graph.router import QueryRouter


class FakeCacheQuery:
    @staticmethod
    def __call__(session_id: str, sql: str, *, max_rows: int = 10_000) -> dict:
        return {
            "columns": ["id", "name"],
            "rows": [[1, "alpha"], [2, "beta"]],
            "row_count": 2,
        }


class FakeLiveQuery:
    @staticmethod
    def __call__(sql: str, *, max_rows: int = 10_000) -> dict:
        return {
            "columns": ["id", "name"],
            "rows": [[3, "gamma"]],
            "row_count": 1,
        }


def test_cache_execution_records_latency_and_audit():
    router = QueryRouter(session_id="s1", data_source="cache")
    with patch("src.graph.router.cache_query", FakeCacheQuery()):
        out = router.execute("SELECT 1")
    assert out["row_count"] == 2
    assert out["columns"] == ["id", "name"]
    summary = router.summary()
    assert summary["queries"] == 1
    assert summary["sources"].get("cache") == 1
    assert isinstance(summary["total_latency_ms"], int)


def test_live_fallback_execution():
    router = QueryRouter(session_id="s1", data_source="live")
    with patch("src.graph.router.live_query", FakeLiveQuery()):
        out = router.execute("SELECT 1")
    assert out["row_count"] == 1
    summary = router.summary()
    assert summary["sources"].get("live") == 1


def test_unknown_data_source_raises():
    router = QueryRouter(session_id="s1", data_source="banana")
    with pytest.raises(RuntimeError):
        router.execute("SELECT 1")


def test_cache_error_records_audit_and_reraises():
    def boom(*args, **kwargs):
        raise RuntimeError("cache down")

    router = QueryRouter(session_id="s1", data_source="cache")
    with patch("src.graph.router.cache_query", side_effect=boom):
        with pytest.raises(RuntimeError, match="cache down"):
            router.execute("SELECT bad")
    summary = router.summary()
    assert summary["queries"] == 1
    assert summary["total_latency_ms"] >= 0
