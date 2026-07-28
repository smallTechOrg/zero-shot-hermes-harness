"""Baseline-compatible graph nodes with optional data-analyst behaviour."""
from __future__ import annotations

from src.graph.state import AgentState
from src.llm.client import LLMClient, load_prompt
from src.llm.providers.base import LLMError


def transform_text(state: AgentState) -> AgentState:
    """Baseline node name/contract intact; enhanced path when analyst context is present."""
    try:
        client = LLMClient()
        system = state.get("instruction") or "You are a helpful assistant."
        user = (state.get("input_text") or "").strip()
        if not user:
            return {"status": "completed", "output_text": "", "error": None}
        text = client.complete(system, user, max_tokens=1024)
        return {
            "status": "completed",
            "output_text": text,
            "provider": client.provider_name,
            "model": client.model,
            "error": None,
        }
    except LLMError as exc:
        return {"status": "failed", "output_text": None, "error": str(exc)}


def plan_query(state: AgentState) -> AgentState:
    try:
        client = LLMClient()
        system = load_prompt("plan-query").replace("{{SCHEMA}}", _schema_context())
        user = (state.get("input_text") or "").strip() or state.get("query") or ""
        text = client.complete(system, user, max_tokens=2048)
        plan = [line.strip() for line in text.splitlines() if line.strip()]
        return {**state, "plan": plan, "error": None}
    except LLMError as exc:
        return {**state, "error": str(exc)}


def generate_sql(state: AgentState) -> AgentState:
    try:
        client = LLMClient()
        system = load_prompt("generate-sql").replace("{{SCHEMA}}", _schema_context())
        user = "\n".join(
            [
                "Plan:",
                "\n".join(state.get("plan") or []),
                "",
                "User query:",
                state.get("input_text") or state.get("query") or "",
            ]
        )
        sql = client.complete(system, user, max_tokens=2048)
        sql = sql.strip().rstrip(";")
        try:
            from src.tools.duckdb_tools import assert_select_only
            assert_select_only(sql)
        except Exception as exc:
            return {**state, "generated_sql": sql, "sql_error": str(exc), "error": None}
        return {**state, "generated_sql": sql, "sql_error": None, "error": None}
    except LLMError as exc:
        return {**state, "generated_sql": None, "sql_error": str(exc), "error": str(exc)}


def execute_query(state: AgentState) -> AgentState:
    sql_error = state.get("sql_error")
    sql = (state.get("generated_sql") or "").strip()
    if sql_error or not sql:
        return {**state, "result_rows": None, "result_columns": None, "error": None}
    try:
        from src.tools.duckdb_tools import execute_select
        connector = _get_connector()
        if connector is None:
            return {**state, "result_rows": None, "result_columns": None, "sql_error": "DuckDB not configured", "error": None}
        t0 = _now_ms()
        rows = execute_select(connector, sql, timeout_seconds=30)
        duration_ms = _now_ms() - t0
        columns: list[str] = []
        if rows:
            columns = list(rows[0].keys())
        return {**state, "result_rows": rows, "result_columns": columns, "duration_ms": duration_ms, "error": None}
    except Exception as exc:
        return {**state, "result_rows": None, "result_columns": None, "sql_error": str(exc), "error": None}


def render_answer(state: AgentState) -> AgentState:
    rows = state.get("result_rows") or []
    try:
        client = LLMClient()
        system = load_prompt("render-answer")
        user = "\n".join(
            [
                "User query:",
                state.get("input_text") or state.get("query") or "",
                "",
                "SQL used:",
                state.get("generated_sql") or "",
                "",
                "Result rows:",
                _safe_json(rows[:200]),
            ]
        )
        text = client.complete(system, user, max_tokens=2048)
        return {**state, "answer_text": text, "output_text": text, "error": None}
    except LLMError as exc:
        fallback = _fallback_answer(rows)
        return {**state, "answer_text": fallback, "output_text": fallback, "error": str(exc)}


def _safe_json(obj: object) -> str:
    try:
        import json
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def _fallback_answer(rows: list[dict]) -> str:
    n = len(rows)
    cols = list(rows[0].keys()) if rows else []
    return f"Returned {n} row(s) with columns: {', '.join(cols)}."


