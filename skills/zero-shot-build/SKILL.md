---
name: zero-shot-build
description: Turn a zero-shot idea into a perfectly-working, thoroughly-tested, spec-driven project — AI-natively designed on whatever stack the requirements pick. One deep intake (which also collects any API keys into .env), then the build runs one phase at a time — autonomous within a phase, with a human testing gate between phases. Also used to add a new capability to an existing project.
argument-hint: [your idea]
disable-model-invocation: true
---

# zero-shot-build — the build loop

**You are the ROOT SESSION.** You alone own the human channel (questions, testing gates,
blockers), git/PR policy, and the server lifecycle — on every platform. What differs per
platform is only *how the work is delegated*:

- **Claude Code** — you run intake and the human gates; each build phase is delegated to
  the **project-builder** orchestrator sub-agent (Task tool), which fans out
  spec-writer / code-generator / qa-auditor natively and returns a phase test-handoff.
  You verify every handback and you launch the server for the gate (a sub-agent's
  background processes die when it returns). Ask the user via your structured-question
  tool (multi-select) with plain text as fallback.
- **Hermes** — there is no orchestrator sub-agent (delegated workers cannot spawn their
  own workers, cannot talk to the user, and their background processes are killed on
  return). You orchestrate directly: delegate *leaf work* (spec-writing, one code slice,
  one audit) to the roles in `../../support/agents/` via `delegate_task` when available,
  **inline otherwise**. Ask via `clarify`, plain text as fallback. Platform sharp edges:
  `references/hermes-pitfalls.md`.

The idea is in `$ARGUMENTS`. **If `$ARGUMENTS` is empty, ask the user in plain text to
describe their idea and WAIT for their free-text reply.** Never use a question tool to
solicit or suggest the idea itself — the idea must come from the user as their own text.

**Shared material** resolves relative to this file: `../../support/…` (true for the repo
checkout, the Hermes tap, and the installed Claude plugin). If that path is absent (a
per-skill Hermes install), the README's install section says how to place the repo's
`support/` tree at `~/.hermes/support` so these references resolve.

**Permissions preflight (Claude Code):** before Stage 2, check the target project's
`.claude/settings.json` grants the harness's autonomy preset (broad Edit/Write/Read/Bash
allow — see the README's "Autonomy setup" section). If it doesn't, tell the user in one
line that the build will stall on permission prompts and point them at that section —
then continue; never silently stop.

Goal: **one prompt → a perfectly-working, thoroughly-tested product, one user-testable
phase at a time** — spec-first, AI-natively designed (`spec/agent.md` is always written),
on the stack the requirements pick. There is no default stack and no fixed boilerplate:
the spec designs the layout and the scaffold gate proves it runs before any feature work.

## The execution model (read this before anything else)

| Concern | Owner | Why |
|---|---|---|
| Talking to the user (questions, gates, blockers) | **Root session only** | workers cannot own the human channel |
| git / branch / PR / commit+push | **Root session** (Claude: via project-builder, which owns git for a build) | git must never be half-done |
| Server lifecycle (boot, smoke, keep serving) | **Root session only** | a worker's background processes die when it returns |
| Writing the spec | spec-writer role | single design authority, self-reviewed |
| Implementing one slice + its tests | code-generator role (one per slice) | parallel when delegation works, sequential inline otherwise |
| Independent review + running gates | qa-auditor role | read-only checker, never the author |

**Delegation policy — try, verify, fall back inline:**

1. **Try** the platform's delegation mechanism for each specialist role (Claude Code: the
   Task tool; Hermes: `delegate_task`, up to 3 children in parallel for independent
   slices).
2. **Verify every handback.** A worker's summary is advisory, not evidence. On return:
   check the durable files actually exist, re-run its gate command cheaply (a compile
   check / test collection, or the real gate if logic changed), and verify handback
   CONTENT — a worker can return "completed" whose body is a rate-limit error; that work
   is NOT done. A worker that returned at "95% done" is normal — **you finish the
   remainder inline**; never re-delegate the same 5%.
3. **Fall back inline.** If delegation is unavailable, errors out, or stalls: read the
   role file (`../../support/agents/<role>.md`) and execute it yourself as a checklist,
   in the same order the delegated version would run. The build NEVER stalls waiting for
   a worker that cannot spawn. Inline is a *normal* mode, not a failure.

**The inner loop (per slice — this is the engine):**

```
implement → run the REAL gate → READ the actual output → fix → re-run
```

