# Phases of Development

> **Assumed (from intake):** Phase 1 scope is CSV-first with DuckDB, single-file active per session. Phase 2 adds live MsSQL via pyodbc, multi-file sessions, proactive suggestions, and anomaly flags. The pilot gate is a working single-file CSV upload + NL query + answer + chart + export flow served by the live FastAPI app.

---

### Phase 1 — Upload -> Query -> Answer

- **Goal:** One upload (CSV/Excel), one natural-language question, one chat-quality answer (text + table + chart + export), rendered through the real `/runs` API and a visibly real `/app/` UI. Zero rough edges on that one tested path.

- **Independent slices (parallel build units):**
  - `slice-a` (backend) — Ingestion path, DuckDB exec wrapper, the new LangGraph graph, API contract extension
    deps: none
  - `slice-b` (frontend) — Upload UI, query form, answer panel with chart + table + export buttons
    deps: slice-a contract (response schema)

- **Key surfaces / files:**
  - `spec/agent.md`, `spec/api.md`, `spec/ui.md`, `spec/data.md`
  - `src/graph/state.py`, `src/graph/nodes.py`, `src/graph/edges.py`, `src/graph/agent.py`
  - `src/llm/client.py`, `src/api/runs.py`, `src/domain`
  - `frontend/public/index.html`, `app.js`, `styles.css`

- **Gate command:**
  `uv run pytest tests/integration -q` (runs against real LLM key in `.env`; never stubbed.)

- **How the user tests it (handoff seed):**
  1. Run `cd C:/Users/Jayant Pratap/data-agent11 && uv run python -m src`
  2. Open `http://localhost:8001/app/` — page loads; upload a CSV; type a question
  3. See prose answer, table data, chart image, and working Export buttons
  4. Parts clearly labelled as Phase 2 stubs: multi-file manager, session history, follow-up suggestions, anomaly flags, auth

---

### Phase 2 — Live DB, Proactive Intelligence, Multi-file

- **Goal:** Connect live to MsSQL with query caching; enable multi-file active state; surface proactive suggestions and anomaly flags; expose CLI surface.

- **Independent slices (parallel build units):**
  - `slice-a` (backend) — MsSQL/pyodbc adapter, QueryCache implementation, multi-file session state
    deps: none (DuckDB path continues to work)
  - `slice-b` (frontend + backend) — Proactive panel, multi-file manager UI, CLI entrypoint
    deps: slice-a `QueryCache` + multi-file session contract

- **Key surfaces / files:**
  - `src/db/` (Alembic migration for `QueryCache`)
  - `src/graph/nodes.py` (suggest/anomaly nodes enabled)
  - `src/api/runs.py`, `src/api/sessions.py`
  - `frontend/public/app.js`, `index.html` (proactive + multi-file UI)
  - `src/cli.py`

- **Gate command:**
  `uv run pytest tests/integration -q` (requires `AGENT_MSSQL_CONNECTION_STRING` set in `.env`)

- **How the user tests it (handoff seed):**
  1. Set `AGENT_MSSQL_CONNECTION_STRING` in `.env`; restart
  2. Open `/app/`, enter MsSQL session
  3. Type a cross-table query; see caching note on second attempt
  4. Upload two files; query across both
  5. See follow-up suggestions + anomaly flags in the proactive panel
  6. CLI: `uv run python -m src --query "..." --format chart+table`
