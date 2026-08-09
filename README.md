# Zero-Shot SDD Skills (v2) — Hermes skill harness

Three Hermes skills for building agentic software **spec-first**. Give it a
one-line idea; walk away with a working, tested, phased agent. The skills are
**repo-independent** — install them into Hermes once, and they operate on
whatever agent repo you point them at.

## Install

The reliable way — install each skill once into `~/.hermes/skills/` (deterministic;
the skills show up in `hermes skills list` immediately and survive `/reload-skills`):

```bash
hermes skills install smallTechOrg/zero-shot-hermes-harness/skills/zero-shot-build --name zero-shot-build --yes
hermes skills install smallTechOrg/zero-shot-hermes-harness/skills/zero-shot-fix   --name zero-shot-fix   --yes
hermes skills install smallTechOrg/zero-shot-hermes-harness/skills/zero-shot-sync  --name zero-shot-sync  --yes
```

Then, in a Hermes session, run **`/reload-skills`** (or restart Hermes). Confirm
with `hermes skills list` — you should see `zero-shot-build`, `zero-shot-fix`,
`zero-shot-sync` marked `enabled`.

> The installed copy lives in `~/.hermes/skills/`, separate from any skills Hermes
> creates or learns on its own — nothing collides or gets overwritten. To pull
> harness updates later, re-run the three `install` commands with `--force`.

**Optional — tap the repo instead of installing.** Tapping reads the skills
straight from the repo's `skills/` dir (your unique copy stays in the repo):

```bash
hermes skills tap add smallTechOrg/zero-shot-hermes-harness
hermes skills tap remove smallTechOrg/zero-shot-hermes-harness   # to undo
```

Note: tapped skills can be slow or intermittently unavailable in `hermes skills
list`/`search` because they're fetched live from GitHub. If a tapped skill
doesn't appear, use the `hermes skills install` method above, or verify with
`hermes skills inspect smallTechOrg/zero-shot-hermes-harness/skills/zero-shot-build`
(the full tap-qualified name).

## Invoke

The skills are `disable-model-invocation: true` — trigger them explicitly:

```
/zero-shot-build <idea>
/zero-shot-fix <bug | error | "tests" | "drift">
/zero-shot-sync [scope]
```

Or describe the goal in plain English and let Hermes route it:

- **build** — "build me an agent that…", "add X to it" → creates the agent /
  adds a capability
- **fix** — "it's erroring on…", "the tests fail" → diagnoses + fixes, then
  verifies
- **sync** — "make the code match the spec" → reconciles spec ↔ code (spec
  wins)

## The three skills

| Skill | Purpose |
|-------|---------|
| `zero-shot-build` | Idea → working, verified, phased agent. Also adds a capability to an existing agent. |
| `zero-shot-fix` | Diagnose + fix a bug / error / failing test / drift, then verify. |
| `zero-shot-sync` | Reconcile spec ↔ code (spec wins), then verify. |

## The Spirit

1. **Spec is the source of truth.** Written before code; when they disagree,
   the spec wins (`/zero-shot-sync`).
2. **Lean harness, not a framework.** `support/` holds rules and patterns that
   keep every session consistent. The product runtime stays provider-agnostic.
3. **Smallest first-time-right win, phase by phase.** Each phase ships the
   smallest increment a human can test, and it must work the *first* time.
4. **A human gates every phase.** Autonomous *within* a phase; stops at each
   boundary for you to test the increment.
5. **Real LLM/API or it doesn't count.** Gates and tests run against the real
   model. A stubbed pass is not a pass.

## Layout

```
skills/
  zero-shot-build/   SKILL.md + references/hermes-pitfalls.md
  zero-shot-fix/     SKILL.md
  zero-shot-sync/    SKILL.md
support/             shared material the skills reference (../../support/…)
  agents/            spec-writer, code-generator, qa-auditor (dual-mode roles)
  patterns/          spec-driven, phases, agentic-ai, test-driven, ui-ux, …
  rules/             ai-agents, git, secret-hygiene
  commands/          zero-shot-{build,fix,sync} (plain-English wrappers)
```

Each `SKILL.md` is the process — follow it exactly; never improvise your own
build/fix flow.

## FAQ

**What if I already have a stack in mind?** State it in the idea:
`/zero-shot-build [idea] — use Python + FastAPI + PostgreSQL`. Stack choices
are binding.

**What if something breaks?** `/zero-shot-fix [what's broken]` — the
qa-auditor role classifies SPEC vs CODE, the generator fixes, qa-auditor
re-gates, the root commits + pushes.

**What if spec and code drift?** `/zero-shot-sync` — qa-auditor audits,
generators fix, spec wins.

**Why didn't my build branch merge to `main`?** By design. Builds live on
feature branches whose PRs target the branch they were cut from, never `main`.
