# Project Layout — Canonical Structure

All agents built from this boilerplate follow this layout exactly. **The layout below is not
aspirational — it is the committed, working baseline in this repo.** `uv run pytest
tests/unit -q` passes on a fresh clone; generators extend these files in place.

---

## README Requirements (Mandatory)

Every generated project **must** have a README that:

1. **States "all commands run from the repo root"** — the repo root IS the project. Put
   this before any other content.
2. **Prefixes all Python commands with `uv run`** — bare `alembic`/`pytest`/`python` fail
   unless the venv is activated, which users won't do.
3. **Includes `uv run alembic current` after `upgrade head`** — blank output = silent
   failure; the user must be able to verify tables exist.
4. **Stays accurate** — every README command is run before a phase is marked complete. A
   wrong README fails the build regardless of whether the code works.

---

## Source Code Rule (Non-Negotiable)

**All application source code lives inside `src/` (backend) or `frontend/public/`
(frontend).** Never place application files at the repo root. The root is for project
config (`pyproject.toml`, `alembic.ini`, `agent.py`, `README.md`, `.env.example`) and
boilerplate infrastructure (`spec/`, `support/`, `AGENTS.md`).

**One package only.** The skeleton ships the flat package `src/` (imported as `src`, run as
`python -m src`). Extend it in place — never create a second package beside it, never copy
it to a new name. Two packages = dead code + two sources of truth.

---

## Directory Tree (the real baseline)

```
<repo root>                        ← repo root IS the agent project
├── src/                           ← the Python package (import src, python -m src)
│   ├── __init__.py                ← __version__
│   ├── __main__.py                ← python -m src → uvicorn on PORT (default 8001)
│   ├── api/
│   │   ├── __init__.py            ← create_app() + lifespan (logging + init_db); mounts frontend at /app
│   │   ├── _common.py             ← ok(), api_error() — the response envelope
│   │   ├── health.py              ← GET /health (provider presence, never key values)
│   │   └── runs.py                ← POST /runs, GET /runs/{id}
│   ├── config/
│   │   └── settings.py            ← BaseSettings, env prefix AGENT_, resettable singleton
│   ├── db/
│   │   ├── models.py              ← SQLAlchemy 2.0 declarative (Mapped types)
│   │   └── session.py             ← engine/session singletons + init_db (resettable)
│   ├── domain/
│   │   └── run.py                 ← Pydantic request/response models
│   ├── graph/                     ← LangGraph — THE CAPABILITY SLOT
│   │   ├── state.py               ← AgentState TypedDict
│   │   ├── nodes.py               ← transform_text (REPLACE), handle_error, finalize
│   │   ├── edges.py               ← conditional routing
│   │   ├── agent.py               ← StateGraph compiled once
│   │   └── runner.py              ← run_agent() — creates row, invokes graph, persists
│   ├── llm/
│   │   ├── client.py              ← LLMClient wrapper + load_prompt()
│   │   ├── retry.py               ← backoff on 429/5xx; actionable 401/404 errors
│   │   └── providers/             ← httpx adapters, no SDKs
│   │       ├── base.py            ← abstract LLMProvider + LLMError
│   │       ├── factory.py         ← create_llm_provider() from settings
│   │       ├── anthropic.py       ├── gemini.py             └── openrouter.py
│   ├── tools/                     ← pure functions: (inputs) → domain models (add as needed)
│   ├── prompts/
│   │   └── transform.md           ← system prompt (REPLACE with your capability's)
│   └── observability/
│       └── events.py              ← structlog config + log_span (latency, error)
├── frontend/
│   └── public/                    ← ZERO-BUILD static frontend, served at /app
│       ├── index.html             ← the transform form (REPLACE with your UI)
│       ├── styles.css
│       └── app.js                 ← same-origin fetch to the API
├── tests/                         ← at repo root, NOT inside src/
│   ├── conftest.py                ← resets settings/db singletons; isolated tmp SQLite per test
│   ├── unit/                      ← pass with NO API key (15 tests out of the box)
│   └── integration/               ← REAL LLM/API via .env keys; skip (never stub) if absent
├── alembic/                       ← wired: env.py reads settings; script.py.mako present
│   └── versions/                  ← empty in the baseline; first schema change adds 0001
├── spec/                          ← the spec templates (filled by spec-writer)
├── support/                      ← rules, patterns, agents, commands
├── agent.py                       ← doctor (default) / --run (migrate + serve)
├── pyproject.toml                 ← deps + pytest config (testpaths, pythonpath=["."])
├── alembic.ini                    ← prepend_sys_path = . (alembic runs without hacks)
├── .env.example                   ← every env var documented; .env is gitignored
├── AGENTS.md                      ← the session entry point
└── README.md
```

