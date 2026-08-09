---
name: agent-builder
description: Orchestrator — plans phases, fans out code-generator instances per slice in parallel, owns the git/PR surface for a build.
tools: Read, Grep, Glob, Bash, Task
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/agent-builder.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `agent-builder` as a native sub-agent.