def recommend_chart(state: AgentState) -> AgentState:
    rows = state.get("result_rows") or []
    columns = state.get("result_columns") or []
    chart_type = "table"
    if rows and len(rows) <= 500 and len(columns) >= 2:
        numeric_cols = [
            c for c in columns
            if any(isinstance(r.get(c), (int, float)) for r in rows[:20])
        ]
        if numeric_cols:
            chart_type = "bar"
    return {**state, "chart_type": chart_type}


def render_chart(state: AgentState) -> AgentState:
    chart_type = state.get("chart_type") or "table"
    rows = state.get("result_rows") or []
    columns = state.get("result_columns") or []
    if chart_type in {"table", None} or not rows:
        return {**state, "chart_png_base64": None}
    try:
        from src.tools.duckdb_tools import render_chart_png
        return {**state, "chart_png_base64": render_chart_png(chart_type, rows, columns)}
    except Exception:
        return {**state, "chart_png_base64": None}


def suggest_followups(state: AgentState) -> AgentState:
    try:
        client = LLMClient()
        system = load_prompt("suggest-followups")
        user = "\n".join(
            [
                "Original question:",
                state.get("input_text") or state.get("query") or "",
                "",
                "Answer:",
                state.get("answer_text") or "",
            ]
        )
        text = client.complete(system, user, max_tokens=1024)
        suggestions: list[str] = []
        flags: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- "):
                item = line[2:]
                if "flag" in line.lower():
                    flags.append(item)
                else:
                    suggestions.append(item)
        return {**state, "follow_up_suggestions": suggestions[:5], "anomaly_flags": flags[:3], "error": None}
    except LLMError:
        return {**state, "follow_up_suggestions": None, "anomaly_flags": None, "error": None}


def prepare_exports(state: AgentState) -> AgentState:
    rows = state.get("result_rows") or []
    formats = state.get("export_formats") or []
    if not rows or not formats:
        return {**state, "export_paths": {}}
    run_id = state.get("run_id") or ""
    try:
        from src.config.settings import get_settings
        from pathlib import Path
        import pandas as pd
        base_dir = Path(get_settings().database_url.replace("sqlite:///", "")).parent / "exports"
        base_dir.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        paths: dict[str, str] = {}
        for fmt in formats:
            fmt = str(fmt).lower()
            if fmt == "csv":
                out = base_dir / f"run-{run_id}.csv"
                df.to_csv(out, index=False)
            elif fmt in {"xlsx", "excel"}:
                out = base_dir / f"run-{run_id}.xlsx"
                df.to_excel(out, index=False)
            else:
                continue
            paths[fmt] = str(out)
        return {**state, "export_paths": paths}
    except Exception as exc:
        return {**state, "export_paths": {}, "error": str(exc)}


def finalize(state: AgentState) -> AgentState:
    return {**state, "status": "completed"}


def handle_error(state: AgentState) -> AgentState:
    return {**state, "status": "failed" if state.get("error") else "completed"}


def ingest_file(file_path: str, normalized_name: str) -> object:
    connector = _get_connector()
    if connector is None:
        raise RuntimeError("DuckDB connector is not configured.")
    from pathlib import Path
    from src.tools.duckdb_tools import open_csv, open_excel
    p = Path(file_path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return open_csv(p, normalized_name, connector)
    if suffix in {".xlsx", ".xls"}:
        return open_excel(p, normalized_name, connector)
    raise ValueError(f"Unsupported file type: {suffix}")


def _get_connector() -> object | None:
    try:
        from src.tools.duckdb_tools import build_connector
        from src.config.settings import get_settings
        return build_connector(get_settings().database_url)
    except Exception:
        return None


def _current_tables() -> list[str]:
    connector = _get_connector()
    if connector is None:
        return []
    try:
        from src.tools.duckdb_tools import list_temp_tables
        return list_temp_tables(connector.connection)
    except Exception:
        return []


def _schema_context() -> str:
    tables = _current_tables()
    if not tables:
        return "No tables loaded."
    connector = _get_connector()
    lines = ["Available tables:"]
    for table in tables:
        cols = "unknown"
        try:
            rows = connector.connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            cols = ", ".join(str(r[1]) for r in rows)
        except Exception:
            pass
        lines.append(f"- {table} ({cols})")
    return "\n".join(lines)


def _now_ms() -> int:
    import time
    return int(time.time() * 1000)
