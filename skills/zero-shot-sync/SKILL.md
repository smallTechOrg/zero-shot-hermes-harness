---
name: zero-shot-sync
description: Reconcile spec and code so they match — spec wins — then verify (whole-tree drift audit).
argument-hint: [optional path or capability to scope to]
disable-model-invocation: true
---

You are the ROOT SESSION orchestrating a spec↔code sync by running the specialist roles in `support/agents/` — delegated via your platform's mechanism (Claude Code: the Task tool / native sub-agents; Hermes: `delegate_task`) when available, **inline otherwise** (read the role file as a checklist). Verify every handback. **Spec is the source of truth — when spec and code disagree, fix the code** (`support/patterns/spec-driven.md`). Optional scope in `$ARGUMENTS`; otherwise the whole project. Run autonomously to a CLEAN audit; pause only on a hard blocker or if a divergence reveals the *spec* is wrong (surface it — don't silently rewrite the spec to match code).

> **Shared material** is referenced as `support/…` — the harness's shared tree, two levels
> up from this file (`skills/<name>/SKILL.md` -> `support/`) in the repo checkout, the
> Hermes tap, and the installed Claude plugin. For a per-skill Hermes install, the README
> says how to place it at `~/.hermes/support`.

**qa-auditor runs FIRST** — read-only, it finds and classifies every divergence and its direction; its verdict routes each fix to the **code-generator** role by named surface (per the project's declared layout in `spec/architecture.md`). You (the root session) own the commit + push.

## Step 1 — Audit (qa-auditor first, drift mode)

Invoke **qa-auditor** in drift mode (whole-tree). For each divergence it returns: severity, the **direction** (code-wrong vs spec-wrong), and **which surface** (per the spec's layout) + file(s). CLEAN → report and stop. It stays read-only and never spawns agents.

## Step 2 — Triage by direction

Per divergence, act on qa-auditor's direction:
- **Code wrong, spec right** (common, default) → fix the code, routed to the surface qa-auditor named.
- **Spec wrong, code right** → do **not** auto-edit the spec to match code. Surface to the user with the specific mismatch and a proposed spec change; wait. (Silently editing the spec defeats spec-driven development.)
- **Undocumented behavior** → remove from code, or if intended, surface as a spec addition for confirmation.

Handle High severity first, then Medium; Low only if in scope.

## Step 3 — Reconcile code (routed by surface, parallel where independent)

Group the "code wrong" divergences **by surface** — the surfaces the project's `spec/architecture.md` layout declares (e.g. one invocation for the backend source tree, one for the frontend/UI surface) — then run the **code-generator** role per group.

Independent groups (disjoint paths) run **concurrently** when delegated, sequentially when inline. Give each generator the spec section + the offending file(s); it edits code to match the spec and adds/updates a test asserting the spec'd behavior. Group divergences that touch the same files into one invocation.

## Step 4 — Verify (qa-auditor, gate mode)

Invoke **qa-auditor** in gate mode to confirm the reconciliation didn't break anything (tests green against the real external services the spec names, keys from `.env`, plus smoke + UI tests if there's a UI). BLOCKED → re-invoke the responsible generator with the detail; loop.

## Step 5 — Re-audit

Invoke **qa-auditor** (drift mode) again. Repeat 2–4 until CLEAN (modulo spec-is-wrong items surfaced for user decision).

## Step 6 — Ship + report

Commit + push yourself (atomic `git commit … && git push`, staging only the changed files, per `support/rules/git.md`). Summarize: divergences by severity and surface, which were fixed in code (files + regression tests), which were surfaced as possible spec bugs awaiting decision, and the final audit status.
