# Data Model

## Storage Technology

> **Assumed:** Phase 1 uses DuckDB (file-based, zero-config, SQL-compatible, supports `SELECT * FROM read_csv_auto(...)`) as the primary analytical engine, persisted to `data/app.db` in the repo. SQLite is also supported as a fallback. Phase 2 adds MsSQL via `pyodbc` with a query-cache layer (cached results stored in DuckDB). Session state and run history live in SQLAlchemy-backed SQLite (the existing `app.db`); the cache layer is separate from the run-history `RunRow` table.

## Entities

### Entity: Run (run history)

Represents every user-initiated analysis run (one per `POST /runs` call).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str (UUID) | yes | Primary key |
| session_id | str | yes | FK to session; groups runs belonging to the same conversation |
| user_query | str | yes | The original natural-language question |
| generated_sql | str | no | SQL executed against the data (shown for verification) |
| answer_text | str | no | Natural-language answer returned to the user |
| table_data | JSON | no | Result rows as list of dicts |
| chart_spec | JSON | no | Chart configuration (type, columns) if a chart was generated |
| exported_files | JSON | no | List of export artifact keys |
| status | str | yes | `completed` / `failed` / `degraded` |
| error_message | str | no | Fatal error string if status is `failed` |
| llm_provider | str | no | Provider used for this run |
| llm_model | str | no | Model identifier used |
| input_files | JSON | no | List of file names active at run time |
| created_at | datetime | yes | Timestamp |
| updated_at | datetime | yes | Last-modified timestamp |

### Entity: Session

Represents a persistent user conversation (browser-storage-backed ID echoed by the frontend).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str (UUID) | yes | Primary key |
| created_at | datetime | yes | Creation timestamp |
| file_count | int | yes | Number of files currently active in the session |
| active_files | JSON | yes | List of `{name, rows, columns, loaded_at}` dicts |
| last_query | str | no | Most recent user query (for resumption) |
| is_active | bool | yes | Soft-delete; inactive sessions are not listed |

### Entity: UploadedFile

Represents a single CSV/Excel upload, tracked per session.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str (UUID) | yes | Primary key |
| session_id | str | yes | FK to session |
| file_name | str | yes | Original filename |
| normalized_name | str | yes | Sanitised table name in DuckDB |
| row_count | int | yes | Rows after ingestion (0 = corrupt/unparesable) |
| column_count | int | yes | Number of columns detected |
| columns | JSON | yes | List of column names + inferred types |
| file_size_bytes | int | yes | Original upload size |
| is_active | bool | yes | Set false when replaced or removed |
| loaded_at | datetime | yes | Ingestion timestamp |

### Entity: QueryCache

Phase 2 cache of MsSQL query results (keyed by normalised SQL hash).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str (UUID) | yes | Primary key |
| sql_hash | str | yes | SHA-256 of normalised SQL (indexed) |
| sql | str | yes | The original SQL text (for debugging) |
| result_rows | JSON | yes | Full result set |
| row_count | int | yes | Number of rows |
| db_source | str | yes | `duckdb_local` or `mssql_<server_id>` |
| created_at | datetime | yes | Cache-insertion time |
| expires_at | datetime | no | Optional TTL; null = indefinite |

### Relationships

```
Session 1 ── N UploadedFile   (session_id)
Session 1 ── N Run            (session_id)
Run N ── 1 QueryCache         (phase 2 only; sql_hash)
```

## Data Lifecycle

| Event | Action |
|-------|--------|
| CSV/Excel uploaded | `UploadedFile` row created; bytes streamed to DuckDB via `read_csv_auto` or openpyxl; table registered in DuckDB |
| File replaced in same slot | Old `UploadedFile` row `is_active=False`; new row created; old DuckDB table dropped; new one created |
| Session expires (no activity > 24 h) | Frontend may discard; backend keeps rows (archive-then-purge planned for production) |
| Query executed | `Run` row written; `generated_sql`, `answer_text`, `table_data` populated |
| MsSQL query returned (Phase 2) | Result checked against `QueryCache.sql_hash`; on miss, result stored |
| Cache TTL hit | `QueryCache` row eligible for TTL-based eviction |
| Auth/audit production | `Run.error_message` + query text + user ID written to audit log (planned, not Phase 1) |

## Sensitive Data

| Field | Notes |
|-------|-------|
| `openrouter_api_key`, `anthropic_api_key`, `gemini_api_key` | `.env` only, never logged or echoed; `health` endpoint reports *presence only* |
| `Run.user_query` | May contain case IDs or PII from police data; treat as sensitive — not sent to external LLMs for storage, only for inference; audit log planned |
| `UploadedFile` rows | Filenames may contain case or officer identifiers |
| `QueryCache.sql` | May expose table/column names; internal only |

> **Assumed:** Deployment is on-prem on an internal network; no data leaves the organisation's perimeter in Phase 1. Phase 2 openrouter inference goes through the LLM provider — upstream LLM terms govern prompt data handling; a data-classification review is planned for production.
