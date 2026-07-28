# API

## API Style

REST (FastAPI) + optional CLI entry point (Click / argparse sub-process).

All endpoints return the standard envelope `{ok: true, data: …}` or `{ok: false, error: {code, message}}`. Agents runs always return HTTP 200; run failure is surfaced in the response body (`status: "failed"`), never as a 500 stack trace.

| Surface | Path | Primary user |
|---------|------|-------------|
| Web UI | `GET /app/` | Human analyst via browser |
| REST API | `POST /runs`, `GET /runs/{run_id}`, `POST /sessions`, `GET /sessions` | Scripted/automated consumers |
| CLI | `uv run data-agent11 --query "..." --file data.csv` | Power users, automation |
| Health | `GET /health` | Monitoring / load-balancer |

## Endpoints

### `POST /runs`

**Purpose:** Execute one NL query over the session's active files. Creates a `Run` row, invokes the agent graph, returns the result.

**Request:**
```json
{
  "session_id": "uuid",
  "query": "Show me total incidents per district last month",
  "active_files": ["incidents_march.csv", "stations.csv"],
  "provider": "openrouter",
  "model": "anthropic/claude-sonnet-4-6",
  "format": "chart+table",
  "export_formats": ["csv", "excel"]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| session_id | str | yes | UUID of the session |
| query | str | yes | Natural-language question |
| active_files | str[] | yes | Filenames in the session's file set |
| provider | str | no | `anthropic` / `gemini` / `openrouter`; default from env |
| model | str | no | Per-provider model ID; default from env |
| format | str | no | `text` / `table` / `chart+table` |
| export_formats | str[] | no | `csv`, `excel`; empty = no export |

**Response:**
```json
{
  "ok": true,
  "data": {
    "run_id": "uuid",
    "status": "completed",
    "answer_text": "A total of 1,247 incidents were recorded across 75 districts...",
    "table": {
      "columns": ["district", "incident_count"],
      "rows": [["Lucknow", 312], ["Kanpur", 289], ...]
    },
    "chart": {
      "type": "bar",
      "title": "Incidents per District",
      "image_data_uri": "data:image/png;base64,..."
    },
    "export_links": {
      "csv": "/runs/{run_id}/export/csv",
      "excel": "/runs/{run_id}/export/excel"
    },
    "follow_up_suggestions": ["Compare with previous month", "Top 5 districts breakdown"],
    "anomaly_flags": [],
    "sql_used": "SELECT district, COUNT(*) AS incident_count FROM incidents_march GROUP BY district ORDER BY incident_count DESC",
    "provider": "openrouter",
    "model": "anthropic/claude-sonnet-4-6",
    "duration_ms": 4210
  }
}
```

**Error cases:**

| Status | Condition |
|--------|-----------|
| 200 (status: degraded) | LLM returned partial output; some fields null |
| 200 (status: failed) | SQL error, DB unavailable, or parser failure — `error_message` populated |
| 422 | Malformed request body (Pydantic validation) |
| 409 | Session already has an active run and concurrency limit reached |

### `GET /runs/{run_id}`

**Purpose:** Fetch a completed or in-progress run by ID.

**Response:** Same envelope with `RunResult` data body.

**Error cases:**
| Status | Condition |
|--------|-----------|
| 404 | Run ID not found |

### `POST /runs/{run_id}/export/csv`  
### `POST /runs/{run_id}/export/excel`

**Purpose:** Stream the run's result table as a CSV or `.xlsx` file download.

**Response:** `Content-Disposition: attachment; filename=run-<run_id>.<csv/xlsx>`

**Error cases:**
| Status | Condition |
|--------|-----------|
| 404 | Run or export data not found |
| 500 | Pandas/openpyxl export failure |

### `GET /health`

**Purpose:** Liveness + readiness probe. Reports provider key presence (not key values).

**Response:**
```json
{
  "ok": true,
  "data": {
    "status": "healthy",
    "providers": {
      "openrouter": true,
      "anthropic": false,
      "gemini": false
    },
    "default_provider": "openrouter",
    "database": "duckdb"
  }
}
```

### `POST /sessions`

**Purpose:** Create a new analysis session.

**Request:** `{}` (empty body)  
**Response:** `{ok: true, data: {session_id: "uuid", created_at: "..."}}`

### `GET /sessions`

**Purpose:** List sessions for the authenticated user (auth TBD for production; pilot allows all).

**Response:** `{ok: true, data: {sessions: [{id, created_at, file_count, is_active}, …]}}`

### `GET /sessions/{session_id}/files`

**Purpose:** List active files in a session.

**Response:** `{ok: true, data: {files: [{id, file_name, row_count, columns, loaded_at}, …]}}`

## Authentication

> **Assumed:** No authentication in pilot phase. Internal on-prem network access control is the deployment-layer perimeter. Authentication (OAuth2 / internal SSO) + audit log (who queried what, when) are planned for production; they are explicit out-of-scope items for Phase 1 and do not block Phase 2.
