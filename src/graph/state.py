"""AgentState — the TypedDict flowing through the graph."""
from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    session_id: str | None
    provider: str | None
    model: str | None
    status: str | None
    error: str | None

    # Input
    input_text: str | None
    instruction: str | None
    active_files: list[str] | None

    # Plan
    plan: list[str] | None

    # SQL
    generated_sql: str | None
    sql_error: str | None

    # Results
    result_columns: list[str] | None
    result_rows: list[dict] | None

    # Outputs
    output_text: str | None
    answer_text: str | None
    chart_type: str | None
    chart_png_base64: str | None
    follow_up_suggestions: list[str] | None
    anomaly_flags: list[str] | None
    export_formats: list[str]
    export_paths: dict[str, str] | None
