# Zero-Shot Harness — spec-first, AI-native project building

Three skills for building software **spec-first and AI-natively**. Give it a one-line
idea; walk away with a working, tested, phased project — on whatever stack the
requirements pick. The skills are **repo-independent**: install them once and they
operate on whatever project repo you point them at. **No default stack, no boilerplate
to clone** — the spec derives the stack, designs the layout, and a scaffold gate proves
the skeleton runs before any feature work.

The `skills/` tree follows the open [Agent Skills](https://agentskills.io) standard, so
it runs on **Claude Code** (as a plugin), **Hermes** (as skills), and any other
Agent-Skills-compatible tool. The `support/` tree is the shared doctrine; only the thin
platform wrappers differ.

Every build is **AI-native by design**: the build process itself is an agentic
multi-role team, and every spec includes `spec/agent.md` — the design evaluated against
the agentic-patterns catalogue, even when the honest conclusion is "no AI capability
needed".

## Install — Claude Code

```
/plugin marketplace add smallTechOrg/zero-shot-harness
/plugin install zero-shot-harness@zero-shot-harness
```

The three skills, four sub-agents, and the shared `support/` material all come with the
plugin. Confirm with `/plugin` (it should list `zero-shot-harness` as enabled). Then do
the one-time **Autonomy setup** below for each project you build in.

## Autonomy setup (recommended — permissions out of the loop's way)

The build is autonomous *within* a phase — that only works if Claude Code isn't pausing
for permission on every edit, test run, and `git push`. In the **project you're building
in** (not this repo), create or extend `.claude/settings.json` with this preset:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Edit", "Write", "Read", "Bash", "WebSearch",
      "WebFetch(domain:github.com)", "WebFetch(domain:raw.githubusercontent.com)",
      "WebFetch(domain:docs.anthropic.com)", "WebFetch(domain:code.claude.com)"
    ],
    "deny": [
      "Read(.env)", "Read(/.env)", "Read(.env.local)", "Read(.env.production)",
      "Edit(.env)", "Read(secrets/**)", "Read(**/*.pem)", "Read(**/*.key)",
      "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.claude/.credentials.json)",
      "Bash(sudo *)",
      "Bash(rm -rf /*)", "Bash(rm -rf ~*)", "Bash(rm -rf ..*)", "Bash(rm -rf .)",
      "Bash(sh)", "Bash(sh -)", "Bash(sh -s*)",
      "Bash(bash)", "Bash(bash -)", "Bash(bash -s*)",
      "Bash(zsh)", "Bash(zsh -)", "Bash(zsh -s*)"
    ],
    "ask": [
      "Bash(git push --force*)", "Bash(git push * --force*)",
      "Bash(git push -f*)", "Bash(git push * -f*)",
      "Bash(git reset --hard*)", "Bash(git clean *)", "Bash(git filter-repo *)"
    ]
  }
}
```

What this gives you, and why it's shaped this way:

- **Zero prompts on the build loop** — broad `Edit`/`Write`/`Read`/`Bash` allow plus
  `defaultMode: acceptEdits`. Deliberately **not** `bypassPermissions`: the allow list
  already removes the friction, while keeping the deny/ask guardrails enforceable (and
  orgs can hard-disable bypass, which would break a preset that relied on it).
- **Secrets stay out of the model's context** — `.env`, key files, `~/.ssh`, `~/.aws`
  are denied. Your app and tests still load `.env` programmatically (a subprocess is not
  the agent reading it) — that's by design: the real-key testing doctrine depends on it.
- **Pipe-to-shell blocked** — `curl … | sh` can't be denied as one pattern (compound
  commands are split), so the preset denies the bare stdin-interpreter forms instead;
  `bash script.sh` and `bash -c "…"` still work.
- **History-destroying git asks first** — force-push, `reset --hard`, `git clean` prompt
  for confirmation instead of being blocked, because the sanctioned secret-rotation flow
  legitimately force-pushes with operator approval.

Notes: if the file already exists, **merge** these keys — don't replace it (and never
remove existing deny rules). Committed allow rules take effect only after you accept the
**workspace trust dialog** the first time Claude Code opens the project — if prompts
persist after setup, check `/permissions`. Personal extras belong in
`.claude/settings.local.json` (auto-gitignored), not in the shared file. For OS-level
enforcement on top (subprocess file reads, `rm -rf` outside the repo), add
`"sandbox": {"enabled": true}`.

## Install — Hermes

**Tap the repo (recommended)** — the skills reference the shared `support/` tree via
relative paths, and the tap preserves the whole layout:

```bash
hermes skills tap add smallTechOrg/zero-shot-harness
/reload-skills        # or restart Hermes
```

**Or per-skill install** (deterministic, survives `/reload-skills`) — then also place
the shared `support/` tree where the installed skills expect it (`~/.hermes/support`):

```bash
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-build --name zero-shot-build --yes
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-fix   --name zero-shot-fix   --yes
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-sync  --name zero-shot-sync  --yes
git clone --depth 1 https://github.com/smallTechOrg/zero-shot-harness /tmp/zsh \
  && rm -rf ~/.hermes/support && cp -R /tmp/zsh/support ~/.hermes/support && rm -rf /tmp/zsh
