# OpenCode Agent Anatomy

Sources: OpenCode source (sst/opencode config.ts, agent.ts), oh-my-opencode
(agents/, config/schema), OpenCode SDK types.gen.d.ts

Covers: agent file formats, all configuration properties, permission system,
mode selection, model configuration, file locations, loading precedence.

## Two Configuration Formats

Agents can be defined in **Markdown** or **JSON**. Markdown is preferred for
custom agents — it's readable, self-contained, and the system prompt lives
naturally in the body.

### Format A: Markdown (Recommended)

Place `.md` files in agent directories. The **filename** (without `.md`) becomes
the agent name. YAML frontmatter = config. Body = system prompt.

```markdown
---
description: >-
  Use this agent when the user needs help with database schema design,
  migrations, query optimization, and PostgreSQL administration.
  
  Examples:
  
  <example>
  Context: User needs to design a database schema.
  user: "Help me design the schema for a multi-tenant SaaS app"
  assistant: "I'll use the db-architect agent for this schema design."
  </example>
mode: all
model: anthropic/claude-sonnet-4-6
temperature: 0.1
color: "#38A3EE"
permission:
  edit: ask
  bash:
    "*": ask
    "git diff": allow
    "psql *": allow
---

# System Prompt

You are a Senior Database Architect specializing in PostgreSQL...

## Your Expertise
- Schema design for production systems
- Query optimization and EXPLAIN ANALYZE interpretation
...
```

### Format B: JSON (in opencode.json)

Under the `"agent"` key. Best for overriding built-in agents or when you
prefer centralized config.

```json
{
  "agent": {
    "db-architect": {
      "description": "Database schema design and optimization specialist",
      "mode": "all",
      "model": "anthropic/claude-sonnet-4-6",
      "temperature": 0.1,
      "prompt": "You are a Senior Database Architect...",
      "permission": {
        "edit": "ask",
        "bash": { "*": "ask", "psql *": "allow" }
      },
      "color": "#38A3EE"
    }
  }
}
```

## File Locations (Precedence: lowest → highest)

| Scope | Path | Use Case |
|-------|------|----------|
| Global | `~/.config/opencode/agent/*.md` | Personal agents, all projects |
| Global | `~/.config/opencode/agents/*.md` | Alternate path |
| Global JSON | `~/.config/opencode/opencode.json` → `agent` | JSON format, global |
| Project | `.opencode/agent/*.md` | Project-specific agents |
| Project | `.opencode/agents/*.md` | Alternate path |
| Project JSON | `opencode.json` → `agent` | JSON format, project |
| Project JSON | `.opencode/opencode.json` → `agent` | Alt project path |

Higher-precedence configs override lower. Project > Global.

**For personal reusable agents → `~/.config/opencode/agent/`**
**For project-specific agents → `.opencode/agent/`**

## All Agent Properties

### Core Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `description` | string | **Yes** (subagents) | Shown in `@` autocomplete. Primary agents use this to decide WHEN to invoke the subagent. Include examples. |
| `mode` | enum | No (default: `"all"`) | `"primary"` = Tab-selectable main agent. `"subagent"` = @-mentionable only. `"all"` = both. |
| `model` | string | No | `"provider/model-id"` e.g. `"anthropic/claude-sonnet-4-6"`, `"openai/gpt-5.2"` |
| `variant` | string | No | Model variant. Only applies when agent's own model is used. |
| `prompt` | string | No | System prompt text. In JSON, can use `"{file:./path.txt}"` for file reference. In Markdown, the body IS the prompt. |
| `temperature` | number | No | 0.0–2.0. Lower = more deterministic. |
| `top_p` | number | No | 0.0–1.0. Alternative to temperature. |

### Execution Control

| Property | Type | Description |
|----------|------|-------------|
| `steps` | number | Max agentic iterations before forcing text-only response. |
| `maxSteps` | number | Deprecated alias for `steps`. |
| `options` | object | Provider-specific pass-through. E.g. `{ "reasoningEffort": "high" }` for OpenAI. |

### Display & Visibility

| Property | Type | Description |
|----------|------|-------------|
| `color` | string | Hex `"#FF5733"` or theme: `"primary"`, `"secondary"`, `"accent"`, `"success"`, `"warning"`, `"error"`, `"info"` |
| `hidden` | boolean | Hide from `@` autocomplete. Subagents only. |
| `disable` | boolean | Remove agent entirely (even built-ins). |

### Permissions

| Property | Type | Description |
|----------|------|-------------|
| `permission` | object | Fine-grained tool permissions. See Permission section. |
| `tools` | object | **Deprecated.** `Record<string, boolean>`. Use `permission` instead. |

## Permission System

Each tool can be set to:
- `"allow"` — run without asking user
- `"ask"` — prompt user before running
- `"deny"` — disable entirely

### Simple Permissions

