# chart-recommendation — Capability

## What it does
Choose an appropriate chart type (bar, line, pie, or skip) based on the result shape, and render it as a PNG data URI.

## Inputs
- `result_columns`, `result_rows`

## Outputs
- `chart_type` (one of: `bar`, `line`, `pie`, `table`, or `null`)
- `chart_png_base64` (PNG data URI when `chart_type != null`)

## External calls
- Matplotlib (server-side render)
- Optional: LLM for ambiguous shapes (e.g. "do you want time-series or categorical?")

## Error cases
- Matplotlib render failure → log error, set `chart_type = null`; answer + table still returned
- >500 rows without explicit chart request → skip chart, note in answer
- 0 rows → skip chart entirely
- Non-numeric columns only → default to table view

## Success criteria
- Chart PNG renders in < 2 s for results up to 500 rows
- Output is a valid PNG data URI that the frontend can embed directly (`<img src="data:image/png;base64,...">`)
- Proactive: "Suggested visualisation" text accompanies the chart in the Phase 2 UI
