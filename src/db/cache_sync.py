"""Cache synchronization — mirror live MsSQL tables into the local DuckDB cache."""
from __future__ import annotations

import os
import time
from typing import Any

import duckdb
import pandas as pd

from src.db.duckdb_store import init_session, _db_path, _lock
from src.db.mssql_connector import live_schema, live_query


def refresh_cache(session_id: str = "sess1") -> dict:
    """Synchronize all tables from MsSQL into the session's DuckDB cache."""
    init_session(session_id)

    conn_str = os.environ.get("AGENT_MSSQL_CONNECTION_STRING")
    if not conn_str:
        raise ConnectionError(
            "AGENT_MSSQL_CONNECTION_STRING environment variable not set. "
            "Set it in .env or via the /api/v1/db/connect endpoint."
        )

    try:
        tables = live_schema()
    except Exception as exc:
        raise ConnectionError(f"Failed to retrieve live schema: {exc}") from exc

    if not tables:
        return {"tables_synced": 0, "total_rows": 0, "elapsed_ms": 0}

    duck_path = _db_path(session_id)
    total_rows = 0
    t0 = time.perf_counter()

    with _lock:
        with duckdb.connect(duck_path, read_only=False) as con:
            for t in tables:
                table_name = t["name"]
                safe_name = table_name.replace(".", "_")
                con.execute(f'DROP TABLE IF EXISTS "{safe_name}"')
                try:
                    result = live_query(f"SELECT * FROM {table_name}")
                except Exception as exc:
                    raise ConnectionError(
                        f"Failed to query live table {table_name}: {exc}"
                    ) from exc
                cols = result["columns"]
                rows = result["rows"]
                if not rows:
                    continue
                df = pd.DataFrame(rows, columns=cols)
                con.from_df(df, table_name=safe_name)
                total_rows += len(rows)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "tables_synced": len(tables),
        "total_rows": total_rows,
        "elapsed_ms": elapsed_ms,
    }


def warmup_cache(session_id: str = "sess1") -> dict:
    """Refresh live tables and pre-create lightweight aggregate views for low-latency common queries."""
    stats = refresh_cache(session_id)
    duck_path = _db_path(session_id)
    views_created = 0
    with _lock:
        with duckdb.connect(duck_path, read_only=False) as con:
            tables = con.execute("SHOW TABLES").fetchall()
            table_names = [row[0] for row in tables]
            for table_name in table_names:
                try:
                    columns = con.execute(f'PRAGMA table_info("{table_name}")').fetchall()
                except Exception:
                    continue
                time_cols = [c[1] for c in columns if "date" in c[1].lower() or "time" in c[1].lower()]
                text_cols = [c[1] for c in columns if c[2] and "VARCHAR" in c[2].upper()]
                if time_cols:
                    tc = time_cols[0]
                    view_name = f"vw_{table_name}_by{tc}"
                    try:
                        con.execute(f'CREATE OR REPLACE VIEW "{view_name}" AS SELECT * FROM "{table_name}" ORDER BY "{tc}"')
                        views_created += 1
                    except Exception:
                        pass
                if text_cols:
                    tc = text_cols[0]
                    view_name = f"vw_{table_name}_{tc}"
                    try:
                        count_aggregation = f'CREATE OR REPLACE VIEW "{view_name}" AS SELECT "{tc}", COUNT(*) AS cnt FROM "{table_name}" GROUP BY "{tc}"'
                        con.execute(count_aggregation)
                        views_created += 1
                    except Exception:
                        pass
                if time_cols and text_cols:
                    tc = time_cols[0]
                    gc = text_cols[0]
                    view_name = f"vw_{table_name}_{tc}_by_{gc}"
                    try:
                        count_grouped = f'CREATE OR REPLACE VIEW "{view_name}" AS SELECT "{tc}", "{gc}", COUNT(*) AS cnt FROM "{table_name}" GROUP BY "{tc}", "{gc}"'
                        con.execute(count_grouped)
                        views_created += 1
                    except Exception:
                        pass

                # Add any other required warm-up path features above this marker (no more builder calls below).
    out = dict(stats)
    out["views_created"] = views_created
    return out