```yaml
permission:
  edit: deny        # Cannot edit files
  bash: ask         # Must ask before running any command
  webfetch: allow   # Can fetch URLs freely
```

### Per-Command Bash Permissions

```yaml
permission:
  bash:
    "*": ask              # Default: ask for everything
    "git status *": allow # But allow git status
    "git diff *": allow   # And git diff
    "git push": deny      # Never push
    "rm *": deny          # Never delete
    "psql *": allow       # Allow postgres commands
```

### Tool-Specific Permissions

```yaml
permission:
  edit: deny              # Read-only agent
  bash:
    "*": deny
    "git log *": allow
    "git diff *": allow
  webfetch: deny
  task:
    "*": deny
    "explore": allow      # Can only delegate to explore
```

### Common Permission Patterns

| Pattern | edit | bash | webfetch | Use Case |
|---------|------|------|----------|----------|
| Full access | allow | allow | allow | Primary coding agent |
| Read-only reviewer | deny | `git diff: allow` | deny | Code reviewer |
| Researcher | deny | deny | allow | Documentation agent |
| Restricted executor | ask | `{specific: allow}` | deny | Task-specific agent |

## The Description Field (Critical)

The `description` is the **most important field for subagents**. The primary
agent (Sisyphus/build) reads descriptions to decide which subagent to invoke.

### What Makes a Good Description

1. **Start with "Use this agent when..."** — frames the trigger condition
2. **Include 3-5 examples** with `<example>` tags showing user→assistant flow
3. **Be specific about the domain** — "database migrations" not "technical tasks"
4. **Mention what it does NOT do** — helps avoid incorrect routing

### Description Template

```yaml
description: >-
  Use this agent when the user needs help with [DOMAIN].
  This includes [TASK 1], [TASK 2], and [TASK 3].
  This agent excels at [STRENGTH].

  Examples:

  <example>
  Context: [Situation]
  user: "[User message]"
  assistant: "I'll use the [agent-name] agent to [action]."
  <commentary>
  [Why this agent is the right choice]
  </commentary>
  </example>

  <example>
  Context: [Different situation]
  user: "[User message]"
  assistant: "I'll use the [agent-name] agent to [action]."
  </example>
```

## Mode Selection Guide

| Mode | Visible In | Invoked By | Best For |
|------|-----------|------------|----------|
| `primary` | Tab switcher | User selects tab | Main working agents (like Sisyphus, plan) |
| `subagent` | `@` menu | Primary agent delegates, or user @-mentions | Specialists invoked on demand |
| `all` | Both | Both methods | Versatile agents useful both ways |

**Default `"all"`** — works in most cases. Use `"subagent"` when the agent
should only be invoked for specific tasks, never as a main agent.

## Model Selection

### Provider/Model Format

Always `"provider/model-id"`:

| Provider | Example |
|----------|---------|
| Anthropic | `anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5` |
| OpenAI | `openai/gpt-5.2`, `openai/gpt-5.3-codex` |
| Google | `google/gemini-3-pro`, `google/gemini-3-flash` |
| Custom | Defined in `opencode.json` `provider` section |

### Model Selection by Agent Role

| Agent Role | Recommended Tier | Why |
|------------|-----------------|-----|
| Deep reasoning / architecture | Opus / GPT-5.2+ | Complex multi-step thinking |
| Code generation / editing | Sonnet / GPT-5.2 | Good balance of speed + quality |
| Fast search / triage | Haiku / Flash | Speed matters, task is simple |
| Frontend / visual | Sonnet / Gemini Pro | Visual understanding helps |
| Review / critique | GPT-5.2+ (medium reasoning) | Needs critical thinking |

## Agent Loading Flow

1. OpenCode starts → reads config files in precedence order
2. Built-in agents registered (build, plan, general, explore, etc.)
3. Plugin agents added (oh-my-opencode adds Sisyphus, Oracle, etc.)
4. Markdown `.md` files scanned from agent directories
5. JSON config agents merged over existing
6. `disable: true` removes agents
7. Final agent registry available to user

### How Markdown Files Are Parsed

```
filename.md → gray-matter parses YAML frontmatter
filename (without .md) → agent name
frontmatter fields → agent config
body text → system prompt
```

The agent name comes from the **filename**, not from any frontmatter field.
Choose filenames that are short, kebab-case identifiers.

## Quick Reference: Minimal Agent

Smallest valid agent (`~/.config/opencode/agent/reviewer.md`):

```markdown
---
description: Code review specialist. Reviews PRs for bugs and best practices.
mode: subagent
permission:
  edit: deny
  bash:
    "*": deny
    "git diff *": allow
---
You are a code reviewer. Read code carefully and provide constructive feedback.
Focus on bugs, security issues, and maintainability.
Never modify files directly.
```

This creates a read-only reviewer agent accessible via `@reviewer`.
