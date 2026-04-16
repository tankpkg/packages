# Package Type Decision Guide

Sources: Tank Contributing Standard (AGENTS.md), Tank atom specification, production bundle analysis

Covers: identifying the correct package type for any use case, choosing between
instruction-only and multi-atom formats, common atom combinations, and
anti-patterns in package design.

## The Two Formats

Tank supports exactly two package formats. Every package is one or the other.

### Instruction-Only Skill

A single `SKILL.md` instruction blob with optional reference files. No build
step, no atoms array. Tank auto-generates a single instruction atom at install.

```
skills/{kebab-name}/
  SKILL.md              # Required -- frontmatter + body (<200 lines)
  tank.json             # Required -- metadata + permissions (no atoms field)
  references/           # Optional -- deep docs (250-450 lines each)
  scripts/              # Optional -- executable code
  assets/               # Optional -- templates, images
```

Best for: domain knowledge, best practices, methodology guides, coding
standards, framework expertise, workflow documentation.

### Multi-Atom Bundle

A package with an `atoms` array in `tank.json` containing typed primitives.
Each atom is a discrete unit of agent capability.

```
bundles/{kebab-name}/
  tank.json             # Required -- metadata + permissions + atoms array
  SKILL.md              # Optional -- instruction content (referenced by atom)
  hooks/                # Optional -- JS/TS hook handlers
  references/           # Optional -- deep docs (250-450 lines each)
  scripts/              # Optional -- executable code
  assets/               # Optional -- templates, images
```

Best for: lifecycle hooks, sub-agents, policy enforcement, MCP tool wiring,
prompt templates, data resources, or any combination of the above.

## The Eight Atom Kinds

Every atom in Tank's system is one of these eight kinds. Each has a
specialized creator skill.

### 1. Instruction

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `instruction`                      |
| Purpose   | Behavioral context injected into the agent |
| Required  | `content` (file path to markdown)  |
| Creator   | `@tank/skill-creator`              |

When to use: the agent needs domain knowledge, coding standards, workflow
steps, or decision frameworks loaded into its system prompt.

Signals:
- "The agent needs to know about X"
- "Follow these coding standards"
- "Use this methodology"
- Pure text, no enforcement needed

### 2. Hook

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `hook`                             |
| Purpose   | Code that runs at lifecycle events |
| Required  | `event`, `handler`                 |
| Creator   | `@tank/hook-creator`               |

When to use: intercept agent behavior at a specific lifecycle point. Hooks
can block, allow, rewrite, or inject context.

Signals:
- "Before the agent stops, check if..."
- "After the agent writes a file, run..."
- "When a session starts, inject..."
- "Block the agent from doing X"
- Need to run code (shell commands, API calls, delegation)

### 3. Agent

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `agent`                            |
| Purpose   | Named role with tools and permissions |
| Required  | `name`, `role`                     |
| Creator   | `@tank/agent-creator`              |

When to use: delegate a specific task to a sub-agent with constrained tools
and an explicit role identity.

Signals:
- "Review the code changes"
- "Audit for security issues"
- "Update the documentation"
- Need a specialist with a narrower tool set than the main agent
- Need readonly access for analysis tasks

### 4. Rule

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `rule`                             |
| Purpose   | Declarative validation constraint  |
| Required  | `event`, `policy`                  |
| Creator   | `@tank/rule-creator`               |

When to use: enforce a static policy without writing code. Rules are
data, not logic -- the runtime evaluates them.

Signals:
- "Block command X"
- "Warn when pattern Y appears"
- "Only allow tools A, B, C"
- Simple match-and-act pair, no conditional logic needed
- Policy can be expressed as a single sentence

### 5. Tool

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `tool`                             |
| Purpose   | MCP server registration            |
| Required  | `name`                             |
| Creator   | `@tank/tool-creator`               |

When to use: wire an existing MCP server into the agent's harness so
its tools become available.

Signals:
- "Connect to this MCP server"
- "Make this tool available to the agent"
- "Register a database/API/service tool"
- MCP server already exists; need a thin wiring layer
- Never for building the MCP server itself

### 6. Resource

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `resource`                         |
| Purpose   | URI-addressable data the agent can read |
| Required  | `uri`                              |
| Creator   | `@tank/resource-creator`           |

When to use: expose data the agent can pull on demand rather than having
it injected every session.

Signals:
- "The agent sometimes needs to reference X"
- "Expose the project architecture map"
- "Make the style guide available"
- Content is large, situational, or task-specific
- Content changes per environment or run

### 7. Prompt

| Field     | Value                              |
| --------- | ---------------------------------- |
| Kind      | `prompt`                           |
| Purpose   | Reusable invocable template        |
| Required  | `name`, `template`                 |
| Creator   | `@tank/prompt-creator`             |

When to use: create a parameterized template the user invokes by name
or slash command.

Signals:
- "Generate a commit message with this format"
- "Create a PR description template"
- "Slash command for incident reports"
- User triggers it on demand, not every session
- Output has a consistent structure with variable slots

### 8. Composite (Bundle of Atoms)

Not a distinct atom kind but a design pattern: combining multiple atom
kinds in a single bundle to create a cohesive capability.

