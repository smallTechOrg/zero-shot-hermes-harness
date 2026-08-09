# Zero-Shot SDD Skills (v2) — entry point

This repo is a **Hermes skill package** (repo-independent). The authoritative
orientation for Hermes is `.hermes.md`. This file is a short mirror.

## What it is

Three Hermes skills for spec-driven agent development, plus the shared
`support/` material they reference:

- `skills/zero-shot-build` — idea → working, verified, phased agent
- `skills/zero-shot-fix` — diagnose + fix a bug/error/failing test/drift, verify
- `skills/zero-shot-sync` — reconcile spec ↔ code (spec wins), verify

## Install (Hermes)

```bash
hermes skills tap add smallTechOrg/zero-shot-harness
/reload-skills        # or restart Hermes
```

Then `/zero-shot-build <idea>` · `/zero-shot-fix <bug>` · `/zero-shot-sync`.

The skills operate on whatever agent repo you point them at — not on this repo.
Follow each `SKILL.md` exactly; it is the process.
