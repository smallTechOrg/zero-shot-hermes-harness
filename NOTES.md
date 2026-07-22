# Release notes

## Phase 2 — Live MsSQL connectivity

- Adds read-replica connectivity with a local DuckDB cache layer.
- New endpoints: `POST /api/v1/db/connect`, `GET /api/v1/db/test-connection`, `GET /api/v1/db/schema`, `POST /api/v1/db/refresh-cache`.
- Frontend adds a Live Database panel with connect + refresh controls, and a data source toggle on Ask.
- `uv run pytest tests/unit -q` is the canonical gate.

### Known follow-ups before merge/PR polish

- Review uncommitted changes in working tree:
 - `src/db/models.py`
 - `src/db/session.py`
 - `src/domain/__init__.py`
 - `src/domain/run.py`
 - `src/llm/providers/openrouter.py`
 - `tests/unit/test_deployment_state.py`
 - `alembic/versions/869440ced39f_add_run_latency_ms.py`
 If these are desired, they should be committed explicitly alongside Phase 2 review.
