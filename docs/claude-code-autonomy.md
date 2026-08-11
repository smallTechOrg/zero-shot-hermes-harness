# Claude Code — Autonomy setup

The build is autonomous *within* a phase — that only works if Claude Code isn't pausing
for permission on every edit, test run, and `git push`. In the **project you're building
in** (not the harness repo), create or extend `.claude/settings.json` with this preset:

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

## Why it's shaped this way

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

## Notes

- If the file already exists, **merge** these keys — don't replace it (and never remove
  existing deny rules).
- Committed allow rules take effect only after you accept the **workspace trust dialog**
  the first time Claude Code opens the project — if prompts persist after setup, check
  `/permissions`.
- Personal extras belong in `.claude/settings.local.json` (auto-gitignored), not in the
  shared file.
- For OS-level enforcement on top (subprocess file reads, `rm -rf` outside the repo), add
  `"sandbox": {"enabled": true}`.
