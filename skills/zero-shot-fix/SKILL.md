---
name: zero-shot-fix
description: Diagnose and fix a bug, runtime error, failing test, or spec/code drift in an existing project, then verify the fix.
argument-hint: [bug description / error / "tests" / "drift"]
disable-model-invocation: true
---

You are the ROOT SESSION orchestrating a targeted fix by running the specialist roles in `support/agents/` — delegated via your platform's mechanism (Claude Code: the Task tool / native sub-agents; Hermes: `delegate_task`) when available, **inline otherwise** (read the role file as a checklist; the fix never stalls waiting for a worker that can't spawn). Verify every handback: files exist, the gate was really run. The target is in `$ARGUMENTS`. **If `$ARGUMENTS` is empty, ask the user in plain text to describe what's broken — the bug, error, failing test, or drift — and WAIT for their free-text reply before doing anything else.** Do NOT use a question tool to solicit, suggest, or pick the problem — the problem statement must come from the user as their own text. Only once you have it do you proceed to Step 1. Run autonomously: diagnose+classify → fix → verify, looping until the failure signal is gone. Pause only on a hard blocker or explicit request.

> **Shared material** is referenced as `support/…` — the harness's shared tree, two levels
> up from this file (`skills/<name>/SKILL.md` -> `support/`) in the repo checkout, the
> Hermes tap, and the installed Claude plugin. For a per-skill Hermes install, the README
> says how to place it at `~/.hermes/support`.

**qa-auditor runs FIRST** — it diagnoses, captures the failing signal, and CLASSIFIES the root cause (SPEC vs CODE, and which surface). Its verdict ROUTES the fix and names the surface. Fixing happens in the **code-generator** role (one invocation per named surface, per the project's declared layout in `spec/architecture.md` — e.g. backend source and/or frontend); judging happens in read-only **qa-auditor**; you (the root session) own the commit + push.

## Step 1 — Diagnose + classify (qa-auditor first)

**Skip if already diagnosed:** if the caller has passed a qa-auditor verdict with exact `file:line` and SPEC/CODE classification, use that as the baseline and go straight to Step 2 — do not re-invoke qa-auditor.

Otherwise, invoke **qa-auditor** with the target. It:
- captures the current red state — the failing test output, the reproduced error, or the specific drift divergence + file — as your before/after baseline;
- CLASSIFIES the root cause as **SPEC** (spec wrong/missing) vs **CODE** (code diverges from spec), and names **which surface** (per the spec's layout) and file(s);
- returns a routed verdict. It stays read-only and never spawns agents.

State the classification in one line. If qa-auditor can't reproduce the reported problem, say so and ask for repro steps rather than guessing.

Done-when, by signal:

| Signal in `$ARGUMENTS` | Done when |
|---|---|
| **Failing tests** | the gate test is green |
| **Bug description** | the wrong behavior no longer occurs and a regression test covers it |
| **Runtime error / stack trace** | the error no longer reproduces when the app runs |
| **Spec/code drift** | qa-auditor (drift mode) reports CLEAN (see also `/zero-shot-sync`) |

## Step 2 — Fix (routed by the verdict)

- **SPEC root cause** → invoke **spec-writer** to rewrite the spec section, then invoke the responsible generator(s) to redo the code toward the corrected spec.
- **CODE root cause** → run the **code-generator** role per named surface — one invocation per surface the spec's layout declares (e.g. one for the backend source tree, one for the frontend/UI surface). They can run concurrently (delegated) or sequentially (inline) if the fix spans surfaces — disjoint paths either way.

Give the generator the precise target, the responsible files, and the spec sections defining correct behavior. It fixes toward spec intent and adds/updates a regression test (for a bug in an external-service integration — LLM, API, store — the regression test runs against the real service with keys from `.env`). It must not mute a test or delete an assertion to go green; if spec and test genuinely conflict, it stops and reports (likely a spec bug → re-run Step 1 as SPEC, or suggest `/zero-shot-sync`).

## Step 3 — Verify (qa-auditor always; scope tiered by fix size)

**qa-auditor verifies every fix** — independence is the point: the agent that judges the fix is never the one that wrote it. What changes by tier is the **scope of what qa-auditor runs**, not whether it runs.

### Scoped gate (express) — use when ALL hold
- Root cause is **CODE**, not SPEC
- `git diff --name-only HEAD` shows **≤ 3 files changed**
- No schema/migration change (the project's migrations directory — as named in `spec/architecture.md` — is untouched)
- No API contract changed (`spec/api.md` untouched)

Invoke **qa-auditor in scoped gate mode**: verify only the changed surface — run the targeted tests covering the changed files + the new regression test + one real-service smoke call on the exact behavior that was broken (and re-verify the UI surface per the project's declared build pipeline if a frontend file changed — no build step for a zero-build static frontend; run the build when one exists). It does NOT run the full suite or full E2E. It still reviews the diff with fresh eyes and returns VERIFIED/BLOCKED. Typical cost: ~1–2 min vs. the full gate's 10+.

### Full gate — use when: SPEC root cause / migration added / API contract changed / > 3 files changed / scoped gate came back BLOCKED

Invoke **qa-auditor** in full gate mode (real keys from `.env`, full suite + E2E) against the Step 1 signal. Still BLOCKED → re-route per the verdict (re-invoke the responsible generator with the new detail); loop until VERIFIED. For a drift fix, also confirm qa-auditor (drift mode) reports CLEAN.

## Step 4 — Ship + report

Commit + push the fix yourself (atomic `git commit … && git push`, staging only the changed files, per `support/rules/git.md`). Summarize: classification (SPEC/CODE + surface), root cause (1–2 sentences), files changed, the regression test added, the verified before→after, and the pushed SHA.
