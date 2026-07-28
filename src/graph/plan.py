"""Plan query — produce a 2–4 step analysis plan from the user's question and schema."""
from __future__ import annotations

from src.llm.client import LLMClient, load_prompt


def plan_query(state: AgentState) -> AgentState:
    try:
        client = LLMClient()
        schema_context = _build_schema_context(state)
        prompt = load_prompt("plan-query").replace("{{SCHEMA}}", schema_context)
        user = (state.get("input_text") or "").strip() or state.get("query") or ""
        result = client.complete(prompt, user, max_tokens=2048)
        plan = [line.strip() for line in result.splitlines() if line.strip()]
        return {**state, "plan": plan, "error": None}
    except LLMError as exc:
        return {**state, "error": str(exc)}


# Local schema helper to avoid duplicating the DB import graph.
def _build_schema_context(state: AgentState) -> str:
    try:
        from src.tools.duckdb_tools import build_connector, list_temp_tables
        connector = build_connector(_resolve_db_url())
        tables = list_temp_tables(connector.connection)
    except Exception:
        tables = []
    if not tables:
        return "No tables loaded."
    lines = ["Available tables:"]
    for table in tables:
        try:
            rows = connector.connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        except Exception:
            rows = []
        cols = ", ".join(str(r[1]) for r in rows) if rows else "unknown"
        lines.append(f"- {table} ({cols})")
    return "\n".join(lines)


def _resolve_db_url() -> str:
    try:
        from src.config.settings import get_settings
        return get_settings().database_url
    except Exception:
        return "sqlite:///./data/app.db"
