# Architecture

## System Overview

data-agent11 is an on-premises data analyst agent for UP Police. Analysts upload CSV or Excel files (or, in Phase 2, query a live MsSQL database) and ask questions in natural language. The agent generates SQL, executes it against an embedded DuckDB engine (or MsSQL via pyodbc), and returns a structured answer: prose summary, a result table, a recommended chart (if applicable), and export artefacts (CSV/Excel). A conversation-style Web UI is served single-origin from the same FastAPI process.

## Component Map

```
[Browser / Web UI]
      │  HTTP (REST + static)
      ▼
[FastAPI App]  ── mounts ──►  frontend/public/  (/app/)
      │
      ├─► [Runs API]   (POST /runs, GET /runs/{id})
      │       │
      │       ▼
      │   [LangGraph Agent] ──► [LLM Provider Layer]
      │       │                   (OpenRouter default / Anthropic / Gemini)
      │       │
      │       ├─► [SQL Generator Node]  ──► DuckDB engine  (Phase 1)
      │       │                                           │
      │       │                                    pyodbc ──► MsSQL  (Phase 2)
      │       │
      │       ├─► [Result Renderer Node] ──► Matplotlib  ──► PNG data URI
      │       │
      │       └─► [Export Node]         ──► CSV / .xlsx download
      │
      └─► [SQLAlchemy ORM]  ──► SQLite (run history, sessions, file metadata)
                                        │
                              QueryCache table (Phase 2)  ──► DuckDB blob store
```

## Layers

| Layer | Responsibility |
|-------|----------------|
| **Frontend (static)** | `frontend/public/` HTML/CSS/JS; served at `/app/`; same-origin `fetch` to `/runs`; zero-build |
| **REST API** | FastAPI routes in `src/api/`; schema-validated requests/responses; endpoint envelope (`ok`/`api_error`) |
| **Agent Orchestration** | LangGraph `StateGraph` in `src/graph/`; compiles once; handles routing, retry, error |
| **LLM Provider** | `src/llm/providers/` — httpx adapters for OpenRouter, Anthropic, Gemini; `retry.py` for 429/5xx; resolve at runtime from `.env` keys |
| **Data Processing** | `src/tools/` — pure functions NL → SQL (via LLM), SQL execution against DuckDB/MsSQL, result shaping, chart recommendations |
| **Persistence** | SQLAlchemy 2.0 (`src/db/`) — run history, sessions, file metadata; Alembic for migrations; DuckDB for analytical queries |
| **Observability** | `src/observability/` — structlog; per-run span; latency, tokens, error; stdout |

## Data Flow — Primary User Journey (Phase 1)

1. **Upload**: Analyst drags a CSV or Excel file into the UI → `POST /runs` with `active_files: [name]` → file streamed to DuckDB via `read_csv_auto` or `pandas.read_excel`; `UploadedFile` row created; DuckDB table registered.
2. **Query**: Analyst types "How many incidents per district?" → `POST /runs` with `query` field → LangGraph agent invoked.
3. **Planner node**: LLM generates a number-of-steps plan (1–4 steps) and identifies which tables/columns to use.
4. **SQL generation**: LLM writes and validates SQL (safety filter: SELECT-only, no DDL/DML).
5. **Execute**: SQL run against DuckDB; result as `list[dict]`.
6. **Render**: LLM writes prose summary; separate LLM call (or model-based heuristic) selects chart type; Matplotlib renders PNG.
7. **Proactive suggestions**: LLM proposes 2–3 follow-up queries and anomaly flags based on result statistics.
8. **Export**: User clicks "CSV" or "Excel" → `POST /runs/{id}/export/…` → file streamed back.
9. **Persist**: All steps logged in `RunRow`; session updated with `last_query`.

## External Dependencies