Creator: `@tank/bundle-creator` (the scaffold) + specific creators for
each atom kind used.

Signals:
- Need more than one atom kind
- Atoms interact (hook delegates to agent, rule gates a tool)
- Single installable package delivers a complete workflow

## Format Decision Flowchart

Follow this sequence to determine which format to use:

```
START
  |
  v
Does the package need ONLY to teach the agent knowledge?
  |
  +-- YES --> Instruction-only skill
  |           Use @tank/skill-creator
  |
  +-- NO
      |
      v
      Does it need any of these?
        - Lifecycle hooks (intercept behavior)
        - Sub-agents (delegated specialists)
        - Rules (declarative enforcement)
        - Tools (MCP server wiring)
        - Resources (on-demand data)
        - Prompts (invocable templates)
      |
      +-- YES --> Multi-atom bundle
      |           Use @tank/bundle-creator + specific creators
      |
      +-- NO --> Instruction-only skill (default)
```

## Common Bundle Compositions

### Quality Gate (hook + agent + instruction)

Intercepts `pre-stop`, delegates review to a readonly agent, blocks
the agent from stopping if critical issues exist.

Atoms: 1 hook (pre-stop), 1 agent (reviewer), 1 instruction (context).

### Safety Policy (rules + instruction)

Declares a set of block/warn rules for dangerous operations. The
instruction explains the rationale so the agent self-corrects.

Atoms: N rules (one per concern), 1 instruction (rationale).

### Tool Integration (tool + instruction)

Wires an MCP server and provides usage guidance so the agent knows
when and why to use the tool.

Atoms: 1 tool (wiring), 1 instruction (guidance).

### Workflow Automation (prompt + agent + hook)

A prompt template generates structured output, an agent processes it,
and a hook triggers the workflow at the right lifecycle point.

Atoms: 1 prompt (template), 1 agent (processor), 1 hook (trigger).

### Context Provider (resource + instruction)

Exposes on-demand data with behavioral guidance for when to read it.

Atoms: 1 resource (data), 1 instruction (guidance).

### Full Enforcement Pipeline (hook + agent + rule + instruction)

The most complex pattern. A hook intercepts an event, delegates to an
agent for analysis, rules enforce policies on the findings, and the
instruction ties everything together.

Atoms: 1 hook (interceptor), 1 agent (analyzer), N rules (policies),
1 instruction (context).

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Using a bundle when a skill suffices | Unnecessary complexity | If all atoms would be instruction, use a skill |
| Every atom kind in one bundle | Over-engineered, hard to maintain | Compose only what the capability requires |
| Duplicating instruction content in hook code | Drift, double maintenance | Single source of truth in SKILL.md |
| Building MCP server code inside a tool atom | Stale, wrong abstraction | Tool atoms are wiring, not implementation |
| One agent with all tools | Diluted expertise | Least-privilege, one responsibility per agent |
| Rules for complex conditional logic | Rules are data, not code | Use hooks for conditional logic |
| Prompt atoms for always-needed context | Prompts are on-demand | Use instruction atoms for ambient context |
| Resources for small, always-relevant data | Resources are pull-model | Use instruction atoms for small ambient data |

## Package Naming Conventions

- Directory: `skills/{kebab-name}/` for instruction-only, `bundles/{kebab-name}/` for multi-atom
- Package name: `@tank/{kebab-name}` -- must match between SKILL.md and tank.json
- Name the package for the CAPABILITY, not the implementation
- Max 64 characters for the `{kebab-name}` portion
- Lowercase, digits, hyphens only

Good names: `@tank/quality-gate`, `@tank/react`, `@tank/security-review`
Bad names: `@tank/hook-agent-rule-combo`, `@tank/my-bundle`, `@tank/v2`

## Deciding Between Similar Atom Kinds

### Instruction vs Resource

| Signal | Instruction | Resource |
|--------|-------------|----------|
| Always relevant | Yes | Overkill |
| Under 50 lines | Yes | Overkill |
| Large data (>50 lines) | Bloats context | Yes |
| Situational or task-specific | Wasteful | Yes |
| Changes per environment | Cannot | Yes |

### Instruction vs Prompt

| Signal | Instruction | Prompt |
|--------|-------------|--------|
| Agent needs this every session | Yes | No |
| User invokes by name/command | No | Yes |
| Has variable slots | No | Yes |
| Produces structured output on demand | No | Yes |

### Rule vs Hook

| Signal | Rule | Hook |
|--------|------|------|
| Simple match-and-act pair | Yes | Overkill |
| Static policy | Yes | Overkill |
| Conditional logic needed | Cannot | Yes |
| External API calls needed | Cannot | Yes |
| Agent delegation needed | Cannot | Yes |
| Dynamic rewriting | Cannot | Yes |

### Tool vs Resource

| Signal | Tool | Resource |
|--------|------|----------|
| Agent invokes operations (create, update, delete) | Yes | No |
| Agent reads data on demand | No | Yes |
| Backed by an MCP server with callable tools | Yes | No |
| Backed by a static or dynamic data source | No | Yes |
