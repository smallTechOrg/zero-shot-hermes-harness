"""Cache synchronization — mirror live MsSQL tables into the local DuckDB cache.

This function copies schema and data from the connected MsSQL read-replica
into the session's DuckDB file. It is intended to be triggered manually
via the UI ("Refresh Cache") to create a local, low-latency copy of
selected analytical tables.

Large tables are copied in full; consider the storage and time implications.
"""

from __future__ import annotations

import os
import time
from typing import Any

import duckdb
import pandas as pd

from src.db.duckdb_store import init_session, _db_path, _lock
from src.db.mssql_connector import live_schema, live_query


def refresh_cache(session_id: str = "sess1") -> dict:
    """Synchronize all tables from MsSQL into the session's DuckDB cache.

    Drops and recreates each table with fresh data. Returns a summary
    with the number of tables synced, total rows copied, and elapsed time.

    Raises:
        ConnectionError: If MsSQL connection string is not set or fetching
                         schema/data fails.
    """
    # Ensure the DuckDB file exists
    init_session(session_id)

    # Ensure MsSQL connection string is configured
    conn_str = os.environ.get("AGENT_MSSQL_CONNECTION_STRING")
    if not conn_str:
        raise ConnectionError(
            "AGENT_MSSQL_CONNECTION_STRING environment variable not set. "
            "Set it in .env or via the /api/v1/db/connect endpoint."
        )

    # Retrieve live schema
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
                # Use a safe table name: replace dots (schema.table) with underscore
                safe_name = table_name.replace(".", "_")
                # Drop if exists
                con.execute(f'DROP TABLE IF EXISTS "{safe_name}"')
                # Fetch all data from the live table
                try:
                    result = live_query(f'SELECT * FROM {table_name}')
                except Exception as exc:
                    raise ConnectionError(
                        f"Failed to query live table {table_name}: {exc}"
                    ) from exc
                cols = result["columns"]
                rows = result["rows"]
                if not rows:
                    # Skip empty tables (no rows) to avoid creating empty DataFrames
                    continue
                # Load into DuckDB using pandas
                import pandas as pd
                df = pd.DataFrame(rows, columns=cols)
                con.from_df(df, table_name=safe_name)
                total_rows += len(rows)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "tables_synced": len(tables),
        "total_rows": total_rows,
        "elapsed_ms": elapsed_ms,
    }
