# Claude Code — Entry Point

This repo is the **zero-shot-harness**: a spec-first harness for building agents,
shipped as a Claude Code plugin. It is *not* an agent project itself — the skills
here operate on whatever agent repo you point them at.

For the Hermes-native orientation see `AGENTS.md` / `.hermes.md`. The `skills/`
and `support/` trees are shared by both platforms; only the wrapper differs.

## Install

```bash
/plugin marketplace add smallTechOrg/zero-shot-harness
/plugin install zero-shot-harness@zero-shot-harness
```

Then `/zero-shot-build <idea>` · `/zero-shot-fix <bug>` · `/zero-shot-sync [scope]`.

## Entry points

| Command | Purpose |
|---------|---------|
| `/zero-shot-build [idea]` | Idea → working, verified, phased agent. Also adds a new capability. |
| `/zero-shot-fix [target]` | Diagnose + fix a bug, error, failing test, or spec/code drift, then verify. |
| `/zero-shot-sync [scope]` | Reconcile spec ↔ code so they match (spec wins), then verify. |

All three are manual (`disable-model-invocation: true`). Each is invocable as a
skill **and** as a slash command — the command defers to the skill, so the two
never drift.

## Starting a new agent project

Clone the boilerplate — a working FastAPI + LangGraph + SQLite baseline whose
capability slot is `transform_text`, tests passing out of the box:

```bash
gh repo create my-agent --template smallTechOrg/zero-shot-boilerplate --private --clone
cd my-agent && claude
```

Then `/zero-shot-build <your idea>`. The harness comes from this plugin — the
boilerplate carries only `spec/`, `src/`, `tests/`, and `frontend/`.

## The team

`/zero-shot-build` delegates to **agent-builder**, which plans phases, fans out
**code-generator** instances per independent slice in parallel, and gates each
with **qa-auditor**. **spec-writer** is the single design authority.

| Agent | Role |
|-------|------|
| agent-builder | Orchestrator — plans phases, fans out generators, owns git/PR |
| spec-writer | Writes the FULL spec (architecture, agent graph, phased roadmap) and self-reviews |
| code-generator | Implements ONE independent slice plus tests — parallelised, one per slice |
| qa-auditor | Independent review, runs gates, audits spec↔code drift — read-only |

Each `agents/<name>.md` is a thin Claude-native pointer; the full definition
lives in `support/agents/<name>.md`, shared with Hermes.

> **Platform note.** `agent-builder` is **Claude-only** — it relies on native
> sub-agent spawning. On Hermes the root session orchestrates directly and the
> other three roles run via `delegate_task` or inline. The `support/agents/`
> definitions for spec-writer, code-generator, and qa-auditor are identical on
> both platforms.

## Source of truth (obey, do not restate)

```
support/rules/ai-agents.md          ← mandatory session rules — read first
support/rules/git.md                ← branch/PR/commit-push discipline
support/rules/secret-hygiene.md     ← secrets never in code; .env untracked
support/patterns/spec-driven.md     ← spec is the source of truth
support/patterns/phases.md          ← phase model and per-phase gates
support/patterns/test-driven.md     ← what counts as a real test
support/patterns/tech-stack.md      ← generic stack rules
support/patterns/code.md            ← naming, structure, conventions
support/patterns/agentic-ai.md      ← catalogue of agentic patterns
support/patterns/engineering-practices.md
support/patterns/ui-ux.md
```

## Key rules (summary — full rules in `support/rules/ai-agents.md`)

- Never write application code before reading the full spec
- Never skip a phase — complete phase N before starting phase N+1
- Commit every logical unit of work; a commit that isn't pushed doesn't exist
- The human tests each phase before the next starts — stop at the boundary and wait
- Each phase is the smallest user-testable win and must work the *first* time
- Tests and evals run against the real LLM/API using keys from `.env` — a stubbed pass is not a pass
- `main` is boilerplate-only — application code never reaches it
