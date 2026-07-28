"""Request/response models for the runs API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    # Baseline field: validation unchanged so existing tests keep passing.
    text: str = Field(..., min_length=1, max_length=100_000)
    instruction: str = Field(
        default="Analyze the data and answer the question.",
        min_length=1,
        max_length=2_000,
    )

    # Data-analyst extension: used when the agent is acting as analyst.
    query: str | None = Field(default=None, min_length=0, max_length=100_000)
    session_id: str | None = Field(default=None)
    active_files: list[str] | None = Field(default=None)
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=200)
    format: str | None = Field(default="chart+table", pattern="^(text|table|chart\\+table)$")
    export_formats: list[str] | None = Field(default=None)

    def resolved_query(self) -> str:
        return self.query if self.query is not None else self.text


class RunResult(BaseModel):
    run_id: str
    status: str
    output_text: str | None = None
    provider: str | None = None
    model: str | None = None
    error_message: str | None = None
    # Data-analyst extension
    answer_text: str | None = None
    table: dict | None = None
    chart: dict | None = None
    export_links: dict[str, str] | None = None
    follow_up_suggestions: list[str] | None = None
    anomaly_flags: list[str] | None = None
    sql_used: str | None = None
    duration_ms: int | None = None
