# Tech-Stack Rules

Generic engineering rules that hold for **every** project, whatever stack is chosen.
**There is no default stack.** The spec-writer derives the best-fit stack — language,
framework, LLM provider/model, database, libraries — from the idea, the intake answers,
and the constraints, and records it (with rationale) in `spec/architecture.md` under
`## Stack`. User stack preferences captured at intake are BINDING; everything else is the
spec-writer's call, documented as `> **Assumed:** …`.

This file is the permanent doctrine those choices must honor — it is not edited per
project. Each rule below is a stack-agnostic principle; the indented case under it is the
field incident that taught us the rule, kept as an illustration, not as a requirement to
use that stack.

---

## Avoid Default Dev Ports

Whatever the stack, the development server **must not squat on the framework's default
port**. Pick the next port up (or any uncommon one), hard-code it as the app's default,
make it overridable via an env var (e.g. `PORT`), and reference the exact resulting URL
in the README.

Reason: default ports (8000, 3000, 5000…) are routinely occupied by other local services,
so first boot fails with no code bug present.

> *Field case:* Python web apps on port 8000 collided with other FastAPI/Django/`http.server`
> instances constantly; moving the default to 8001 eliminated the failure class with zero
> code change.

## Frontend — Simplest Thing That Satisfies the Spec

The default frontend for any project that needs a UI is **zero-build static assets served
by the backend on a single origin** — no package install, no bundler, no runtime-version
hazard. The styled-render gate then reduces to "the served page contains the real UI and
its linked CSS/JS return 200 non-empty".

- **Single-origin is the canonical run + test path.** One server, one documented URL
  (exact port and path, trailing slash included). The gate and the user test this exact
  path.
- **Adopt a build-pipeline framework ONLY when the spec genuinely needs it** — complex
  client state, routing, component reuse at scale. A framework adds a build step the
  gates must then cover, and every one of these was a real first-build failure in the
  field:
  - the production build must run and its **built assets must be what the backend
    serves** (single-origin — never a two-server dev flow as the test path);
  - the built CSS must contain real selectors — an unstyled 200 fails the gate;
  - pin a supported LTS of the frontend runtime (version file / `engines` field) —
    bleeding-edge runtimes have shipped SSR-breaking globals;
  - commit the lockfile.
- **E2E for any UI surface:** a live-server smoke that walks the primary journey and
  asserts real output content appears. If the journey is JS-driven in the browser —
  including a zero-build static app whose flow runs through its own JS — the smoke is a
  headless-browser run (e.g. one Playwright script; no build pipeline needed). Pure
  server-rendered/static HTML with no JS on the tested path may be gated with
  HTTP-client content assertions.

## LLM Model Name Rule

**Always use a current, verified model name — never a deprecated or guessed one.**

- Model names change. Before hardcoding any model identifier, verify it exists by calling
  the provider's list-models API or checking current documentation.
- The model name must be configurable via an env var (e.g. `APPNAME_LLM_MODEL`) so it can
  be changed without a code deployment.
- A 404 NOT_FOUND from the LLM API almost always means the model name is wrong — check
  the name first before debugging anything else.
- At intake/scaffold time, validate the chosen model answers a minimal real call — a slug
  can be present in docs yet dead for this account (see the key-validation rule below).

Examples of verified-current defaults **as of 2026** (illustrative — re-verify before
pinning; the spec records the project's actual choice):

| Provider | Example model | Notes |
|----------|---------------|-------|
| Anthropic | `claude-sonnet-4-6` | verify against current docs before pinning |
| OpenRouter | `anthropic/claude-sonnet-4-6` | provider-prefixed; routes to the underlying model |
| Google Gemini | `gemini-3.1-pro` | fast/cheap alternatives exist for latency-sensitive nodes |
| OpenAI | `gpt-4o-mini` | |

## Deploy-Time Dependencies Are Main Dependencies

Anything the project needs at **deploy or setup time** — the database driver, the
migration tool, anything a production bootstrap runs — **must be declared in the main
dependency block**, never in a dev-only group.

Reason: migrations and setup scripts run in environments that install only production
dependencies; a dev-only driver makes deploy-time commands fail even though tests pass.

> *Field case:* `psycopg2-binary` declared under a dev-only group let the test suite pass
> while `alembic upgrade head` failed on any machine that hadn't installed dev deps.

## Tests Run on the Production Engine

**Tests must use the same database engine (and driver) as production.** A lighter
stand-in that "should behave the same" is not a passing gate — dialect differences,
migration behavior, and driver quirks only surface on the real engine.

- The test database must be set up automatically — the test harness creates and tears
  down the schema; no manual steps.
- The test DB URL is provided via env var (e.g. `TEST_DATABASE_URL`, or the main
  `DATABASE_URL` pointing at a dedicated `_test` database). The README documents this.
- Use a dedicated test database — never the development or production one.

> *Field case:* suites green on SQLite shipped migrations that failed on PostgreSQL; the
> rule is now: prod PostgreSQL ⇒ tests on PostgreSQL, created/dropped by the test
> fixture, no exceptions.

## LLM / API Test Rule

**Tests and evals run against the real LLM/API using keys loaded from `.env`.** There is
no offline-passing requirement; real-key execution is the default and required path for
every gate, on the production database engine. A stub provider MAY exist as an optional
local fallback when a key is genuinely absent, but it is never the gate. The quality bar
is perfect, zero errors — edge-case, end-to-end, and UI tests are required, not optional.

- The build and tests load keys programmatically from `.env` (gitignored); confirm a key
  by presence (bool) only — never echo, print, paste, or commit a secret value.
- **Validate the key AND the model with one minimal real call before building** — a key
  can be present but dead (revoked account, expired trial), and a model slug can be
  stale; discovering either mid-build wastes a phase.
- A stub is permitted only for an integration whose external system isn't built yet —
  never as a substitute for the real provider on a path that exists.
- **CI contract:** a runner without secrets cannot pass the real-key gate. Either inject
  the keys from a secret store, or guard the real-key tests with a skip when keys are
  unset. Skipped is not passed: the gate is BLOCKED if a required key is missing locally.

## Toolchain Discipline

- **Every documented command uses the stack's runner prefix** so it works without manual
  environment activation (e.g. `uv run pytest` for Python+uv, `npx vitest run` for Node,
  `bun test` for Bun). A bare command that requires an activated venv/PATH the user never
  set up is a broken README line.
- **Pin the interpreter/runtime in run commands** — invoke the project's own toolchain
  explicitly (e.g. `.venv/bin/python -m <pkg>`, the version manager's shim), never a bare
  global that can resolve to the wrong installation.
- **Assume only the spec's toolchain exists on the machine.** Never invoke a tool the
  spec's stack didn't install.
