# Agent

## Agent Architecture Pattern

Planner-first data analyst. The agent decomposes each natural-language query into 2–4 explicit steps before generating SQL, executes the SQL against DuckDB (or MsSQL in Phase 2), and then renders the structured answer. Error handling is explicit: SQL errors, empty results, and LLM failures are surfaced as typed states; the user never sees a 500 stack trace.

> **Assumed:** Single-agent, single-graph LangGraph `StateGraph`. No multi-agent orchestrator, no tool-calling loop per se — the graph encodes the fixed pipeline `plan → sql → execute → render → suggest`. Retry logic lives in the LLM provider layer (`retry.py`) and in the SQL execution wrapper; the graph itself routes on typed error states.

---

## State

`AgentState` extends the baseline `AgentState` from `src/graph/state.py` with data-analyst fields.

```python
class AgentState(TypedDict, total=False):
    run_id: str
    session_id: str
    provider: str
    model: str
    status: str
    error: str | None

    # Input
    input_text: str       # user natural-language query
    active_files: list[str]

    # Plan
    plan: list[str]       # 2–4 steps: tables/joins/filters/reasoning

    # SQL
    generated_sql: str | None
    sql_error: str | None

    # Results
    result_columns: list[str] | None
    result_rows: list[dict] | None

    # Outputs
    answer_text: str | None
    chart_type: str | None
    chart_png_base64: str | None
    follow_up_suggestions: list[str] | None
    anomaly_flags: list[str] | None
    export_formats: list[str]
    export_paths: dict[str, str] | None
```

---

## Nodes

| Node | Responsibility | Inputs → Outputs |
|------|----------------|-------------------|
| `plan_query` | LLM call: inspect schemas of `active_files`, produce a 2–4 step plan (tables, joins, filters, reasoning) | `input_text`, `active_files` → `plan` |
| `generate_sql` | LLM call: translate `plan` + user query into SELECT-only SQL; POST-check blocked keywords | `plan`, `input_text` → `generated_sql` |
| `execute_query` | Run SQL against DuckDB (`duckdb.execute`) or MsSQL (`pyodbc`) | `generated_sql`, `active_files` → `result_rows`, `sql_error` |
| `render_answer` | LLM call: turn raw rows into prose summary + table | `result_rows`, `input_text` → `answer_text` |
| `recommend_chart` | Heuristic / LLM call: choose bar/line/pie/table based on row count and column dtypes | `result_columns`, `result_rows` → `chart_type` |
| `render_chart` | Matplotlib render → PNG base64 (or skip on 0 rows / >500 rows without explicit request) | `chart_type`, `result_rows`, `result_columns` → `chart_png_base64` |
| `suggest_followups` | LLM call: propose 2–3 follow-up queries + anomaly flags | `result_rows`, `input_text` → `follow_up_suggestions`, `anomaly_flags` |
| `prepare_exports` | Pandas + openpyxl: write CSV/XLSX blobs, return download URIs | `result_rows` → `export_paths` |
| `finalize` | Mark run completed | → `status = "completed"` |
| `handle_error` | Capture error, mark run failed/degraded | → `status`, `error` |

---

## Edges

```
START
  │
  ▼
plan_query ──[error]──► handle_error
  │
  ▼
generate_sql ──[sql_error]──► handle_error
  │
  ▼
execute_query ──[sql_error]──► handle_error
  │
  ▼
render_answer
  │
  ▼
recommend_chart
  │
  ▼
render_chart (optional; skip on 0 rows / heavy output)
  │
  ▼
suggest_followups
  │
  ▼
prepare_exports
  │
  ▼
finalize ──► END
```

Error edges from any node route to `handle_error`, which writes `status` and `error` and routes to `END`.

---

## Assembly

```python
from src.graph.state import AgentState
from langgraph.graph import END, StateGraph

g = StateGraph(AgentState)
for node in ["plan_query", "generate_sql", "execute_query", "render_answer",
             "recommend_chart", "render_chart", "suggest_followups",
             "prepare_exports", "finalize", "handle_error"]:
    g.add_node(node, getattr(src.graph.nodes, node))

g.set_entry_point("plan_query")
# ... add edges as shown above ...
agentic_ai = g.compile()
```

> **Assumed:** Graph compiles once at import (`src/graph/agent.py`). No per-run state mutation leaks across invocations because the runner builds a fresh `initial` dict for each `invoke()`.

---

## Invariants

1. **No DDL/DML via generated SQL:** `execute_query` runs a safety filter (regex or AST) rejecting `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `EXEC`, `;` chain. Only `SELECT` is permitted.
2. **One batched LLM call per node output:** never a per-row loop.
3. **Empty results are not errors:** `render_answer` produces "No matching rows found"; `render_chart` and `prepare_exports` are skipped.
4. **Timeouts:** per-query DuckDB timeout is 30 seconds (Phase 2 MsSQL: 45 seconds). LLM timeout 60 seconds.
5. **No secret leakage:** generated SQL, query text, and LLM prompts are logged in structured form; never echoed client-side beyond the explicit "Show SQL" UI toggle.
