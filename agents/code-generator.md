---
name: code-generator
description: Implements ONE independent slice (backend `src/`, frontend, or both) plus its tests. Spawned in parallel, one per slice.
tools: Read, Write, Edit, Bash, Grep, Glob
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/code-generator.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `code-generator` as a native sub-agent.
