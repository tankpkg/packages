# Agent Atom Anatomy

Sources: Tank Contributing Standard (AGENTS.md), quality-gate bundle (canonical example), Tank atom specification

Covers: the complete schema for `kind: "agent"` atoms in Tank bundles — required fields, optional fields, canonical tool names, model tiers, extension bags, and how agent atoms differ from standalone platform-specific agents.

## What Is an Agent Atom

An agent atom is a typed primitive inside a Tank bundle's `tank.json`. It
declares a named role that platform adapters translate into whatever agent
format the target harness expects. The atom itself is portable — it contains
no platform-specific logic.

Agent atoms live in the `atoms` array of a multi-atom package:

```json
{
  "name": "@tank/my-bundle",
  "version": "1.0.0",
  "atoms": [
    {
      "kind": "agent",
      "name": "code-reviewer",
      "role": "Senior code reviewer. Review modified files only.",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    }
  ]
}
```

The `kind` field must be `"agent"`. This distinguishes it from the six other
atom kinds: `instruction`, `hook`, `rule`, `tool`, `resource`, and `prompt`.

## Required Fields

Every agent atom must include these two fields. Omitting either causes a
validation error.

### `name` (string, required)

The agent's identifier within the bundle. Used by hooks, rules, and other
atoms to reference this agent. Must be kebab-case.

```json
"name": "code-reviewer"
```

Rules for naming:
- Lowercase, digits, hyphens only
- Descriptive of the agent's function
- Unique within the bundle (no two agent atoms share a name)
- Short — prefer `reviewer` over `comprehensive-code-quality-reviewer`

### `role` (string, required)

A concise description of the agent's identity, expertise, and behavioral
constraints. This is the agent's system prompt in compressed form. Platform
adapters expand it into whatever format the harness requires.

```json
"role": "Senior code reviewer. Review ONLY the modified files/hunks provided. Categorize every issue as critical, high, medium, or low. Focus on bugs, security, correctness, and maintainability. Do NOT review style/formatting — linters handle that. Be concise: one line per issue with file, line, severity, and what's wrong."
```

Guidelines for writing effective roles:
- Lead with WHO the agent is: "Senior code reviewer", "Security auditor",
  "Documentation maintainer"
- Follow with WHAT it does: specific task scope
- Include CONSTRAINTS: what it must not do
- Keep it under three sentences for `fast` model agents
- Allow up to five sentences for `powerful` model agents that need nuance
- Use imperative form: "Review", "Categorize", "Focus on"
- Include output format expectations when relevant

## Optional Fields

These fields refine agent behavior. Omitting them applies sensible defaults.

### `tools` (string array, optional)

The set of canonical tool names the agent can access. Omitting grants no
tools — the agent can only reason and respond, not take actions.

```json
"tools": ["read", "grep", "glob", "lsp"]
```

Apply least-privilege: grant only tools the agent needs for its stated role.

### Canonical Tool Reference

| Name | Capability | Typical Use |
|------|-----------|-------------|
| `bash` | Execute shell commands | Build, test, install, run scripts |
| `read` | Read file contents | Inspect code, config, docs |
| `write` | Create or overwrite files | Generate new files |
| `edit` | Modify existing files | Patch, refactor, fix code |
| `grep` | Search file contents by pattern | Find usages, patterns, strings |
| `glob` | Find files by name pattern | Discover file structure |
| `lsp` | Language server operations | Go-to-definition, references, diagnostics |
| `mcp` | Invoke MCP server tools | External service integration |
| `browser` | Web browser automation | Scraping, testing, visual verification |
| `fetch` | HTTP requests | API calls, download resources |
| `git` | Git operations | Diff, log, blame, branch |
| `task` | Delegate to subagents | Orchestration, parallel work |
| `notebook` | Notebook operations | Jupyter, observable notebooks |

Custom tool names are also accepted. Platform adapters map them to their
local equivalents or ignore unknown names gracefully.

### `model` (string, optional)

The computational tier for this agent. Determines the trade-off between
speed, cost, and reasoning depth.

```json
"model": "fast"
```

| Tier | When to Use | Trade-off |
|------|------------|-----------|
| `fast` | Pattern matching, triage, formatting, simple review | Fastest, cheapest, least depth |
| `balanced` | Code generation, editing, moderate analysis | Default for most agents |
| `powerful` | Architecture decisions, security audit, complex reasoning | Slowest, most expensive, deepest |
| `custom` | Specific model required by use case | Set value to vendor model ID string |

