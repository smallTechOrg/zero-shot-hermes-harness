# UI

## UI Type

Zero-build static web app served by FastAPI at `/app/`. Single-origin: same server, no CORS, no bundler, no Node dependency. The frontend is a set of plain HTML + CSS + vanilla JS files in `frontend/public/`. JS framework adoption is deferred unless client-side complexity demands it.

> **Assumed:** Web UI is primary surface. REST API is exposed for programmatic consumers. CLI surface is also exposed (via `uv run data-agent11 --query "..."`) for power users and automation.

## Views / Screens

### Screen: Session Dashboard (`/app/`)

**Purpose:** The landing page. User creates or resumes sessions, sees active files (Phase 1: one at a time), types a natural-language question, and sees the answer + artefacts.

**Key elements:**
- **Header bar**: App title ("UP Police Data Analyst"), provider badge (shows which LLM provider is active), session ID (copyable UUID).
- **File-upload zone**: Drag-and-drop or file-picker for CSV and Excel files. Shows upload progress, parse status, column list, row count after ingest. **Labelled stub in Phase 1:** "Multi-file Manager" panel — share a session ID to enable multi-file mode; rest is stub-labelled ("Phase 2").
- **Query input**: Large textarea with "Ask about your data…" placeholder; sends on Ctrl+Enter.
- **Answer panel** (real, Phase 1): Renders structured answer — prose summary, result table (scrollable, sortable headers), chart image (PNG from Matplotlib/Plotly), and action buttons.
- **Action bar** (real, Phase 1): "Regenerate chart", "Export CSV", "Export Excel" (stub-labelled as "Phase 1" alongside real buttons when implemented).
- **Feedback / Proactive panel** (Phase 2 stub in Phase 1): "Suggested follow-up questions" and "Anomaly flags" shown as greyed-out cards with a "Coming in Phase 2" badge.
- **Error state** (real, Phase 1): Agent-level error shown as an alert: error message, "Show SQL" toggle (displays SQL that was generated), "Ask as different question" reset.

**Actions available:**
- Upload CSV / Excel (Phase 1 — single file)
- Ask a question in natural language
- View answer (text + table + chart)
- Export result as CSV (Phase 1) or Excel (Phase 1)
- Show generated SQL for verification
- Reset / ask a new question
- Open multi-file manager (stub, Phase 2)
- View session history (stub, Phase 2)
- Accept follow-up suggestion (stub, Phase 2)

### Screen: Error / Clarification Overlay

**Purpose:** Shown when the agent needs human clarification (ambiguous query, missing context, data quality issue).

**Key elements:**
- Human-readable error or clarification prompt (e.g. "Which column should I use for dates? Found: `dt`, `date_`, `incident_dt`")
- Potential SQL shown (editable or copyable)
- "Best-guess answer" option with an "uncertain" flag
- "Retry with clarification" button

## Error States

| State | UI Treatment |
|-------|-------------|
| LLM unavailable | Alert banner: "AI service temporarily unavailable — your data is safe. Retry or check back later." Show last-known SQL. |
| CSV corrupt / unparseable | Per-file error card: "Could not read this file. Check it's a valid CSV or Excel file." Suggest export from source system. |
| Query timeout (MsSQL, Phase 2) | Alert: "Database query timed out. Try narrowing your filter or date range." |
| Empty result | Informational: "This query returned no rows. Try broadening date range or removing filters." |
| Cache miss (Phase 2) | Transparent: "Querying live database…" spinner; note that repeated queries are faster. |
| Auth missing | Config screen: "LLM API key not configured. Add `OPENROUTER_API_KEY` to your `.env` and restart." Never falls back silently in a way that hides the real failure. |

## Tech Stack

- Serve static files via FastAPI `StaticFiles` mount at `/app/`
- Charts rendered server-side as PNG (Matplotlib) served as data-URI in JSON; no frontend chart library required
- Responsive layout: CSS Grid + Flexbox; mobile-friendly ( officers may use tablets)

> **Assumed:** No JS framework in Phase 1 — plain HTML/CSS/JS keeps the gate to "served page contains real UI and its linked CSS/JS return 200 non-empty." A JS framework is adopted only if client-side state/routing complexity exceeds what vanilla JS handles cleanly.
