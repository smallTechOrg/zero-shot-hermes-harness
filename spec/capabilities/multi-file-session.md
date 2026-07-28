# multi-file-session — Capability

## What it does
Maintain a persistent analysis session that can hold multiple uploaded files active simultaneously, letting the agent see and query across all of them in one run.

## Inputs
- `session_id` (UUID)
- List of `active_files` (each with `file_name`, `normalized_name`, `row_count`, `columns`)

## Outputs
- Updated session state: `active_files` list, `file_count`, `last_query`
- SQL generator sees all active table names; can produce JOINs or UNIONs

## Storage
- `Session` row (SQLite) tracks metadata
- Each `UploadedFile` row tracks per-file metadata
- DuckDB holds the actual tables; all tables in the same DuckDB connection are queryable together

## Error cases
- Upload of a second file with the same normalized name → old file replaced, old table dropped
- Duplicate active file in the same upload → 422 with message "File already active in this session"
- Incompatible schemas across files for a JOIN → LLM flags it in `anomaly_flags`; suggests column mapping

## Success criteria
- Two CSVs uploaded in the same session; query "show rows from both" returns combined/joined result
- Session survives browser refresh (frontend stores `session_id` in `localStorage`)
- Removing a file sets `is_active = False` in DB and drops its DuckDB table
