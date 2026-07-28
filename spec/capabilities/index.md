# data-agent11 — Spec Index

**Project:** UP Police Data Analyst Agent
**Status:** Spec complete — ready for build
**Spec review:** PASS (root inline)

---

## Spec Files

| File | What it covers |
|---|---|
| `architecture.md` | System overview, component map, layers, data flow, stack, deployment model |
| `agent.md` | LangGraph graph (planner-first data analyst pattern) |
| `data.md` | Entities, fields, relationships, lifecycle |
| `api.md` | REST endpoints, CLI surface |
| `ui.md` | Web UI screens and interactions |
| `roadmap.md` | Phased plan with goals, slices, gates, handoff |
| `README.md` | Spec usage guide |

## Capabilities

| Capability | File |
|---|---|
| CSV/Excel ingest, validation, DuckDB load | `csv-ingestion.md` |
| Natural-language query execution | `nl-query.md` |
| NL to SQL, planner-first generation | `sql-generation.md` |
| Text answer + table + proactive suggestions | `result-rendering.md` |
| Chart type selection + PNG render | `chart-recommendation.md` |
| CSV / `.xlsx` export | `export.md` |
| Multi-file sessions, persistent state | `multi-file-session.md` |
