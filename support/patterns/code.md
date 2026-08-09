# Code Style

> Generic code conventions that apply to **every** project — harness doctrine the
> spec-writer and code-generators follow, not a per-project file. The project's chosen
> language/stack lives in `spec/architecture.md` (`## Stack`), and its language-specific
> conventions live there too (`## Conventions`) — this file is never edited per project.

---

## Universal Rules

These apply regardless of language or framework:

1. **Types at boundaries** — every function that crosses a module boundary must use typed inputs and outputs (Pydantic, TypeScript interfaces, Go structs, etc.) — never raw dicts or `any`
2. **One responsibility per file** — a file does one thing; if it's doing two things, split it
3. **No comments explaining WHAT** — code should be self-documenting via names; only comment WHY something non-obvious is done
4. **No dead code** — remove unused imports, functions, and variables immediately; don't comment them out
5. **Fail loudly at startup** — validate all required config/env vars at startup; don't fail silently at runtime
6. **No hardcoding** — values that could change (URLs, limits, credentials) go in config or environment variables

## Per-Project Conventions Live in the Spec

Naming conventions, file organization, error-handling shape, logging fields, and testing
conventions are **language- and stack-specific**, so the spec-writer records them in
`spec/architecture.md` under `## Conventions` when it chooses the stack. Generators follow
that section exactly; if it is silent on a question, the universal rules above and the
stack's idiomatic community convention apply, in that order.

---

## Test Environment Rules

These apply to all projects. No exceptions.

1. **Same DB engine as production** — if the app uses PostgreSQL, tests use PostgreSQL. A lighter stand-in is not a substitute: a suite that only passes on it tells you nothing about whether migrations and queries work against the real database.

2. **Automated setup — no manual steps** — the test setup (e.g. `conftest.py` for pytest, a setup file for vitest/bun) must create all required tables and tear them down automatically. The test runner must work with a single command after setting the test DB URL.

3. **Isolated test database** — use a dedicated database (e.g. `myapp_test`, not `myapp`). Never run tests against the development or production database.

4. **Test DB URL via environment** — expose the test database URL through the same env var mechanism as the app (e.g. `DATABASE_URL` pointing at the test DB, or a `TEST_DATABASE_URL` the test setup reads). Document this in the README.

5. **DB URL and API keys in `.env.example`** — the `.env.example` file must include the test DB URL and every required LLM/API key with clear placeholders (e.g. `APPNAME_ANTHROPIC_API_KEY=`) so the user knows what to fill in. Filling `.env` with real keys is the only manual user step, requested at intake; tests and evals load these keys programmatically and confirm them by presence only.

6. **Migrations are an explicit documented step** — the README must include the migration command (and its verify command) as an explicit step before running the app or tests. Never rely on auto-create from ORM metadata alone in production.

---

## LLM Provider Selection and Stubs

**Tests and evals run against the real provider using keys loaded from `.env`** (edge-case, end-to-end, and UI tests are required, not optional). The real provider is the default and required path; a stub is an optional local fallback only.

Any project with an LLM dependency must follow these patterns:

1. **`provider=auto` by default → real when the key is set.** Resolve to the real provider when the API key env var is present in `.env`; the user never flips a flag in addition to setting the key. Encapsulate this in one resolved-provider property on the settings object. Only when a key is genuinely absent may it fall back to an optional stub.

2. **Tolerate dirty `.env` values.** Config resolution must strip inline `#` comments and surrounding whitespace before comparing enum-like env values (`provider`, `mode`, etc.). A `.env` written months ago with `APPNAME_LLM_PROVIDER=anthropic   # anthropic | openai` must not silently pin the wrong provider. Most settings libraries do NOT strip inline comments — do it yourself in a resolved property, never trust the raw field.

**If you keep the optional stub fallback**, it should be credible and self-evident:

- Outputs branch on explicit node tags, not prose keywords. Each node injects a unique tag (`<node:plan>`, `<node:draft>`, ...) and the stub matches those tags, so a draft prompt containing "expand this outline" never triggers the stub's "outline" branch.
- "Draft"-class outputs are shaped like the real thing (paragraphs/headings, not a bare bullet list).
- If the stub is active in dev, label it visibly so its output is never mistaken for real. This is a should-when-used, not a gate: the gate runs against real keys.

---

## Integration Test Patterns

Integration and e2e tests call the **real** LLM provider with keys loaded from `.env` — the call is NOT stubbed. The suite is overly tested: edge cases, error paths, end-to-end journeys, and (for any UI/HTTP surface) UI states are all required. Because real responses are non-deterministic, integration/e2e assertions check stable structural properties (status, shape, key fields) rather than exact prose; unit tests stay fully deterministic (inject the clock, seed randomness). Run against the production DB engine — never a stand-in.

---

## Field-Tested Gotchas (per-stack reference — apply when the spec chooses that stack)

Real first-build failures, kept so no project relearns them. Each is binding **for
projects on that stack**; for other stacks, take the underlying principle.

### Python — Starlette ≥ 1.0 `TemplateResponse` signature

Starlette 1.0 and FastAPI 0.115+ require the **new** call signature:

```python
# CORRECT (Starlette ≥ 1.0)
return templates.TemplateResponse(request, "page.html", {"foo": bar})

# WRONG (pre-1.0 form) — fails with TypeError: unhashable type: 'dict'
return templates.TemplateResponse("page.html", {"request": request, "foo": bar})
```

*Principle:* pin the framework version and use its current API form — mixed-era snippets
are a first-boot failure class.

### Python — pydantic-settings: always set `extra="ignore"`

`pydantic-settings` reads **the entire `.env` file** and validates every key. If `.env`
contains variables the model doesn't declare (`TEST_DATABASE_URL`, `EDITOR`, CI vars), it
raises `ValidationError: Extra inputs are not permitted`.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APPNAME_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # ← required — .env may contain vars we don't own
    )
```

*Principle:* config loaders must tolerate unowned keys in shared env files — `.env` is a
commons.

### Python — replacing an async init function in tests

Monkeypatch an async `init_db()` with an async noop — not a sync lambda:

```python
# CORRECT
async def _noop(): pass
monkeypatch.setattr("mypackage.agent.runner.init_db", _noop)

# WRONG — breaks await
monkeypatch.setattr("mypackage.agent.runner.init_db", lambda: None)
```

*Principle:* test doubles must match the interface's sync/async shape exactly.

### Any web stack — pipeline errors render an error page, never a raw exception response

When an LLM pipeline step fails (provider 4xx/5xx, invalid response, timeout), the failure
propagates back to the route via the pipeline state's `error` field. Render a readable
error page/response with a retry path — don't re-raise it as a bare framework exception
(a naked JSON 422/500).

*Principle:* every route that invokes the pipeline follows this; the error template/shape
always exists and links back to the start.
