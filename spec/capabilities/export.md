# export — Capability

## What it does
Package the current result rows as downloadable CSV or `.xlsx` and stream them back to the browser.

## Inputs
- `result_rows`, `result_columns`
- requested format (`csv` or `excel`)

## Outputs
- Streaming HTTP response with `Content-Disposition: attachment`
- File name pattern: `run-<run_id>.<csv|xlsx>`

## External calls
- Pandas `DataFrame.to_csv()` for CSV export
- Pandas + openpyxl for `.xlsx` export

## Error cases
- Pandas/openpyxl failure → 500 surfaced as `status: failed` in the next read
- No result rows → 404 with message "No data to export for this run"

## Success criteria
- CSV download opens in Excel without encoding issues (UTF-8 BOM)
- `.xlsx` preserves column headers and cell values exactly
- Export of 50,000 rows completes in < 3 s