```

Confirm with `hermes skills list` — the three skills should show `enabled`. To pull
updates later, re-run the installs with `--force` and refresh `~/.hermes/support`.

## Invoke

The skills are `disable-model-invocation: true` — trigger them explicitly:

```
/zero-shot-build <idea>
/zero-shot-fix <bug | error | "tests" | "drift">
/zero-shot-sync [scope]
```

Or describe the goal in plain English and let the agent route it:

- **build** — "build me a tool/app/service that…", "add X to it" → creates the project /
  adds a capability
- **fix** — "it's erroring on…", "the tests fail" → diagnoses + fixes, then verifies
- **sync** — "make the code match the spec" → reconciles spec ↔ code (spec wins)

## The three skills

| Skill | Purpose |
|-------|---------|
| `zero-shot-build` | Idea → working, verified, phased project. Also adds a capability to an existing project. |
| `zero-shot-fix` | Diagnose + fix a bug / error / failing test / drift, then verify. |
| `zero-shot-sync` | Reconcile spec ↔ code (spec wins), then verify. |

## The Spirit

1. **Spec is the source of truth.** Written before code; when they disagree, the spec
   wins (`/zero-shot-sync`).
2. **AI-native by design.** Every spec includes `spec/agent.md` — the idea evaluated
   against the agentic-patterns catalogue. "No AI capability needed" is a legitimate
   written conclusion; an unexamined design is not.
3. **No default stack.** Your stated preferences are binding; everything else is derived
   from the requirements and recorded with rationale. The scaffold gate proves the
   skeleton runs before any feature work.
4. **Smallest first-time-right win, phase by phase.** Each phase ships the smallest
   increment a human can test, and it must work the *first* time.
5. **A human gates every phase.** Autonomous *within* a phase; stops at each boundary
   for you to test the increment.
6. **Real services or it doesn't count.** Gates run against the real external services
   the spec names — the real LLM when the design has AI capability, the production
   database engine always. A stubbed pass is not a pass.

## Layout

```
skills/
  zero-shot-build/   SKILL.md + references/hermes-pitfalls.md
  zero-shot-fix/     SKILL.md
  zero-shot-sync/    SKILL.md
support/             shared doctrine the skills reference (../../support/…)
  agents/            spec-writer, code-generator, qa-auditor (dual-mode)
                     + project-builder (Claude-only orchestrator — never run on Hermes)
  patterns/          spec-driven, phases, agentic-ai, test-driven, ui-ux, …
  rules/             ai-agents, git, secret-hygiene

.claude-plugin/      Claude Code wrapper: plugin.json + marketplace.json
agents/              Claude-native sub-agent pointers into support/agents/
CLAUDE.md            Claude entry point   (AGENTS.md / .hermes.md = Hermes)
```

The skills register as slash commands themselves — there is no separate commands layer,
so the skill file is the single source of truth for each flow.

Each `SKILL.md` is the process — follow it exactly; never improvise your own build/fix
flow.

## FAQ

**What if I already have a stack in mind?** State it in the idea:
`/zero-shot-build [idea] — use Python + FastAPI + PostgreSQL`. Stack choices are
binding. With no preference stated, the spec-writer derives the best fit from your
requirements and records the rationale in `spec/architecture.md`.

**Does every project get AI bolted on?** No. `spec/agent.md` is always *written*, but
"no AI capability needed" is a first-class conclusion — deterministic logic that fully
serves the requirements beats an LLM every time.

**What if something breaks?** `/zero-shot-fix [what's broken]` — the qa-auditor role
classifies SPEC vs CODE, the generator fixes, qa-auditor re-gates, the root commits +
pushes.

**What if spec and code drift?** `/zero-shot-sync` — qa-auditor audits, generators fix,
spec wins.

**Why didn't my build land on `main`?** By design. Builds live on feature branches
whose PRs target the branch they were cut from — you review and merge; the build never
merges its own PR.
