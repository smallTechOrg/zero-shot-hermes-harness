# AI Agent Rules

**These rules apply to every session driving a zero-shot build, fix, or sync — on any
platform (Claude Code, Hermes, or any Agent-Skills-compatible tool).**

Read this file completely before doing anything else.

**The execution model (governs every build):** the ROOT SESSION owns the human channel
(questions + testing gates), git/PR, and the server lifecycle. The specialist roles in
`../agents/` (spec-writer, code-generator, qa-auditor) run via the platform's
delegation mechanism when available and **inline otherwise** — the root reads the role
file as a checklist. Delegated workers cannot ask the user, may return early (the root
verifies every handback and finishes remainders), and their background processes die on
return — only the root serves.

- **Claude Code:** roles are native sub-agents (spawned via the Task tool); a build is
  additionally coordinated by the **project-builder** orchestrator sub-agent, one phase
  per invocation. The root session still owns the human gates and the live server.
- **Hermes:** roles run via `delegate_task` (leaf work only — workers cannot spawn
  workers) or inline. There is no orchestrator sub-agent; the root orchestrates.

---

## ⚠ Non-Negotiable Rules

These rules are never optional, never skipped, and must survive context compression. If your context window is compressed and you can only remember a few rules, these are the ones.

1. **README must always be accurate.** Every command in the README must work exactly as written, from the directory stated. Before ending any session or marking any phase complete: run the README commands yourself — if any fail, fix the README first. A README that lies is worse than no README.

2. **Never claim a test passed if you didn't run it.** "It should work" is not a passing test. Run the suite (pytest, vitest, `go test`, …). Show the output. If you can't run it, say so — do not fabricate results.

3. **All commands in docs use the stack's runner prefix.** Every migration/test/run command in the README and docs must carry the prefix that makes it work without manual environment activation (e.g. `uv run` for Python+uv, `npx` for Node, `bun` for Bun). Bare commands fail unless the user activated an environment — which they won't.

4. **Working directory must be explicit.** Any README or doc section with shell commands must state the exact working directory at the top of the code block. "Run from project root" is not enough — give the exact relative path from the repo root.

5. **Tests run on the production database engine.** If production is PostgreSQL, tests run against PostgreSQL — a suite that only passes on a lighter stand-in does not count as passing.

6. **Golden-path UI smoke test is mandatory before Phase 2 passes.** If the project has any UI or HTTP surface, Phase 2 must include an automated test that walks the full primary user journey end-to-end against the **real external services the spec names** (the real LLM/API when the design has AI capability — keys from `.env`) and asserts **response content**, not just status codes. If the journey is JS-driven in the browser (including a zero-build static app whose primary flow runs through its JS), the smoke is a headless-browser run; HTTP-client assertions alone gate only server-rendered/static pages with no JS on the tested path. A build that returns 200 but renders a broken-looking page is a failing build. Edge-case and end-to-end coverage of the journey are required, not optional.

7. **Tests and evals run against the real external services the spec names, using keys loaded from `.env`** — the real LLM/API whenever `spec/agent.md` gives the project AI capability, the production database engine always. There is no offline-passing requirement; real-key execution is the default and required path for every gate. (A project whose `spec/agent.md` concluded "no AI capability needed" has no LLM gate — a missing LLM key is then not a blocker.) A stub provider MAY exist as an optional local fallback when a key is genuinely absent, but it is never the gate. The quality bar is perfect, zero errors — edge-case, end-to-end, and UI tests are required, not optional. The gate must exercise the **hard, idiomatic inputs the capability promises** and push the **real service's hard outputs through every guard** on the user's path — not just one easy happy-path example (see `../patterns/test-driven.md` → "Gate Tests Must Cover the Capability's Hard Cases").

8. **Every commit must be pushed immediately.** `git commit -m "..." && git push origin <branch>` is one indivisible action — a commit that isn't pushed doesn't exist. See `git.md`.

9. **Builds never land on the default branch directly.** Everything a `/zero-shot-build` run produces lives on a feature branch cut from the current HEAD and is PR'd back to *the branch it was cut from* (`--base $base`) — never committed straight to `main`/`master`. The user merges PRs; the build never merges its own. See `git.md`.

10. **A PR must exist before the first feature-branch commit.** Open it right after the first push, **based on the branch you cut from** (`gh pr create --base "$base" --head feature/<slug>-<YYYYMMDD-HHMM>-v0.1`, where `$base` is the HEAD captured before `checkout -b`); every later push updates it. See `git.md`.

---

### Optional stub fallback (non-normative)

The real provider is the default and what every gate tests. A stub provider MAY exist purely as a local fallback for when a key is genuinely absent:

- It should auto-select real when a key is present (`provider=auto` → real when key set), never requiring the user to flip a flag *in addition* to setting the key.
- If an active stub is ever used, signal it visibly in the UI so demo output is never mistaken for real output.
- If implemented, its per-node outputs should be distinct (branch on injected node tags, never on prose keywords) and shaped like real output, so the fallback is not misleading.

None of this is gated — the Phase 2 gate runs against real keys.

---

## 1. Session Start Checklist

Complete all steps in order before writing any code:

- [ ] Read `spec/roadmap.md` — know what you're building
- [ ] Check if the spec is complete (no `<!-- FILL IN -->` markers in product spec files)
  - If there is no `spec/` yet, or it is incomplete: tell the user to run `/zero-shot-build`; do not write application code
