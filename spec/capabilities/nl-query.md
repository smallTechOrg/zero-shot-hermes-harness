# nl-query — Capability

## What it does
Translate a natural-language question into a deterministic query execution plan and invoke the agent graph.

## Inputs
- `session_id`, `query` string, list of session `active_files`
- Optional: `provider`, `model`, `format`, `export_formats`

## Outputs
- `run_id`, `status`, and structured result envelope:
  - `answer_text`, `table` (columns + rows), `chart` (type + data URI)
  - `sql_used` (for verification), `follow_up_suggestions`, `anomaly_flags`
  - `export_links` (CSV/XLSX download URIs), `provider`, `model`, `duration_ms`

## External calls
- LLM (plan + SQL + summary + suggestions)
- DuckDB (`duckdb.execute`) or MsSQL (`pyodbc`) query execution
- Pandas/openpyxl for export blobs

## Error cases
- LLM failure → surfaced as `status: failed`, `error_message` populated; no 500
- SQL parse/execution failure → routed to `handle_error`; SQL returned for inspection
- Empty result → `status: completed`, `answer_text` = "No matching rows found"; chart/export skipped
- Timeout → same failure envelope; 30s DuckDB / 45s MsSQL default

## Success criteria
- `POST /runs` returns 200 in < 15 s with non-empty `answer_text`
- Generated SQL is `SELECT`-only; DDL/DML rejected at the executor boundary
- Re-running the same query within cache window (Phase 2) returns cached result fast
