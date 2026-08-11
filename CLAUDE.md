# Claude Code — Entry Point

This repo is the **zero-shot-harness**: a spec-first harness for building projects,
AI-natively, shipped as a Claude Code plugin. It is *not* a project itself — the skills
here operate on whatever project repo you point them at, on whatever stack the
requirements pick. **There is no default stack and no required boilerplate.**

For the Hermes-native orientation see `AGENTS.md` / `.hermes.md`. The `skills/` and
`support/` trees are shared by both platforms (and any Agent-Skills-compatible tool);
only the wrapper differs.

## Install

```
/plugin marketplace add smallTechOrg/zero-shot-harness
/plugin install zero-shot-harness@zero-shot-harness
```

Then, in the project you'll build in, set up autonomy once — copy the permissions preset
from **[docs/claude-code-autonomy.md](docs/claude-code-autonomy.md)** into that project's
`.claude/settings.json`. Without it, every build command raises a permission prompt and
the autonomous phase loop degrades to a click-through session.

## Entry points

The three skills register as slash commands directly (there is no separate `commands/`
layer — the skill is the only artifact, so nothing can drift):

| Skill | Purpose |
|---------|---------|
| `/zero-shot-build [idea]` | Idea → working, verified, phased project. Also adds a new capability. |
| `/zero-shot-fix [target]` | Diagnose + fix a bug, error, failing test, or spec/code drift, then verify. |
| `/zero-shot-sync [scope]` | Reconcile spec ↔ code so they match (spec wins), then verify. |

All three are manual (`disable-model-invocation: true`) — you invoke them; the model
never auto-triggers them.

## Starting a new project

Any repo works — brand new (`git init my-project`) or existing. No template to clone:
intake captures your constraints, the spec-writer derives the best-fit stack from the
requirements (your stated preferences are binding), designs the layout, and the build
proves a minimal runnable skeleton via the **scaffold gate** before any feature work.

```bash
git init my-project && cd my-project && claude
# then: /zero-shot-build <your idea>
```

## The team

`/zero-shot-build` runs intake and the human testing gates in the root session, then
delegates each phase to **project-builder**, which plans the phase, fans out
**code-generator** instances per independent slice — all in one message, maximum
parallelism — and gates each slice with **qa-auditor** the moment it lands.
**spec-writer** is the single design authority.

| Agent | Role |
|-------|------|
| project-builder | Orchestrator — plans phases, fans out generators, owns git/PR for the build |
| spec-writer | Writes the FULL spec (architecture with stack + layout, the AI-native design in `spec/agent.md` — always, phased roadmap) and self-reviews |
| code-generator | Implements ONE independent slice plus tests — parallelised, one per slice; also builds the scaffold |
| qa-auditor | Independent review, runs gates against real services, audits spec↔code drift — read-only |

Each `agents/<name>.md` is a thin Claude-native pointer; the full definition lives in
`support/agents/<name>.md`, shared with Hermes.

> **Platform note.** `project-builder` is **Claude-only** — it relies on native
> sub-agent spawning. On Hermes the root session orchestrates directly and the other
> three roles run via `delegate_task` or inline. The `support/agents/` definitions for
> spec-writer, code-generator, and qa-auditor are identical on both platforms.

## AI-native, always

`spec/agent.md` is written for **every** project — the spec-writer evaluates each idea
against the agentic-patterns catalogue (`support/patterns/agentic-ai.md`) and records
either the chosen composition or an explicit, reasoned "no AI capability needed". A
missing file is a design hole; a written "no" is a design decision.

## Source of truth (obey, do not restate)

```
support/rules/ai-agents.md          ← mandatory session rules — read first
support/rules/git.md                ← branch/PR/commit-push discipline
support/rules/secret-hygiene.md     ← secrets never in code; .env untracked
support/patterns/spec-driven.md     ← spec is the source of truth
support/patterns/phases.md          ← scaffold gate, phase model, per-phase gates
support/patterns/test-driven.md     ← what counts as a real test
support/patterns/tech-stack.md      ← generic stack rules (no default stack)
support/patterns/project-layout.md  ← layout principles (the tree is designed per spec)
support/patterns/code.md            ← universal conventions
support/patterns/agentic-ai.md      ← the AI-native lens + pattern catalogue
support/patterns/engineering-practices.md
support/patterns/ui-ux.md
```

## Key rules (summary — full rules in `support/rules/ai-agents.md`)

- Never write application code before reading the full spec
- Never skip a phase — complete phase N before starting phase N+1
- Commit every logical unit of work; a commit that isn't pushed doesn't exist
- The human tests each phase before the next starts — stop at the boundary and wait
- Each phase is the smallest user-testable win and must work the *first* time
- Tests and gates run against the real external services the spec names, keys from
  `.env` — a stubbed pass is not a pass
- Builds live on feature branches and land only through PRs the user merges — never
  directly on the default branch
