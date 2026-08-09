# Zero-Shot Harness — spec-first, AI-native project building

Three skills for building software **spec-first**. Give it a one-line idea; walk away with
a working, tested, phased project — on whatever stack the requirements pick. The skills
are **repo-independent**: install them once and they operate on whatever project repo you
point them at. **No default stack, no boilerplate to clone** — the spec derives the stack,
designs the layout, and a scaffold gate proves the skeleton runs before any feature work.

## The three skills

| Skill | Purpose |
|-------|---------|
| `zero-shot-build` | Idea → working, verified, phased project. Also adds a capability to an existing project. |
| `zero-shot-fix` | Diagnose + fix a bug / error / failing test / drift, then verify. |
| `zero-shot-sync` | Reconcile spec ↔ code (spec wins), then verify. |

## Invoke

The skills are `disable-model-invocation: true` — trigger them explicitly:

```
/zero-shot-build <idea>
/zero-shot-fix <bug | error | "tests" | "drift">
/zero-shot-sync [scope]
```

Or describe the goal in plain English and let the agent route it:

- **build** — "build me a tool/app/service that…", "add X to it" → creates the project /
  adds a capability
- **fix** — "it's erroring on…", "the tests fail" → diagnoses + fixes, then verifies
- **sync** — "make the code match the spec" → reconciles spec ↔ code (spec wins)

## The Spirit

1. **Spec is the source of truth.** Written before code; when they disagree, the spec
   wins (`/zero-shot-sync`).
2. **No default stack.** Your stated preferences are binding; everything else is derived
   from the requirements and recorded with rationale. The scaffold gate proves the
   skeleton runs before any feature work.
3. **Smallest first-time-right win, phase by phase.** Each phase ships the smallest
   increment a human can test, and it must work the *first* time.
4. **A human gates every phase.** Autonomous *within* a phase; stops at each boundary
   for you to test the increment.
5. **AI-native by design.** Every spec includes `spec/agent.md` — the idea evaluated
   against the agentic-patterns catalogue. "No AI capability needed" is a legitimate
   written conclusion; an unexamined design is not.
6. **Real services or it doesn't count.** Gates run against the real external services
   the spec names — the real LLM when the design has AI capability, the production
   database engine always. A stubbed pass is not a pass.

## Install

The `skills/` tree follows the open [Agent Skills](https://agentskills.io) standard, so it
runs on **Claude Code** (as a plugin), **Hermes** (as skills), and any other
Agent-Skills-compatible tool. The `support/` tree is the shared doctrine; only the thin
platform wrappers differ.

### Claude Code

```
/plugin marketplace add smallTechOrg/zero-shot-harness
/plugin install zero-shot-harness@zero-shot-harness
```

The three skills, four sub-agents, and the shared `support/` material all come with the
plugin. Confirm with `/plugin` (it should list `zero-shot-harness` as enabled). Then do
the one-time **[Claude Code autonomy setup](docs/claude-code-autonomy.md)** for each
project you build in — without it, every build command raises a permission prompt and the
"autonomous within a phase" promise breaks.

### Hermes

```bash
hermes skills tap add smallTechOrg/zero-shot-harness
/reload-skills        # or restart Hermes
```

Full instructions (per-skill install, `support/` placement, autonomy model) in
**[docs/hermes-setup.md](docs/hermes-setup.md)**.

## Layout

```
skills/
  zero-shot-build/   SKILL.md + references/hermes-pitfalls.md
  zero-shot-fix/     SKILL.md
  zero-shot-sync/    SKILL.md
support/             shared doctrine the skills reference (as support/…)
  agents/            spec-writer, code-generator, qa-auditor (dual-mode)
                     + project-builder (Claude-only orchestrator — never run on Hermes)
  patterns/          spec-driven, phases, agentic-ai, test-driven, ui-ux, …
  rules/             ai-agents, git, secret-hygiene

.claude-plugin/      Claude Code wrapper: plugin.json + marketplace.json
agents/              Claude-native sub-agent pointers into support/agents/
CLAUDE.md            Claude entry point   (AGENTS.md / .hermes.md = Hermes)
docs/                claude-code-autonomy.md · hermes-setup.md
```

The skills register as slash commands themselves — there is no separate commands layer,
so the skill file is the single source of truth for each flow.

Each `SKILL.md` is the process — follow it exactly; never improvise your own build/fix
flow.

## FAQ

**What if I already have a stack in mind?** State it in the idea:
`/zero-shot-build [idea] — use Python + FastAPI + PostgreSQL`. Stack choices are
binding. With no preference stated, the spec-writer derives the best fit from your
requirements and records the rationale in `spec/architecture.md`.

**Does every project get AI bolted on?** No. `spec/agent.md` is always *written*, but
"no AI capability needed" is a first-class conclusion — deterministic logic that fully
serves the requirements beats an LLM every time.

**What if something breaks?** `/zero-shot-fix [what's broken]` — the qa-auditor role
classifies SPEC vs CODE, the generator fixes, qa-auditor re-gates, the root commits +
pushes.

**What if spec and code drift?** `/zero-shot-sync` — qa-auditor audits, generators fix,
spec wins.

**Why didn't my build land on `main`?** By design. Builds live on feature branches
whose PRs target the branch they were cut from — you review and merge; the build never
merges its own PR.
