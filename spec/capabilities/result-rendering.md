# result-rendering — Capability

## What it does
Turn raw query results into a structured answer: prose summary + table data + optional chart recommendation.

## Inputs
- `result_rows`, `result_columns`
- `input_text` (for summary context)

## Outputs
- `answer_text` (prose summary)
- `chart_type` recommendation
- `follow_up_suggestions`, `anomaly_flags`

## External calls
- LLM (prose summary + suggestions + flags in one batched call)

## Error cases
- LLM call fails → route to `handle_error`
- 0 rows → answer becomes "No matching rows found"; `follow_up_suggestions` = broader search suggestions

## Success criteria
- `answer_text` is non-empty on `status = completed`
- `answer_text` directly answers the user's question using generated data, not boilerplate