When `model` is omitted, the platform adapter chooses its own default
(typically `balanced`).

For `custom`, provide the vendor model identifier directly:

```json
"model": "anthropic/claude-sonnet-4-20250514"
```

### `readonly` (boolean, optional)

When `true`, the agent must not modify files or execute destructive commands.
Platform adapters enforce this by stripping write-capable tools or adding
permission restrictions.

```json
"readonly": true
```

Default: `false` (the agent can use all granted tools without restriction).

Set `readonly: true` for:
- Code reviewers
- Security auditors
- Architecture analyzers
- Dependency scanners
- Any agent whose role is observation, not mutation

### `extensions` (object, optional)

Platform-specific overrides. Each key is a platform adapter name, and the
value is an opaque object passed through without validation. The core Tank
spec does not interpret extensions — adapters own their shape.

```json
{
  "kind": "agent",
  "name": "reviewer",
  "role": "Code reviewer.",
  "tools": ["read", "grep"],
  "readonly": true,
  "extensions": {
    "opencode": {
      "mode": "subagent",
      "temperature": 0.1,
      "color": "#4CAF50"
    },
    "cursor": {
      "when": "code-review"
    }
  }
}
```

Use extensions to configure:
- Agent visibility mode (e.g., subagent-only vs user-facing)
- Temperature and sampling parameters
- UI presentation (color, icon, category)
- Platform-specific permissions beyond the canonical set
- Routing and delegation hints

## Agent Atoms vs Standalone Platform Agents

Tank agent atoms are not the same as platform-native agent files. The key
differences:

| Aspect | Tank Agent Atom | Platform Agent |
|--------|----------------|----------------|
| Location | `tank.json` `atoms` array | Platform-specific directory |
| Format | JSON object with typed fields | Markdown, YAML, or platform format |
| Portability | Works across any Tank-compatible harness | Locked to one platform |
| Role definition | `role` field (compact) | Full system prompt (verbose) |
| Tool permissions | Canonical names in `tools` array | Platform-specific permission syntax |
| Model selection | Tier names (`fast`, `balanced`, etc.) | Vendor model IDs |
| Composition | Multiple atoms in one bundle | Separate files per agent |
| Distribution | Installed via `tank install` | Manual copy or platform package manager |

### When to Use Agent Atoms

- Building reusable, distributable agent bundles
- Composing multi-agent workflows (reviewer + fixer + gate)
- Sharing agents across teams and projects
- Ensuring portability across harnesses

### When to Use Platform Agents Instead

- One-off personal agents for a specific workflow
- Agents that depend heavily on platform-specific features
- Prototyping before packaging as a Tank bundle

## Composition with Other Atom Kinds

Agent atoms gain power when combined with other atom kinds in the same
bundle.

### Agent + Hook

A hook triggers the agent at a lifecycle point. The quality-gate bundle
pairs a `pre-stop` hook with a `code-reviewer` agent — the hook detects
modified code files and delegates review to the agent.

### Agent + Rule

A rule enforces a constraint based on the agent's output. If the agent
reports critical issues, a rule can block the session from stopping.

### Agent + Instruction

An instruction atom injects behavioral context. The agent handles the
role; the instruction provides domain knowledge, checklists, or review
criteria.

### Agent + Tool

A tool atom registers an MCP server. The agent references the tool by
name in its `tools` array to gain custom capabilities beyond the
canonical set.

## Validation Rules

Platform adapters validate agent atoms at install time. Expect errors for:

| Violation | Error |
|-----------|-------|
| Missing `name` | "Agent atom requires 'name' field" |
| Missing `role` | "Agent atom requires 'role' field" |
| Duplicate `name` in bundle | "Duplicate agent name in atoms array" |
| Empty `tools` array | Warning only — agent can reason without tools |
| Unknown tool name | Warning only — adapter may not support it |
| `readonly: true` with `write`/`edit`/`bash` tools | Warning — adapter may strip those tools |

## Complete Agent Atom Template

Minimal:

```json
{
  "kind": "agent",
  "name": "my-agent",
  "role": "Description of who this agent is and what it does."
}
```

Full:

```json
{
  "kind": "agent",
  "name": "my-agent",
  "role": "Description of who this agent is and what it does. Include constraints and output format expectations.",
  "tools": ["read", "grep", "glob"],
  "model": "balanced",
  "readonly": true,
  "extensions": {
    "platform-name": {
      "key": "value"
    }
  }
}
```
