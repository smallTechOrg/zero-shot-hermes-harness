# sql-generation — Capability

## What it does
Convert an LLM-produced plan + natural-language query into safe, executable SELECT SQL for the active file(s).

## Inputs
- `plan` list (from `plan_query` node)
- `input_text` (user query)
- `active_files` list → used to look up available table names + columns in DuckDB

## Outputs
- `generated_sql` string
- `sql_error` string (on failure; otherwise `None`)

## External calls
- LLM (one batched call per generation/repair attempt)
- DuckDB `PRAGMA table_info(...)` or `SHOW COLUMNS` to confirm table/column names

## Error cases
- LLM returns non-SELECT text → `sql_error = "Generated SQL is not SELECT-only"`
- LLM returns syntactically invalid SQL → retry once with error fed back in
- Table/column names unavailable → surfaced to user as clarification request
- After 2 failed attempts → route to `handle_error`; SQL shown so user can verify/retry

## Success criteria
- Generated SQL parses and executes without error
- SQL is logged and returned to the UI under "Show SQL"
- All columns referenced in SQL are present in at least one active file
