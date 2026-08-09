# Hermes skills — install & invoke

The three skills in `harness/skills/` are designed to run **inside a local
[Hermes](https://github.com/NousResearch/hermes-agent) install**, not as files
in your agent codebase. This keeps the harness out of every project you build
while still giving Hermes the full build/fix/sync loop.

## What gets installed

| Destination | Contents |
|---|---|
| `~/.hermes/skills/zero-shot-build/` | the build-loop skill (`SKILL.md` + `references/`) |
| `~/.hermes/skills/zero-shot-fix/` | the diagnose-and-fix skill |
| `~/.hermes/skills/zero-shot-sync/` | the spec↔code drift-sync skill |
| `~/.hermes/skills/zero-shot-harness-support/` | **one shared copy** of everything the skills reference — `agents/`, `patterns/`, `rules/`, `commands/` |

The install script rewrites each skill's relative `harness/...` references to an
**absolute path** pointing at the shared support dir. Result: skills are fully
self-contained — no `harness/` directory needs to exist at your project root at
runtime, and every role/pattern/rule file lives in exactly one place you can
open, edit, and verify.

## Install

```bash
# from the harness repo root (this script lives at the repo root):
bash install-hermes-skills.sh

# or override destinations:
HERMES_SKILLS_DIR=/path/to/skills bash install-hermes-skills.sh
```

It is **idempotent** — re-running it refreshes all three skills + the support
dir. To remove everything it installed:

```bash
bash install-hermes-skills.sh --uninstall
```

## Verify the install

```bash
# Hermes lists loaded skills; the three should appear:
ls ~/.hermes/skills | grep zero-shot

# the relative refs should now be absolute and resolve:
grep -rn "harness/" ~/.hermes/skills/zero-shot-build/SKILL.md || echo "OK: no relative harness/ refs remain"
test -f ~/.hermes/skills/zero-shot-harness-support/agents/qa-auditor.md && echo "OK: support roles present"
```

Then start (or restart) Hermes. The skills load on startup — no extra config.

## Invoke

The skills are `disable-model-invocation: true`, so **you trigger them
explicitly** (Hermes won't auto-fire them). Use the `/<skill>` form:

| Your prompt | What runs |
|---|---|
| `/zero-shot-build <idea>` | Full intake → design → phase-by-phase build → human testing gate → ship. Leave `<idea>` empty to be asked. |
| `/zero-shot-fix <bug \| error \| "tests" \| "drift">` | qa-auditor diagnoses + classifies (SPEC vs CODE), code-generator fixes, qa-auditor re-gates. |
| `/zero-shot-sync [scope]` | Whole-tree drift audit; reconciles code to spec (spec wins); verifies CLEAN. |

Example:

```
/zero-shot-build a CLI that turns meeting notes into a tagged task list
/zero-shot-fix the /health endpoint returns 500 after the auth slice
/zero-shot-sync
```

### Editing after install

Everything is plain Markdown under `~/.hermes/skills/`. To change build
behaviour, edit the skill `SKILL.md`; to change a role's behaviour (e.g. how the
qa-auditor classifies drift), edit the file in `zero-shot-harness-support/`.
Hermes re-reads skills on each invocation, so changes take effect immediately —
no restart needed for content edits.

> **Keeping in sync with upstream:** re-run `install-hermes-skills.sh` after
> pulling new harness changes. It overwrites the local copies with the latest
> from the repo.
