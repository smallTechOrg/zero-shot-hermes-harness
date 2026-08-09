---
name: project-builder
description: Orchestrator — plans phases, fans out code-generator instances per slice in parallel, owns the git/PR surface for a build. Invoked by /zero-shot-build, one phase per invocation.
tools: Read, Grep, Glob, Bash, Task
model: inherit
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/project-builder.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `project-builder` as a native sub-agent.

If the path above shows a literal unexpanded `${CLAUDE_PLUGIN_ROOT}`, locate the
installed `zero-shot-harness` plugin under `~/.claude/plugins/` and read
`support/agents/project-builder.md` from that plugin root instead.