**Provider stalls & `continue`:** at build start, tell the user in ONE line: "If I ever stop
with a provider/rate error, just type `continue` — progress is committed as I go, nothing is
lost." When resumed with `continue` after a stall: re-read `git status`, resume the current
step exactly where it stopped — no re-planning, no re-reading the spec, no apology.

Never claim, always observe: a gate "passes" only when you ran the exact command and read
its real output tail this session. Cheap re-verification (compile + collect-only) after
mechanical edits; the full real-key gate after logic changes and before any handoff.

## Stage 1 — Intake (the only interactive setup step)

Intake has **two fixed sections and a variable middle**:

1. **Product rounds (variable, minimum 5)** — all product questions, progressively deeper.
   Keep going until every dimension that would force a design decision in Phase 1 is
   resolved. Five rounds is the floor; complex ideas may need more. Each round covers a
   different dimension and never repeats covered ground.
2. **Technical round (fixed, always last)** — build-blockers only (LLM provider if the
   idea plausibly involves AI, stack preferences, access method).

All rounds use the platform's structured-question tool (multi-select). Resilience rules:

- **If the question tool fails DURING a round** (mid-round timeout, empty result,
  unavailable), fall back to plain text for the REMAINING rounds only — ask one question
  at a time, wait for the reply, then ask the next. **Never restart from Round 1.** Skip
  any round already successfully completed. This is a mid-stream fallback, not a full
  reset.
- **Once all product rounds AND the technical round are complete**, intake is done. Do NOT
  loop back to re-ask previous rounds. If you're uncertain about an answer from earlier,
  record it as `Assumed: …` in the brief and move forward. Intake happens exactly once.
- **Follow up on ambiguity.** If an answer could be read two ways, or a single pick may
  have dropped options that also apply, ask a short follow-up — never guess.
- **Empty answer = "you decide".** Pick the lowest-risk default, record it as
  `Assumed: …` in the brief, and move on. Don't re-ask, don't block.

**How to decide when to stop product rounds:** after each round ask: *"Is there any
dimension — interaction model, state/memory, features, constraints, edge cases,
observability, integrations — that, if left unresolved, would force spec-writer to guess?"*
If yes: another round on that dimension. If no: technical round. Err toward one more round
rather than an ambiguous brief.

**The golden rule: Phase 1 is the smallest user-testable quick win.** Richer intake sharpens
*which* slice to build first — it does not license a bigger Phase 1.

**The cardinal rule across ALL rounds: every question and every option must be specific to
THIS idea.** After Round 1 you know the idea category — use it. A user must instantly
recognise every option as being about their thing. Generic options are a failure.

### Round 1 — What is the idea? (4 questions, all multiSelect)

Acknowledge the idea in one sentence, then ask four themes — adapt wording and all options
to the idea:

- **What it works on** *(4 idea-specific options)* — the data, content, or domain it
  processes. Concrete: not "documents" but "CSV exports from our CRM".
- **What it produces** *(4 idea-specific options)* — concrete outputs: "an interactive chart
  I can explore", "a ranked list with reasons".
- **Usage pattern** — who uses it, how often, in what context.
- **Non-negotiables** — always offer at least: "My data can't leave my machine", "Keep costs
  very low", "Must connect to [something they mentioned]", "None — just build it well".

### Round 2 — How users interact (4 questions, all multiSelect)

Write ALL questions and options as a product designer who has used tools exactly like this:

- **Session model** — how long does one "conversation" or working session last?
- **Memory & state** — what carries across turns or sessions?
- **Multi-item handling** — one thing at a time or many?
- **When things go wrong** — clarify first, best-guess + flag, show the attempt, retry?

Skip any question Round 1 already answered.

### Round 3 — Feature depth (4 questions, all multiSelect)

What makes it genuinely powerful vs a toy — all options idea-specific concrete features:

- **Intelligence depth** — deterministic logic? one LLM call? multi-step? iterate-until-right? plan-first? (This seeds the AI-native lens — but the lens runs regardless of the answer.)
- **Output richness** — text, charts, tables, exportable files?
- **Proactive intelligence** — only answers? suggests follow-ups? flags anomalies?
- **Integration surface** — standalone, saves back, exports, embeds?

### Round 4 — Constraints & scale (3 questions, all multiSelect)

- **Data scale & performance** — how much data, how fast?
- **Privacy & data residency** — local-only, rows-never-leave, cloud-fine, compliance?
- **Reliability bar** — prototype, production, audit trail, access control?