- [ ] If spec is complete: read the full spec manifest (roadmap, architecture, capabilities, data, api, ui, agent) plus these rules and the patterns
- [ ] Run `git status` — working tree must be clean before starting
- [ ] **Branch from the current HEAD**: `base=$(git rev-parse --abbrev-ref HEAD)` then `git checkout -b feature/<slug>-$(date +%Y%m%d-%H%M)-v0.1` (the date-time slug keeps the branch name unique) — never `git checkout main` first (see `git.md`)
- [ ] **Extend the scaffold in place** per `spec/architecture.md` (`## Layout`) and `../patterns/project-layout.md` — never write app code at the repo root, never create a second package beside the source root
- [ ] Confirm `.env` exists and contains the keys the spec requires, if any (requested at intake) — tests and the build run against the real external services using these keys
- [ ] Confirm which phase you are implementing (see `../patterns/phases.md`)

## 2. Build Flow

The goal is: **one prompt → a perfectly-working, thoroughly-tested product, delivered one user-testable phase at a time.** Intake is the only interactive setup step. After it, the build is autonomous *within* a phase, with a **human testing gate between phases** — the user tests each phase before the next one starts.

```
INTAKE (capture scope, constraints, stack preferences; ask additional clarifying
        questions up front if anything is ambiguous; request the user fill .env
        with the required API keys/secrets)
        ↓
DESIGN + SCAFFOLD (full spec incl. spec/agent.md — the AI-native lens — then the
       minimal runnable skeleton on the chosen stack, proven by the scaffold gate)
        ↓
BUILD PHASE N (implement the phase; gated by passing real-key tests) → publish the
       phase test-handoff
        ↓
HUMAN TESTING GATE (the user tests the phase; on Yes → next phase, on issue →
       qa-auditor diagnoses → the right generator fixes → re-gate → re-present)
        ↓
BUILD PHASE N+1 … (repeat at every phase boundary)
```

**TIGHT SCOPE FOR QUICK WINS / FIRST-TIME-RIGHT:** Phase 1 is the *smallest* user-testable win and must work the first time the user tests it — zero rough edges on the tested path. The frontend builds in parallel and may include clearly-labelled non-functional stubs so the user sees the vision; a stub must never be mistaken for a bug. The user must never have to debug what we hand them.

**Rules that never change:**
- User stack preferences captured at intake are **BINDING**. Where intake is silent ("no preference" / "you decide"), the spec-writer derives the best-fit stack from the requirements and records it with rationale as `> **Assumed:** …` in `spec/architecture.md` — there is no default stack, and the choice is never re-litigated mid-build.
- `spec/agent.md` is written for **every** project — the AI-native design lens; "no AI capability needed" is a legitimate written conclusion, a missing file is not.
- Filling `.env` is the only manual user step, requested at intake.
- Each build phase must pass its gate against the real LLM/API before the next phase starts.
- The human tests each phase before the next one starts — that is the gate between phases.
- spec-writer self-reviews its spec (architecture + agent design + roadmap), generators build independent slices in parallel, and qa-auditor independently gates each phase.

```
[Phase implemented] → [real-key gate passes] → [committed] → [human tests] → [next phase]
```

---

## 3. Spec-First Rule

**No code change without a spec backing it.**

If you are asked to implement something not in the spec:
1. Stop
2. Tell the user what spec gap you found
3. Propose adding it to the spec first
4. Wait for approval before writing code

See `../patterns/spec-driven.md` for full details.

## 4. Phase Discipline

**Never start phase N+1 while phase N is incomplete or failing.**

Each phase ends when:
- All code for that phase is written and committed
- All tests for that phase pass
- The qa-auditor role has returned VERIFIED (or you have run the gate checklist manually)
- **README is updated** to reflect what this phase added — any new setup steps, commands, endpoints, or environment variables must be accurate and runnable before the gate is declared passed (Rule 1 applies at every phase boundary, not just at session close)

See `../patterns/phases.md` for the phase definitions and gates.

## 5. Git Discipline

See `git.md` for the full rules. Summary:

- Commit every logical unit of work — never let the working tree stay dirty for more than one logical change
- **Push immediately after every commit** — `git commit -m "..." && git push origin <branch>` is one indivisible action
- Commit message format: `phase-N: [what you did]`
- Never commit secrets; never force-push without user confirmation
- **Never `git add -A` / `git add .`** — stage specific files only

**Before every reply to the user:**
1. Run `git status`
2. If dirty: commit and push
3. Confirm the working tree is clean **and** the branch is pushed before replying

## 6. Test Before Claiming Done

A phase is not done until all tests pass against the real LLM/API. "It looks right" is not a test. The quality bar is perfect, zero errors — not fast and minimal.

- Write tests for each capability as you implement it, including edge cases
- Cover end-to-end and UI journeys (real keys) for any UI/HTTP surface
- Run the full suite against keys from `.env` before marking a phase complete
- If tests fail, fix them before moving on

## 7. Error Resilience

Every external call (API, database, LLM) must have:
- Error handling that doesn't crash the app
- Logged failures (to file or stdout at minimum)
- Graceful degradation (the system continues if a non-critical step fails)

Surface a clear, actionable error when an API key is missing or invalid (point the user at `.env`) — never silently fall back in a way that hides a real failure during tests.

## 8. No Gold-Plating

Build what the spec says, nothing more.

- No extra features "while you're in there"
- No refactoring outside the current phase scope
- No premature abstractions
- If you spot a future improvement, note it and keep moving

## 9. When Stuck

If requirements are unclear:
1. Stop
2. State your specific questions to the user
3. Ask the user — do not guess

If the spec is ambiguous:
1. State the ambiguity
2. Propose an interpretation
3. Wait for confirmation before implementing

## 10. Closing a Session

Before ending a session:
- [ ] Working tree is clean (all changes committed and pushed)
- [ ] Tests pass
- [ ] `README.md` updated if project layout, setup steps, or commands changed
