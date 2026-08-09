# Hermes — install & autonomy

## Install

**Tap the repo (recommended)** — the skills reference the shared `support/` tree, and the
tap preserves the whole layout so those references resolve without any extra step:

```bash
hermes skills tap add smallTechOrg/zero-shot-harness
/reload-skills        # or restart Hermes
```

**Or per-skill install** (deterministic, survives `/reload-skills`) — then also place the
shared `support/` tree where the installed skills expect it (`~/.hermes/support`):

```bash
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-build --name zero-shot-build --yes
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-fix   --name zero-shot-fix   --yes
hermes skills install smallTechOrg/zero-shot-harness/skills/zero-shot-sync  --name zero-shot-sync  --yes
git clone --depth 1 https://github.com/smallTechOrg/zero-shot-harness /tmp/zsh \
  && rm -rf ~/.hermes/support && cp -R /tmp/zsh/support ~/.hermes/support && rm -rf /tmp/zsh
```

Confirm with `hermes skills list` — the three skills should show `enabled`. To pull
updates later, re-run the installs with `--force` and refresh `~/.hermes/support`.

> **Security scan.** Skills installed from a community source are scanned on install.
> These skills reference the shared `support/` tree by name and include git-branch
> commands in prose — both can trip heuristic flags. If a scan blocks the install with a
> CAUTION verdict you've reviewed, re-run the `install` with `--force`.

## Autonomy

On Hermes there is no per-project permissions file — the root session orchestrates
directly and delegates *leaf work* (spec-writing, one code slice, one audit) to the roles
in `support/agents/` via `delegate_task` when available, **inline otherwise**. There is no
orchestrator sub-agent (delegated workers cannot spawn their own workers, cannot talk to
the user, and their background processes are killed on return), so the `project-builder`
role is **Claude-only and never runs on Hermes**.

Platform sharp edges the build skill accounts for are documented in
`skills/zero-shot-build/references/hermes-pitfalls.md`.
