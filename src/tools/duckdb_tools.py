"""DuckDB tooling: schema introspection, TEMP TABLE creation, and SELECT-only enforcement."""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

_SELECT_RE = re.compile(r"^\s*SELECT", re.IGNORECASE)
DDL_DML_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|EXEC|EXECUTE|COPY|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
_SEMICOLON_CHAIN_RE = re.compile(r";\s*\w")
# Disallow a trailing semicolon that then appends a second statement.
_MAX_CONNECTION_ATTEMPTS = 2
_DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class TableMeta:
    normalized_name: str
    original_name: str
    row_count: int
    columns: list[dict[str, str]]


class DuckDBConnector:
    """Thin wrapper keeping a DuckDB file connection alive for the app lifetime."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._connection: duckdb.DuckDBPyConnection | None = None
        self._conn_lock = __import__("threading").RLock()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        conn = duckdb.connect(self.db_path, read_only=False)
        conn.execute("SET TimeZone = 'UTC'")
        try:
            conn.execute("SET temp_directory = ''")
        except Exception:
            pass
        return conn

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        with self._conn_lock:
            if self._connection is None:
                self._connection = self._connect()
            return self._connection

    def close(self) -> None:
        with self._conn_lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception:
                    pass
                self._connection = None

    def __enter__(self) -> "DuckDBConnector":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def refresh_connection(self) -> duckdb.DuckDBPyConnection:
        self.close()
        return self.connection


def build_connector(database_url: str) -> DuckDBConnector:
    # Phase 1 always uses DuckDB regardless of whether the URL is sqlite:// for run history.
    # We derive a DuckDB file name next to the sqlite file so crashes don't clobber history.
    if database_url.startswith("sqlite:///"):
        candidate = database_url[len("sqlite:///") :]
    else:
        candidate = ":memory:"
    if candidate == ":memory:":
        duckdb_path = ":memory:"
    else:
        duckdb_path = str(Path(candidate).with_suffix(".duckdb"))
    return DuckDBConnector(duckdb_path)


def open_csv(path: str | Path, table_name: str, connector: DuckDBConnector) -> TableMeta:
    conn = connector.connection
    # Ensure any prior temp table with the same name is dropped.
    try:
        conn.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
    except Exception:
        pass
    try:
        conn.execute(
            f"CREATE OR REPLACE TEMP TABLE \"{table_name}\" AS SELECT * FROM read_csv_auto('{path}')"
        )
    except Exception:
        # Fall back to pandas for exotic encodings / formats.
        df = pd.read_csv(path)
        conn.register("_df_fallback", df)
        conn.execute(
            f"CREATE OR REPLACE TEMP TABLE \"{table_name}\" AS SELECT * FROM _df_fallback"
        )
    return _describe_table(conn, table_name)


def open_excel(path: str | Path, table_name: str, connector: DuckDBConnector) -> TableMeta:
    conn = connector.connection
    try:
        conn.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
    except Exception:
        pass
    df = pd.read_excel(path)
    conn.register("_df_fallback", df)
    conn.execute(
        f"CREATE OR REPLACE TEMP TABLE \"{table_name}\" AS SELECT * FROM _df_fallback"
    )
    return _describe_table(conn, table_name)


def list_temp_tables(conn: duckdb.DuckDBPyConnection) -> list[str]:
    try:
        rows = conn.execute("SHOW TABLES").fetchall()
    except Exception:
        return []
    return [str(r[0]) for r in rows]


def _describe_table(
    conn: duckdb.DuckDBPyConnection, table_name: str
) -> TableMeta:
    columns_rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall() or []
    columns = [{"name": row[1], "type": (row[2] or "unknown")} for row in columns_rows]
    try:
        count_row = conn.execute(
            f'SELECT COUNT(*) AS cnt FROM "{table_name}"'
        ).fetchone()
        row_count = int(count_row[0]) if count_row else 0
    except Exception:
        row_count = 0
    return TableMeta(
        normalized_name=table_name,
        original_name=table_name,
        row_count=max(row_count, 0),
        columns=columns,
    )


def assert_select_only(query: str) -> None:
    if query and not _SELECT_RE.match(query):
        raise ValueError("Only SELECT statements are permitted.")
    if query and DDL_DML_RE.search(query):
        raise ValueError("DDL/DML keywords are not allowed in the query.")
    if query and _SEMICOLON_CHAIN_RE.search(query):
        raise ValueError("Multiple statements in one query are not allowed.")


def execute_select(
    connector: DuckDBConnector,
    query: str,
    *,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    assert_select_only(query)
    with connector._conn_lock:
        try:
            rel = connector.connection.execute(query)
            columns = [desc[0] for desc in rel.description] if rel.description else []
            rows = rel.fetchall()
        except duckdb.IOException as exc:
            # Connection-level failure — refresh once per call and retry.
            connector.refresh_connection()
            rel = connector.connection.execute(query)
            columns = [desc[0] for desc in rel.description] if rel.description else []
            rows = rel.fetchall()
    dict_rows = [dict(zip(columns, row)) for row in rows]
    return dict_rows


def render_chart_png(
    chart_type: str,
    rows: list[dict[str, Any]],
    columns: list[str] | None,
) -> str | None:
    if not rows:
        return None
    import base64
    import io

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    df = pd.DataFrame(rows)
    x = columns[0] if columns else df.columns[0]
    y = columns[1] if len(columns) > 1 else df.columns[0]

    fig, ax = plt.subplots(figsize=(6.0, 3.6), dpi=140)
    try:
        if chart_type == "bar":
            if len(df.columns) >= 2:
                ax.bar(df[x].astype(str), df[y])
            else:
                ax.bar(df.index.astype(str), df.iloc[:, 0])
        elif chart_type == "line":
            if len(df.columns) >= 2:
                ax.plot(df[x].astype(str), df[y])
            else:
                ax.plot(df.iloc[:, 0])
        elif chart_type == "pie":
            values = df[y] if len(df.columns) >= 2 else df.iloc[:, 0]
            ax.pie(values.values, labels=(df[x].astype(str).values if len(df.columns) >= 2 else values.index.astype(str).values), autopct="%1.0f%%")
        else:
            ax.text(0.02, 0.5, df.head(10).to_string(index=False), va="center", ha="left", fontsize=8, family="monospace")
            ax.axis("off")
            fig.set_size_inches(8.0, 3.6)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.25)
            buf.seek(0)
            png = base64.b64encode(buf.read()).decode("utf-8")
            return f"data:image/png;base64,{png}"
    except Exception as exc:
        return None
    finally:
        plt.close(fig)
    ax.set_xlabel(x)
    if chart_type != "pie":
        ax.set_ylabel(y if chart_type != "line" else (columns[1] if len(columns) > 1 else columns[0]))
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.25)
    buf.seek(0)
    png = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{png}"
