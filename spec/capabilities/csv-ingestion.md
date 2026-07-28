# csv-ingestion — Capability

## What it does
Accepts a CSV or Excel upload for an analysis session, validates the file, ingests it into DuckDB, and records metadata so it can be referenced in SQL generation.

## Surface ownership
- `frontend/public/app.js` upload form + progress (UI slice of Phase 1)
- `src/api/runs.py` intake/validation routes (backend slice)

## Contract
- **Input:** `multipart/form-data` or `active_files: ["name.csv"]` referencing an already-stored blob
- **Output:** `UploadedFile` row + DuckDB table registered; file appears in session files list
- **Failure modes:**
  - Corrupt file: `status: failed`, UI shows "Could not read this file"
  - Duplicate name within session: replaced, old row `is_active=False`
  - Empty file: accepted; `row_count = 0`; agent still references the empty table on query

## Invariants
- File names are sanitised to valid DuckDB identifiers (alphanumeric + `_`)
- Original filename preserved for display; `normalized_name` used for SQL
- Max file size enforced server-side (assumed: 200 MB); reject with `422` if exceeded
