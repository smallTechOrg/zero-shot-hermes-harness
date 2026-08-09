---
name: code-generator
description: Implements ONE independent slice (backend source, frontend, or both, per the spec's layout) plus its tests. Spawned in parallel, one per slice. Also builds the scaffold slice on a fresh project.
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/code-generator.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `code-generator` as a native sub-agent.

If the path above shows a literal unexpanded `${CLAUDE_PLUGIN_ROOT}`, locate the
installed `zero-shot-harness` plugin under `~/.claude/plugins/` and read
`support/agents/code-generator.md` from that plugin root instead.
