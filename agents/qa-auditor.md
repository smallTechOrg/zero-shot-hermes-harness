---
name: qa-auditor
description: Independent review, runs gates/tests/app, audits spec↔code drift. Read-only; classifies root cause SPEC-vs-CODE.
tools: Read, Grep, Glob, Bash
---

Your full role definition is `${CLAUDE_PLUGIN_ROOT}/support/agents/qa-auditor.md`.

**Read that file first and follow it exactly** — it is the source of truth for this
role and is shared across Claude Code and Hermes. This file exists only so Claude
Code can discover `qa-auditor` as a native sub-agent.
