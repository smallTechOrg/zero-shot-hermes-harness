# Project Layout — Principles

Every project this harness builds follows the layout **the spec-writer designs for it** in
`spec/architecture.md` (`## Layout`), honoring the principles below. There is no fixed
skeleton and no default stack — the layout is derived from the chosen stack, then made
real in the scaffold stage and verified by the scaffold gate (`phases.md`)
**before** any feature slice is built. From that point on, generators extend the scaffold
in place.

---

## README Requirements (Mandatory)

Every generated project **must** have a README that:

1. **States the working directory for all commands** — put "all commands run from the
   repo root" (or the exact directory) before any other content.
2. **Uses the stack's runner prefix on every command** (e.g. `uv run`, `npx`, `bun`) —
   bare commands fail unless an environment is manually activated, which users won't do.
3. **Includes the verification command after every setup command** — e.g. after running
   migrations, the command that proves they applied (blank output = silent failure). The
   user must be able to verify the setup worked.
4. **Stays accurate** — every README command is run before a phase is marked complete. A
   wrong README fails the build regardless of whether the code works.

---

## Source Code Rules (Non-Negotiable)

1. **All application source lives inside a dedicated source directory** (backend) and a
   dedicated frontend directory (if there is a UI). Never place application files at the
   repo root. The root is for project config, `spec/`, `.env.example`, and the README.
2. **One package/module root only.** The scaffold establishes one import root; extend it
   in place — never create a second package beside it, never copy it to a new name. Two
   packages = dead code + two sources of truth.
3. **Tests live at the repo root** (`tests/` or the stack's convention), outside the
   source package, with unit and integration tiers separated.
4. **`spec/` is part of the project.** The spec files are committed with the code they
   govern — they are the durable memory every session re-reads.
5. **`.env.example` documents every env var**; `.env` holds the real values and is
   gitignored, never staged (`../rules/secret-hygiene.md`).

---

## The Scaffold (replaces a fixed boilerplate)

The spec-writer designs the concrete tree — directories, entry point, config module,
test harness — as part of `spec/architecture.md`. The scaffold stage then builds it as a
**minimal runnable skeleton**: the app boots via its documented run command, a smoke test
passes, and the working tree is committed, *before* Phase 1 slices begin. That scaffold
gate is what a cloned boilerplate used to guarantee ("tests pass out of the box") — now
it is guaranteed per-project, on whatever stack the spec chose.

A good scaffold, whatever the language:

- **entry point** — one documented run command starts the app (pinned interpreter/runtime,
  non-default port, env-overridable);
- **config module** — typed settings loaded from env/`.env`, validated at startup, secret
  fields never printable;
- **persistence** — engine/session setup plus the migration tool wired from day one if
  the project has a database;
- **test harness** — the test runner configured with automated setup/teardown against the
  production engine, one command to run;
- **observability** — structured logging wired, not deferred.

## AI-Native Layout Rules (for any project with LLM capabilities)

When `spec/agent.md` gives the project AI capabilities, the layout additionally provides:

1. **An LLM abstraction layer** — application code calls one internal client interface,
   never a provider SDK/API directly; providers are swappable adapters behind it, and the
   model name comes from configuration.
2. **Prompts are files, not string literals** — kept in a dedicated prompts directory,
   loaded at runtime, reviewable in diffs.
3. **The agent graph/loop is its own module** — state, nodes/steps, routing, and assembly
   live together, mirroring the structure documented in `spec/agent.md`, so the drift
   audit can compare code to spec mechanically.
4. **Retry/backoff at the provider boundary** — rate limits and transient errors are
   handled once, in the adapter, with actionable errors for auth/model failures.
5. **Every LLM call is instrumented** — latency, token/cost signal, and error logged per
   call (`engineering-practices.md` → Observability).

## Structural Rules (any stack)

1. **A response envelope at every API boundary** — one consistent success/error shape;
   a failed run is a structured, actionable error, never a naked 500 or a stack trace.
2. **Singletons are resettable** — settings/DB/client singletons expose a reset seam so
   tests can isolate state.
3. **Tools/helpers are pure functions** where possible — inputs → typed outputs, no
   hidden state.
4. **Gates run against real services** — real LLM/API keys from `.env`, the production
   database engine (`tech-stack.md`).

> *Field reference:* the original harness shipped these principles as a committed Python
> baseline — FastAPI app factory, LangGraph graph module, SQLAlchemy session, structlog,
> static single-origin frontend, alembic wired, tests green on a fresh clone. That tree
> remains a worked example of this file's rules, not a requirement: the same shape exists
> for a Node service, a Go CLI, or any stack the spec picks.
