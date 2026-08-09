# Zero-Shot SDD Skills (v2) — entry point

This repo is a **skill package** (repo-independent) serving Hermes, Claude Code, and any
Agent-Skills-compatible tool. The authoritative orientation for Hermes is `.hermes.md`.
This file is a short mirror.

## What it is

Three skills for spec-driven, AI-native project development, plus the shared
`support/` material they reference:

- `skills/zero-shot-build` — idea → working, verified, phased project
- `skills/zero-shot-fix` — diagnose + fix a bug/error/failing test/drift, verify
- `skills/zero-shot-sync` — reconcile spec ↔ code (spec wins), verify

## Install (Hermes)

```bash
hermes skills tap add smallTechOrg/zero-shot-harness
/reload-skills        # or restart Hermes
```

(Per-skill `hermes skills install` also works — see the README: it needs the shared
`support/` tree copied to `~/.hermes/support`.)

Then `/zero-shot-build <idea>` · `/zero-shot-fix <bug>` · `/zero-shot-sync`.

The skills operate on whatever project repo you point them at — not on this repo.
There is no default stack: the spec derives it from your requirements. Follow each
`SKILL.md` exactly; it is the process.