### Round 5 — Observability, trust & transparency (3–4 questions, all multiSelect)

- **Reasoning visibility** — answer only, show the work, show every step, full chain?
- **Usage & cost awareness** — hidden, tokens, cost per query, running total?
- **Health & progress** — spinner, step counter, progress + timer, streaming?
- **Logging & audit** — nothing, per-query log, full DB history, full audit trail?

### Additional product rounds (as many as needed)

Common spill-over dimensions: edge cases & error handling; collaboration & sharing; output
lifecycle (ephemeral vs persistent); onboarding & defaults; any remaining trade-off that
would produce a meaningfully different Phase 1. Keep going until the brief would let
spec-writer fill every capability file without a single guess.

### Technical round — always last (3–4 questions)

- **LLM provider** *(single-select; ask whenever the idea could plausibly use AI)* —
  **Anthropic**, **Gemini**, **OpenRouter (any model)**, **Other / self-hosted**, or
  **"No AI in this product"**. Drives which key the user sets. (The scaffold's provider
  layer is built per the spec — any HTTP-API provider works.) Note: even on "No AI", the
  spec-writer still writes `spec/agent.md` — it may legitimately conclude "no AI
  capability needed", in writing.
- **Stack preference** — language, framework, database? **"No preference" → the
  spec-writer derives the best-fit stack from the requirements and records it with
  rationale in `spec/architecture.md` (`## Stack`), flagged `Assumed:`.** There is no
  default stack; a stated preference is BINDING.
- **How will they access it?** — Web UI, CLI, REST API, scheduled job.
- **One follow-up** only if something would force a mid-build pause.

**API key** (the only manual user step — skip if the product needs no external provider).
**`.env` is a secret-bearing file — never open it with a file-read tool on ANY platform.**
(Hermes hard-blocks the read outright; on Claude Code the autonomy preset denies it; and
reading it into context risks echoing a secret.) Instead run a short script via the
terminal tool that loads `.env` itself (`python-dotenv`, `source .env`, or the stack's
equivalent) and prints ONLY a pass/fail signal — presence as a boolean for the chosen
provider's var (e.g. `APPNAME_ANTHROPIC_API_KEY`; for **Other**, ask which env var + base
URL) — never the value itself. **Use an ABSOLUTE path to `.env`, never a relative one** —
sandboxed script runners resolve relative paths against the sandbox, not the repo, and
silently report MISSING even when the key is present (confirmed on a live run). Resolve
the repo root first (`git rev-parse --show-toplevel`), then load `<repo_root>/.env`.
Present → **validate it works** in that same script: one minimal real API call to the
chosen model, printing only `OK` or the error type (`401`/`429`/`model_not_found`) — a
key can be *present but dead* and a model slug can be stale; discovering either mid-build
wastes a phase. Missing, or the test call fails → tell the user the specific reason and
ask them to fix `.env` (from `.env.example`), then re-run the check. Never echo, print,
or commit a key value.

**Synthesis brief**: 2–3 paragraphs covering: what the product does and who uses it; the
interaction model (session shape, memory, multi-item); key capabilities (depth, outputs,
proactive behaviours, edge-case handling, integrations, observability); hard constraints
(scale, privacy, reliability); stack preferences + access model. Name the one core path
for Phase 1 explicitly. ("Just build it" → narrow MVP, lowest-risk defaults, documented
as assumptions.)

## Stage 2 — Design + scaffold (first phase only)

