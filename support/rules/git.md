# Git Discipline

All git rules that apply to every session driving a build, fix, or sync — on any platform. Only the ROOT SESSION (or, on Claude Code, the project-builder orchestrator it delegates git to) runs git — other delegated workers never commit, push, or branch.

---

## Branch Model

- **Builds never land on the default branch directly.** Nothing a `/zero-shot-build` run produces — no application code, no generated feature, no phase output — is ever committed straight to `main`/`master`. Everything lands on a feature branch and reaches the default branch only through a PR **the user merges** — the build never merges its own PR.
- **The build's PR targets `<base>` (the branch it was cut from), NOT `main`.** Open it with `--base "$base"` so the generated increment stays isolated and reviewable on its own branch. If `<base>` IS the default branch (the normal case in a user's own project), the PR simply targets it — the point is the user reviews and merges, never the build.
- **Branch names carry a date-time slug so they are always unique.** Use `feature/<slug>-$(date +%Y%m%d-%H%M)-v0.1` — the timestamp guarantees no clash with branches from earlier runs, local or remote. **Before creating it, check the name is free on origin** (`git ls-remote --heads origin "$name"`); if it somehow exists, bump the timestamp. **Never `git checkout` an existing feature branch to build into** — reusing a prior build's branch imports that build's spec and stack (a live run reused `feature/up-police-data-analyst-v0.1` and inherited an old ASP.NET+MSSQL project, then tried `dotnet`/Docker on a Python box).
- **Start every fresh build from a clean baseline.** Before scaffolding, confirm the branch you're on doesn't already carry a *different* build's spec or app tree. An existing filled `spec/` is fine when you're intentionally adding a capability to that project; it is contamination when you're starting a new build — in that case stop and confirm with the user; do not silently continue on a prior build's branch.
- **Never `git checkout`/switch branches over a dirty tree.** Commit or stash first — uncommitted `spec/` edits cause "local changes would be overwritten by checkout" and the switch fails mid-build.
- **Branch every build from the CURRENT HEAD.** Capture where you are first: `base=$(git rev-parse --abbrev-ref HEAD)` — call it `<base>` — then `git checkout -b feature/<slug>-$(date +%Y%m%d-%H%M)-v0.1` from there. Never `git checkout main` first — the user parked this session on the branch they want built against; silently switching to the default branch builds against the wrong base.
- All phase commits go to the feature branch, never to the default branch.
- If you find yourself on the default branch while writing application code, stop immediately, create the feature branch, and continue there.
- **Accidental commit to the default branch? Revert, don't panic.** Fix it with `git revert <sha>` (never force-push/rewrite shared history) and push. The feature-branch copy remains the canonical source. Document the revert in the PR.


---

## Commit + Push Are One Atomic Action

**Every commit must be pushed immediately.** `git commit` and `git push` are a single atomic action — never one without the other.

```bash
git commit -m "phase-N: what you did" && git push origin <branch>
```

A commit that is not pushed does not exist as far as the project is concerned. This is not optional and survives context compression — if you remember only one rule: **commit then push, every time, no exceptions.**

---

## PR Must Exist Before the First Feature-Branch Commit

After creating the feature branch and pushing the first commit, immediately open a PR — based on `<base>` (the branch you cut from, captured before `checkout -b`):

```bash
base=$(git rev-parse --abbrev-ref HEAD)   # BEFORE checkout -b — this is <base>
branch="feature/<slug>-$(date +%Y%m%d-%H%M)-v0.1"   # date-time slug keeps it unique
git checkout -b "$branch"
# ... first commit + push ...
gh pr create --base "$base" --head "$branch"
```

Every subsequent `git push` automatically updates the same PR. Pushing commits without an open PR is equivalent to committing without pushing: the work is invisible and unreviewable.

---

## Before Every Reply to the User

1. Run `git status`
2. If dirty: commit and push with `git commit -m "..." && git push origin <branch>`
3. Confirm the working tree is clean **and** the branch is pushed before replying

---

## Commit Message Format

```
phase-N: [what you did]
```

Examples:
- `phase-1: add domain models`
- `phase-2: stub agent loop end-to-end`
- `harness: add git discipline doc`

The diff shows the *what*. The message answers: *why was this change needed, and what is the outcome?*

---

## Staging Rules

- **Never `git add -A` or `git add .`** — always stage specific files or directories. `-A` sweeps in untracked leftovers from prior build attempts (stray packages, abandoned experiments) and poisons the commit.
- If a phase needs many files, list them explicitly or stage directories one at a time.
- Run `git diff --staged` before every commit. You are responsible for what you push.

---

## Commit Quality

- **Commits are logical units.** Each commit should be a self-contained, reviewable change. "Fix bug and refactor and add feature" is three commits.
- **No commented-out code in commits.** If code is not needed, delete it. Git history preserves it.
- **Never commit secrets** — no API keys, passwords, or tokens in source files. See `secret-hygiene.md`. The `.env` containing API keys is the only manual user step and must stay gitignored — `.env.example` is committed, `.env` is never staged.
- **Never force-push without explicit user confirmation.**

---

## PR Description

Every PR needs:
- What changed
- Why
- How to verify

Screenshots or test output for UI/behavioural changes.

---

## Phase Gate: Git Checklist

A phase is not complete until:
- [ ] All code for the phase is committed
- [ ] Commit is pushed to the feature branch
- [ ] Working tree is clean (`git status` shows nothing)
- [ ] Phase test-handoff published; for a build, the human has tested and approved the phase

To see phase history: `git log --oneline | grep "phase-"`

---

## Closing a Session

Before ending any session:
- [ ] Working tree is clean (all changes committed and pushed)
- [ ] Branch is up to date with remote