**The capability slot** — the three surfaces to replace for your agent:
1. `src/graph/nodes.py` — replace `transform_text` with your capability logic (add nodes/edges per `spec/agent.md`)
2. `src/prompts/transform.md` — replace with your system prompt(s)
3. `frontend/public/` — replace the transform form with your UI

Everything else (graph assembly, API envelope, DB session, settings, provider layer,
logging, test fixtures) is wired and tested — change it only when the spec requires it.

---

## Key File Shapes (as committed — read the real files, these are the contracts)

- **Settings** (`src/config/settings.py`): `env_prefix="AGENT_"`, `.env` file, resettable
  module singleton (`_settings = None` in tests). `resolve_provider()` auto-detects from
  whichever key is set; `resolve_model()` falls back to per-provider defaults.
- **DB** (`src/db/session.py`): lazy engine + sessionmaker singletons, `get_session()`
  FastAPI dependency, `create_db_session()` context manager for nodes/scripts, `init_db()`
  create_all for the baseline. **Schema changes beyond the baseline ship an alembic
  revision** — `create_all` never ALTERs an existing table; a stale dev DB turns a green
  suite into a live 500.
- **Nodes** (`src/graph/nodes.py`): `(state) -> partial state`; failures go into
  `state["error"]` (the error edge routes to `handle_error`) — never raise through the graph.
- **API** (`src/api/`): every route returns `ok(data)` or raises `api_error(code, message,
  status)`. A failed agent run is a 200 with `status: "failed"` + an actionable
  `error_message` — never a naked 500.
- **Tests** (`tests/conftest.py`): autouse fixtures reset the settings/db singletons and
  point `AGENT_DATABASE_URL` at a tmp SQLite file per test; the `no_keys` fixture blanks
  provider keys via env vars (env beats `.env` in pydantic-settings). Integration tests
  `pytest.skip` when no real key is present — they never stub.

---

## Alembic (wired, empty until first schema change)

`alembic.ini` carries `prepend_sys_path = .` (so `from src...` imports resolve — without it
`alembic` fails with `ModuleNotFoundError` even though pytest passes) and `env.py` injects
the URL from settings. On the first schema change:

```bash
# repo root
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
uv run alembic current        # must print a revision — blank = silent failure
```

---

## Rules

1. **Agent code goes in `src/`** — never at the repo root.
2. **No repository pattern** — direct SQLAlchemy queries in nodes and API handlers.
3. **TypedDict state** — not dataclass or Pydantic, for graph state.
4. **Tools are pure functions** — `(inputs) → domain model`, no class instantiation.
5. **Prompts are `.md` files** in `src/prompts/` — loaded at runtime via `load_prompt()`.
6. **LLM abstraction** — nodes call `LLMClient`, never a provider adapter directly.
7. **Response envelope** — every route returns `ok(data)` or raises `api_error()`.
8. **Singletons resettable** — settings and db expose module-level `_x = None` reset.
9. **Frontend is zero-build by default** — static files in `frontend/public/`, served
   single-origin at `/app`. Adopt a JS framework only when the spec demands it; the build
   then becomes part of the gate.
10. **Gates run against real services** — real LLM/API keys from `.env`, production DB
    driver (never SQLite when prod is PostgreSQL).