1. **DESIGN** — run the **spec-writer** role (Claude Code: via project-builder's first
   invocation; Hermes: delegate or inline) with the brief. It writes the full spec:
   capabilities, `spec/architecture.md` (`## Stack` with rationale + `## Layout` +
   `## Conventions`), **`spec/agent.md` — ALWAYS** (the AI-native design lens: patterns
   chosen from `../../support/patterns/agentic-ai.md`, or the written conclusion "no AI
   capability needed"), and the phased plan in `spec/roadmap.md` (per phase: Goal ·
   independent slices · key files · the exact runnable Gate command · how the user tests
   it). **Verify on handback**: no `<!-- FILL IN -->` left, every phase has a runnable
   gate, `spec/agent.md` exists and is complete (composition OR reasoned "no"). Surface
   its `Assumed:` flags to the user in your next message (don't wait on them).
2. **SCAFFOLD** — git per `../../support/rules/git.md`:
   - **Clean-baseline precheck (do this FIRST).** A fresh build must not inherit a prior
     build: if the current branch already carries a *different* project's filled `spec/`
     or app tree, STOP and confirm with the user before continuing. (A live run inherited
     an old ASP.NET+MSSQL spec this way and tried `dotnet`/Docker on a Python box.)
     An existing spec is fine when the user asked to ADD a capability to this project.
   - `base=$(git rev-parse --abbrev-ref HEAD)` — capture `<base>` BEFORE branching; never
     `git checkout main` first.
   - `name="feature/<slug>-$(date +%Y%m%d-%H%M)-v0.1"` — the date-time slug makes it
     unique. Before creating it, `git ls-remote --heads origin "$name"`; if it somehow
     exists, bump the timestamp. **Never `git checkout` an existing feature branch to
     build into** — that imports the prior build's stack. Then `git checkout -b "$name"`.
   - **Build the scaffold** — the minimal runnable skeleton the spec's `## Layout`
     defines (code-generator role, scaffold slice), then run the **scaffold gate**
     (`../../support/patterns/phases.md`): deps install, app boots via its documented run
     command, smoke test green, migration tool wired if there's a DB, key validated.
     Write `.env.example` documenting every env var.
   - First commit + push, then open the PR immediately: `gh pr create --base "$base"` —
     **never straight onto the default branch**; the user merges PRs, the build never does.

## Stage 3 — Build one phase (the loop)

For the current phase (Phase 1 first; later phases on user approval):

**Claude Code:** invoke **project-builder** (Task tool) — first invocation carries the
brief; each later one carries "build Phase N" + the user's feedback from the prior gate.
It fans out generators per slice in parallel, gates each with qa-auditor, commits and
pushes the phase, and returns the PHASE TEST-HANDOFF. **Verify the handback**: commits
exist and are pushed, the gate output it reports is real (spot-run it cheaply), the
handoff names a run command and URL. Then go to Stage 4 — you own the server, not it.

**Hermes (or inline fallback anywhere):** run the engine yourself:

1. **Read the phase's slices** from `spec/roadmap.md`.
2. **Implement each slice** via the **code-generator** role — delegate independent slices
   in parallel (up to 3) when delegation works AND the LLM key is a paid/dedicated one;
   otherwise inline, sequentially, one slice at a time. **On a shared/free key, prefer
   sequential inline** — parallel fan-out multiplies 429s on one credential pool and
   stalls the build (mining prior runs showed ~14h cumulative blocked on pool
   exhaustion). Verify each handback's CONTENT, not just its status. Each slice = its
   surfaces + its tests, test-first. Tell each generator exactly which files it owns;
   slices own disjoint paths.
3. **Gate each slice as it lands** via the **qa-auditor** role: independent code review +
   run the slice's real gate (real LLM/API keys from `.env`, production DB engine) + read
   the actual output. BLOCKED → route the named finding back to the generator role for
   that surface; loop until VERIFIED. Never start the next phase with a BLOCKED slice.
4. **Phase-level checks (once per phase, after slices aggregate):**
   - **Boot gate**: start the app with the EXACT documented run command from the repo
     root, pinned interpreter/runtime (never a bare global — a shared environment can
     shadow it). No import/startup traceback. A green test run does NOT prove this — test
     runners mask boot-only import bugs.
   - **Fresh-DB check**: if the schema changed this phase, run the migration and its
     verify command (a revision must print) against the same DB the server uses — or,
     pre-migrations, recreate the dev database. A stale dev DB turns a green suite into a
     500 on the live server.
   - **Live smoke**: health + the phase's new endpoint(s) + the UI page served — real
     responses read, not assumed.
5. **Commit + push the phase** — stage the phase's files explicitly (never `git add -A`),
   `git commit -m "phase-N: <desc>" && git push origin <branch>` as ONE atomic action.
   Update the PR body (what this phase added, how to run, what's deferred). **Hard gate: a
   phase isn't done until committed + pushed + PR current — do this BEFORE the handoff.**

## Stage 4 — Human testing gate (you own the run)

**The user's ONLY jobs are: (a) put secrets in `.env`, (b) click around the running app.
They never run a terminal command to test.** You own the server and the gate:

1. **Launch the server yourself**: from the repo root, the documented run command with the
   pinned interpreter/runtime, using the terminal tool's **background mechanism** (Claude
   Code: `run_in_background`; Hermes: `background=true`) on a **free port** (retry the
   next port if busy; export the port env var). **Never a `&`-backgrounded command,
   `nohup`, `setsid`, or `disown`** — platforms hard-block or orphan those. Then, in a
   FOLLOW-UP terminal call, health-check with retry:
   `for i in {1..10}; do curl -sf localhost:$PORT/health && break || sleep 2; done`
   (each terminal call starts fresh at the repo root — use absolute paths, don't rely on
   a prior `cd`). This curl/httpx smoke asserting response CONTENT is the gate of record;
   a browser check is a bonus only when a browser tool is actually available. If it never
   responds → BLOCKER: route to qa-auditor, fix, relaunch. **Never present a URL you
   haven't verified live this session; never hand the user a command to run the server.**
   (Access model drives the gate: for a CLI project, run the primary commands yourself,
   show real output, and hand the user the exact invocations as release notes; for a
   scheduled job, trigger one run yourself and show the produced artifact.)
2. **Present phase release notes**: the ONE live URL; what was built this phase; what to
   click/type; the expected result; which parts are clearly-labelled stubs vs real (a stub
   must never read as a bug); what the next phase adds. No terminal commands in the handoff.
3. **Ask via the structured-question tool — ALWAYS MULTI-SELECT, never a single verdict.**
   One option per testable feature this phase shipped, plus "App didn't load / error" and
   "Nothing worked" escapes. A multi-select tells you *which* parts passed in one answer.
   If the tool won't load: plain text, one question at a time.
4. **Route on the answer:**
   - Didn't load → qa-auditor (boot failure) → fix → relaunch → re-present.
   - Any negative → capture what they saw → run the **zero-shot-fix** procedure (you stay
     the root; qa-auditor diagnoses + classifies SPEC-vs-CODE, the generator fixes,
     scoped re-gate) → rebuild/restart → re-present. Loop until satisfied.
   - All positive → *"Ready for Phase N+1?"* — on "one more thing first", route as
     negative; on yes → Stage 3 for the next phase.

## The build journal (capture learnings as you go)

Maintain **`NOTES.md` on the build's feature branch** throughout the run — commit it with
each phase. It is a *harness-improvement log*, not an app changelog: record only friction
with the harness or the runtime, each entry with symptom → what you did → the durable
lesson. Typical entries: a question-tool failure, a delegated worker that returned early,
a gate that passed for the wrong reason, a rule that fought you, a question the intake
should have asked. Timestamp the run start (date + time) in the first entry so platform
logs can be sliced to this run afterwards (Hermes: `~/.hermes/logs/agent.log`,
`~/.hermes/sessions/request_dump_*`).

After the run, durable generic lessons get distilled into the harness (platform pitfalls
into `references/`, behaviour changes into the role files) via a separate harness PR; the
war-story details stay behind on the build branch's NOTES.md.

## Stage 5 — Ship + report

1. **qa-auditor** — final whole-tree drift audit (CLEAN). Route divergences as in Stage 4.
2. Ensure everything is pushed and the PR body is current. Never merge the PR yourself.
3. Summarize: what was built, the **live URL it's serving at** (keep it running), what's
   deferred, the PR link. Run commands live in the README for the record — not as
   something the user must execute.

## Adding a capability to an existing project

Spec already filled in → skip scope intake; confirm `.env` covers any new provider/key.
spec-writer adds the capability + an incremental phase to `spec/roadmap.md`
(self-reviewed; re-runs the AI-native lens if the capability could be AI-powered) →
Stage 3 loop for that phase → Stage 4 gate. Same rules, one phase.

## Failure modes (each of these happened on a real run)

- Waiting for a delegated worker that can never spawn (depth cap) instead of going inline.
- Trusting a worker's "done" without checking the files / re-running the gate — workers
  return early at ~95% routinely; the root finishes.
- A worker (or you) launching the test server inside a delegate — it dies on return; only
  the root serves.
- Presenting the gate without a live, verified URL — bouncing an un-run app back to the
  user as a question. The gate owns the run.
- A bare global interpreter/runtime picking up the wrong environment → phantom
  module-not-found errors. Always the pinned, project-local one.
- A stale dev DB (schema drifted since auto-create) turning green tests into live 500s —
  migrate or recreate before the boot gate.
- Looping an LLM call per output line/token in generated code — one batched call per
  artifact, split downstream (a per-line loop burned a real monthly spend cap).
- Single-choice gate questions (throws away per-feature signal); dumping all intake
  questions in one message when the question tool is down.
- Committing to the default branch, a commit without a push, a push without a PR,
  `git add -A`, or staging `.env`.
