---
name: spec-writer
description: The single design authority — writes the FULL spec (vision, architecture with stack + layout + conventions, the AI-native design in spec/agent.md — always, phased roadmap) and self-reviews it.
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/spec-writer.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `spec-writer` as a native sub-agent.

If the path above shows a literal unexpanded `${CLAUDE_PLUGIN_ROOT}`, locate the
installed `zero-shot-harness` plugin under `~/.claude/plugins/` and read
`support/agents/spec-writer.md` from that plugin root instead.
