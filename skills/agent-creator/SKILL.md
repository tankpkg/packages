---
name: "@tank/agent-creator"
description: |
  Author Tank agent atoms — named roles with tools, permissions, and model
  tiers that embed in multi-atom bundles. Covers the agent atom schema
  (required and optional fields), role design (identity-first definition,
  tool scoping, least-privilege, readonly vs read-write), model tier
  selection (fast/balanced/powerful/custom), composing multi-agent bundles,
  and platform portability via extension bags. Harness-agnostic — agents
  are defined once in tank.json and translated by platform adapters.
  Synthesizes Tank Contributing Standard (AGENTS.md), quality-gate bundle
  patterns, and multi-agent system design principles.

  Trigger phrases: "create agent", "agent atom", "tank agent",
  "agent role", "agent bundle", "readonly agent", "agent tools",
  "define agent", "new agent atom", "multi-agent bundle",
  "agent model tier", "compose agents", "code reviewer agent",
  "security auditor agent", "agent permissions"
---

# Tank Agent Creator

## Core Philosophy

1. **Identity before instructions** — Define WHO the agent is (name + role)
   before configuring WHAT it can do (tools + model). A clear role drives
   behavior more than verbose prompts.

2. **Least-privilege tooling** — Grant only the tools the agent needs.
   A reviewer needs `read` and `grep`, not `write` and `bash`. Excess
   tools invite excess behavior.

3. **Readonly by default** — Mark agents `readonly: true` unless they must
   modify files. Most analysis, review, and audit agents never need write
   access. This prevents accidental mutations.

4. **One responsibility per agent** — Each agent atom solves one problem.
   Compose multiple single-purpose agents in a bundle rather than building
   one omniscient agent that does everything poorly.

5. **Portable, not vendor-locked** — Agent atoms are harness-agnostic.
   Platform-specific behavior goes in `extensions`, not in the core schema.
   The same agent definition works across any Tank-compatible harness.

## Quick-Start: Common Tasks

### "I need an agent that reviews code"

1. Define the atom in `tank.json`:
   ```json
   {
     "kind": "agent",
     "name": "code-reviewer",
     "role": "Senior code reviewer. Review modified files only. Categorize issues as critical/high/medium/low. Focus on bugs, security, correctness.",
     "tools": ["read", "grep", "glob", "lsp"],
     "model": "fast",
     "readonly": true
   }
   ```
2. Pair with a hook or rule atom to trigger the review automatically.
   -> See `references/worked-examples.md` for the full pattern.

### "I need an agent that modifies files"

1. Omit `readonly` (defaults to false) and add write tools:
   ```json
   {
     "kind": "agent",
     "name": "doc-updater",
     "role": "Documentation maintainer. Update docs to match code changes.",
     "tools": ["read", "write", "grep", "glob"],
     "model": "balanced"
   }
   ```
2. Grant `write` and/or `edit` only when the agent must produce file output.
   -> See `references/role-design.md` for the readonly decision framework.

### "I need multiple agents working together"

1. Define each agent as a separate atom in the same `tank.json`.
2. Give them different tool sets and model tiers.
3. Coordinate via hook or rule atoms.
   -> See `references/worked-examples.md` for the reviewer+fixer pattern.

### "Agent exists but isn't effective"

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Too generic output | Role is vague | Write a specific, opinionated role string |
| Does things it shouldn't | Too many tools granted | Remove unnecessary tools |
| Slow on simple tasks | Wrong model tier | Switch to `fast` for analysis tasks |
| Modifies files unexpectedly | Missing `readonly: true` | Add readonly for non-mutating agents |
| Works in one harness only | Platform logic in role | Move platform specifics to `extensions` |

## Decision Trees

### Tool Selection

| Agent Purpose | Recommended Tools | Readonly |
|--------------|-------------------|----------|
| Code review / audit | `read`, `grep`, `glob`, `lsp` | Yes |
| Security scanning | `read`, `grep`, `glob` | Yes |
| Documentation update | `read`, `write`, `grep`, `glob` | No |
| Code generation / fix | `read`, `write`, `edit`, `grep`, `glob`, `lsp` | No |
| Research / exploration | `read`, `grep`, `glob`, `fetch` | Yes |
| Test writing | `read`, `write`, `edit`, `grep`, `glob`, `bash` | No |
| Orchestration | `read`, `grep`, `task` | Yes |

### Model Tier Selection

| Task Complexity | Tier | Use When |
|----------------|------|----------|
| Pattern matching, formatting, triage | `fast` | Speed matters more than depth |
| Code generation, editing, analysis | `balanced` | Default for most agents |
| Architecture, security, complex reasoning | `powerful` | Accuracy is critical |
| Specific model required | `custom` | Vendor model ID as string |

### Canonical Tool Names

| Name | Capability |
|------|-----------|
| `bash` | Shell command execution |
| `read` | Read file contents |
| `write` | Create or overwrite files |
| `edit` | Modify existing files |
| `grep` | Search file contents |
| `glob` | Find files by pattern |
| `lsp` | Language server protocol |
| `mcp` | MCP server invocation |
| `browser` | Web browser automation |
| `fetch` | HTTP requests |
| `git` | Git operations |
| `task` | Subagent delegation |
| `notebook` | Notebook operations |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| One agent that does everything | Diluted expertise, tool sprawl | Split into focused agents |
| All tools granted to every agent | Unintended side effects | Least-privilege per role |
| Role string is a full essay | Models lose focus | Keep role under 3 sentences |
| Platform-specific logic in role | Breaks portability | Use `extensions` bag |
| No `readonly` on analysis agents | Accidental file mutations | Default to `readonly: true` |
| Duplicating role across bundles | Drift between copies | Extract to shared bundle |

## Reference Index

| File | Contents |
|------|----------|
| `references/agent-atom-anatomy.md` | Tank agent atom schema — required fields, optional fields, canonical tools, model tiers, extension bags, how agents differ from standalone platform agents |
| `references/role-design.md` | Designing effective agent roles — identity-first definition, tool scoping, readonly vs read-write, single-responsibility, composing multi-agent bundles |
| `references/worked-examples.md` | Four worked agent examples — code-reviewer, security-auditor, doc-updater, and a multi-agent reviewer+fixer bundle |
