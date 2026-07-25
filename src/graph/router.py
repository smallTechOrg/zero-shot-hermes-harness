"""Query router — prefer DuckDB cache, fall back to MsSQL live, log latency + audit."""
from __future__ import annotations

import os
import time
from typing import Any

from src.db.duckdb_store import query as cache_query
from src.db.mssql_connector import live_query
from src.observability.events import get_logger

logger = get_logger("query_router")


class QueryRouter:
    """Minimal execution surface to centralize caching vs live query execution."""

    def __init__(self, session_id: str, data_source: str = "cache") -> None:
        self.session_id = session_id
        self.data_source = data_source
        self.audit: list[dict[str, Any]] = []

    def execute(self, sql: str, max_rows: int = 10_000) -> dict[str, Any]:
        start = time.perf_counter()
        source = self.data_source
        result: dict[str, Any] | None = None
        error: str | None = None

        try:
            if self.data_source == "cache":
                result = cache_query(self.session_id, sql, max_rows=max_rows)
            elif self.data_source == "live":
                result = live_query(sql, max_rows=max_rows)
            else:
                raise ValueError(f"Unknown data_source {self.data_source!r}")
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            latency_ms = int((time.perf_counter() - start) * 1000)
            self.audit.append(
                {
                    "sql": sql,
                    "source": source,
                    "latency_ms": latency_ms,
                    "row_count": 0,
                    "error": error,
                }
            )
            raise RuntimeError(error) from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        self.audit.append(
            {
                "sql": sql,
                "source": source,
                "latency_ms": latency_ms,
                "row_count": result.get("row_count", 0),
                "error": None,
            }
        )
        return result

    def summary(self) -> dict[str, Any]:
        if not self.audit:
            return {"queries": 0, "total_latency_ms": 0, "sources": {}}
        total_latency = sum(item["latency_ms"] for item in self.audit)
        sources: dict[str, int] = {}
        for item in self.audit:
            sources[item["source"]] = sources.get(item["source"], 0) + 1
        return {"queries": len(self.audit), "total_latency_ms": total_latency, "sources": sources}