| Dependency | Purpose | Failure Mode | Mitigation |
|------------|---------|--------------|------------|
| **OpenRouter API** | LLM inference (default) | 429 rate-limit, 5xx, key invalid | Retry with backoff (exponential, 3 attempts); on persistent failure surface user-friendly error; ask clarifying question |
| **Anthropic API** | LLM inference (alternative) | Same as above | Same retry; resolve_provider picks whichever key is configured |
| **Google Gemini API** | LLM inference (alternative) | Same as above | Same |
| **DuckDB** | Local analytical engine (Phase 1) | Corrupt `.db` file, disk full | Detect corrupt file on open; prompt re-upload |
| **MsSQL via pyodbc** | Live production DB (Phase 2) | Network drop, auth failure, timeout | Retry once; surface specific error; `QueryCache` avoids re-fetch on repeat queries |
| **SQLite (internal)** | Run history + session state (always) | Corrupt journal | Alembic `upgrade head` + `init_db()` repair path |

## Stack

> **Assumed:** All stack decisions below are derived from the intake brief and the harness defaults. User stack preferences from intake that are binding: Python, FastAPI, LangGraph, DuckDB/SQLite, LLM providers OpenRouter (default) + Anthropic + Gemini, zero-build static frontend, uv, on-prem on-premises deployment. MsSQL/pyodbc, query caching, multi-file, persistent sessions, auth/audit (planned) are brief requirements mapped below.

- **Language:** Python 3.11+
- **Agent framework:** LangGraph (`langgraph` package)
- **LLM provider + default model:** OpenRouter / `anthropic/claude-sonnet-4-6` (configurable via `AGENT_LLM_MODEL`; resolves to per-provider default if blank)
- **LLM providers supported:** OpenRouter (default), Anthropic, Google Gemini — resolver picks whichever API key is configured in `.env`
- **Backend:** FastAPI, uvicorn, port **8001**
- **Database (analytical):** DuckDB (Phase 1) → MsSQL via `pyodbc` (Phase 2); SQLAlchemy 2.0 for ORM models
- **Database (persistence):** SQLite via SQLAlchemy — run history, sessions, file metadata, query cache
- **Frontend:** Zero-build static files (`frontend/public/`), served at `/app/`
- **Dependency management:** `uv` + `pyproject.toml`

### Key Libraries

| Library | Version / pin | Purpose |
|---------|--------------|---------|
| `fastapi` | latest | REST API + static file serve |
| `uvicorn[standard]` | latest | ASGI server |
| `langgraph` | latest | Graph orchestration |
| `langchain-core` | latest | LLM abstractions |
| `duckdb` | latest | Embedded analytical DB (Phase 1) |
| `pyodbc` | latest | MsSQL driver (Phase 2) |
| `sqlalchemy` | >= 2.0 | ORM + session management |
| `alembic` | latest | Schema migrations |
| `httpx` | latest | LLM provider HTTP client (no SDK) |
| `pandas` | latest | CSV/Excel read, result shaping, export |
| `openpyxl` | latest | `.xlsx` export |
| `matplotlib` | latest | Chart PNG rendering |
| `pydantic-settings` | latest | `.env` config |
| `structlog` | latest | Structured logging |
| `python-dotenv` | latest | `.env` loading |

### Avoid

- **No ORM for DuckDB query execution** — raw SQL via DuckDB Python API; SQLAlchemy for the internal SQLite store only
- **No SDKs for LLM providers** — direct `httpx` calls per `harness/patterns/code.md`
- **No Node / npm in Phase 1** — zero-build static frontend is wired; the gate reduces to "linked CSS/JS return 200 non-empty"
- **No silent provider fallback in production tests** — real-key execution is required; stub is optional dev fallback only, always labelled

## Deployment Model

> **Assumed:** On-prem single-node deployment on an internal network. A single `uv run python -m src` process exposes both the REST API and the static frontend. No load balancer required in the pilot. Docker deployment is deferred to post-pilot; runbook is `uv run python -m src` from the repo root.

- **Run command:** `cd C:/Users/Jayant Pratap/data-agent11 && uv run python -m src` (port 8001)
- **Exposed surface:** `http://<host>:8001/app/` (Web UI) + REST API on same origin
- **Data directory:** `data/app.db` (SQLite) + `data/cache.duckdb` (DuckDB)
- **Secrets:** `.env` file at repo root (gitignored); internal-only
- **Auth:** Planned for production; pilot relies on network access control
- **Audit:** Logging via structlog wired to stdout; persistent audit table planned for production
