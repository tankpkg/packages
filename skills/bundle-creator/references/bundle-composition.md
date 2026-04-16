# Bundle Composition Patterns

Sources: Tank Contributing Standard (AGENTS.md), @tank/quality-gate bundle,
Tank registry conventions (2025-2026).

Covers: when to compose which atoms together, what makes a good bundle vs a
bad one, sizing signals, skill-vs-bundle decision, permission scoping, and
anti-patterns to avoid.

## Skill vs Bundle Decision

The fundamental question: does the package need machine enforcement or just
context injection?

| Need                                         | Answer              |
| -------------------------------------------- | ------------------- |
| Domain knowledge, best practices, workflows  | Instruction-only    |
| Lifecycle interception (pre-stop, pre-write)  | Bundle with hook    |
| Delegatable sub-agent with tool constraints  | Bundle with agent   |
| Declarative policy enforcement               | Bundle with rule    |
| MCP server integration                       | Bundle with tool    |
| External data source                         | Bundle with resource|
| Slash command or prompt template             | Bundle with prompt  |

If every atom in your planned bundle would be `instruction`, stop and
create an instruction-only skill instead. Bundles exist for atoms that
need the runtime, not for organizing prose.

## Atom Composition Patterns

### Pattern 1: Hook + Agent + Instruction

The most common bundle pattern. A hook intercepts a lifecycle event,
delegates to a sub-agent for analysis, and uses the agent's response
to decide whether to block, continue, or inject context.

**When to use:** Automated quality gates, pre-commit checks, code review,
security scanning, documentation validation.

**Atom roles:**
- `hook`: Intercepts the event, orchestrates the flow
- `agent`: Performs the analysis (readonly, constrained tools)
- `instruction`: Gives the agent and the hook behavioral context

**Example:** @tank/quality-gate uses `pre-stop` hook -> `code-reviewer`
agent -> instruction with severity definitions.

**Wiring:** The hook handler calls `delegateToAgent(agentName, prompt)`.
The agent name in the delegation call must match the agent atom's `name`.

### Pattern 2: Rule + Instruction

Lightweight enforcement without custom code. The runtime enforces the
rule declaratively. The instruction explains the rationale so the agent
understands why it was blocked.

**When to use:** Simple allow/block policies, guardrails, safety nets
that do not need conditional logic.

**Atom roles:**
- `rule`: Declares the policy (block/warn/allow on event)
- `instruction`: Explains the "why" so the agent can self-correct

**Example:** A "no-force-push" bundle:

```json
"atoms": [
  {
    "kind": "rule",
    "event": "pre-command",
    "policy": "block",
    "reason": "Force push to main is prohibited"
  },
  {
    "kind": "instruction",
    "content": "./SKILL.md"
  }
]
```

### Pattern 3: Tool + Instruction

Registers an external MCP tool and provides instructions on when and how
to use it.

**When to use:** Integrating external services (linters, APIs, databases)
that the agent should call during its work.

**Atom roles:**
- `tool`: Registers the MCP server
- `instruction`: Teaches the agent when to invoke the tool and how to
  interpret its output

### Pattern 4: Resource + Prompt + Instruction

Exposes data and provides a templated way to query it.

**When to use:** Knowledge bases, schema references, configuration
lookups where the agent needs both the data and a structured way to
query it.

**Atom roles:**
- `resource`: Makes data available
- `prompt`: Provides a structured query template
- `instruction`: Explains the data model and query patterns

### Pattern 5: Hook + Rule (Layered Enforcement)

Combines declarative rules with programmatic hooks for defense in depth.
The rule provides a fast, unconditional check. The hook adds conditional
logic for nuanced cases.

**When to use:** Security-critical workflows where you want both a hard
stop (rule) and a smart analysis (hook).

## Sizing Signals

### When a bundle is too small

| Signal                               | Action                      |
| ------------------------------------ | --------------------------- |
| Single instruction atom only         | Convert to skill            |
| Hook does nothing but log            | Remove the hook             |
| Agent has no tools                   | Merge role into instruction |
| Rule never triggers in practice      | Remove or soften to warn    |

### When a bundle is too large

| Signal                               | Action                      |
| ------------------------------------ | --------------------------- |
| 7+ atoms                            | Split into focused bundles  |
| Multiple unrelated hook events       | Split by event domain       |
| Agent has 8+ tools                   | Reduce tool scope           |
| Permissions cover everything         | Audit and restrict          |
| SKILL.md exceeds 200 lines          | Move detail to references/  |

### Right-sizing guidance

Most bundles have 2-4 atoms. The canonical @tank/quality-gate has 3 atoms
(hook + agent + instruction). Resist the urge to add atoms "just in case."
Each atom should have a clear, testable purpose.

## Permission Scoping

Permissions in tank.json are the union of what all atoms need. Follow
the principle of least privilege:

### Network

| Atom needs                           | Permission                    |
| ------------------------------------ | ----------------------------- |
| No external calls                    | `"outbound": []`              |
| Calls specific API                   | `"outbound": ["api.host.com"]`|
| Calls multiple APIs                  | List each hostname explicitly |

Never use wildcard network access. List each hostname.

### Filesystem

| Atom needs                           | Permission                    |
| ------------------------------------ | ----------------------------- |
| Read project files (most bundles)    | `"read": ["**/*"]`            |
| Write reports                        | `"write": ["reports/**"]`     |
| Write to specific dir                | `"write": ["output/*.json"]`  |

Never grant write to `["**/*"]` unless the bundle genuinely needs to
write anywhere in the project.

### Subprocess

| Atom needs                           | Permission                    |
| ------------------------------------ | ----------------------------- |
| No child processes                   | `"subprocess": false`         |
| Hook runs git commands               | `"subprocess": true`          |
| Hook runs test suite                 | `"subprocess": true`          |

The @tank/quality-gate sets `subprocess: false` in its tank.json but its
hook actually uses `git diff`. This works because the hook runs through
the agent's existing shell capabilities. Set `subprocess: true` only when
the hook handler itself spawns processes outside the agent's tool chain.

## Agent Design Within Bundles

### Role String

The agent's `role` field is its system prompt. Write it as a direct
instruction to the agent:

**Good:** "Senior code reviewer. Flag bugs and security issues by
severity. Output one line per issue: [SEVERITY] file:line - description."

**Bad:** "This agent is a code reviewer that helps find bugs."

### Tool Selection

Grant the minimum tools the agent needs:

| Agent purpose              | Typical tools                    |
| -------------------------- | -------------------------------- |
| Code review (readonly)     | `read`, `grep`, `glob`, `lsp`   |
| Documentation writer       | `read`, `write`, `grep`         |
| Test runner                | `read`, `bash`, `grep`          |
| Security scanner           | `read`, `grep`, `glob`, `fetch` |

### Readonly Flag

Set `readonly: true` for agents that should never modify files. This is
a safety net — even if the role prompt says "do not write," the readonly
flag enforces it mechanically.

## Anti-Patterns

### The Kitchen Sink Bundle

**Symptom:** 8+ atoms, broad permissions, does "everything."
**Fix:** Split into focused bundles. One capability per bundle.

### The Instruction-Only "Bundle"

**Symptom:** All atoms are `instruction` kind. No hooks, agents, or rules.
**Fix:** Convert to an instruction-only skill. Remove the atoms array.

### The Overprivileged Agent

**Symptom:** Agent has `tools: ["bash", "write", "edit", "mcp"]` but only
reads files.
**Fix:** Reduce to `["read", "grep"]` and add `readonly: true`.

### The Silent Hook

**Symptom:** Hook intercepts an event but only logs — never blocks,
rewrites, or delegates.
**Fix:** Either add meaningful logic or remove the hook.

### The Orphan Atom

**Symptom:** Agent atom defined but never delegated to by any hook.
Rule atom on event no hook handles.
**Fix:** Wire the atom or remove it. Every atom must participate.

### The Missing Instruction

**Symptom:** Bundle has hooks and agents but no instruction atom. The
agent lacks context about what the bundle does and why.
**Fix:** Add an instruction atom with a SKILL.md explaining the bundle's
purpose, severity definitions, and expected behavior.

## Composition Checklist

Before publishing a bundle, verify:

1. Every atom has a clear, testable purpose
2. No atom is orphaned (unreferenced by any flow)
3. Permissions are the minimum union of all atom needs
4. Agent tools are scoped to actual requirements
5. Hook handlers reference existing files
6. Instruction content is under 200 lines
7. The bundle name describes the capability, not the plumbing
8. The bundle has fewer than 7 atoms (ideally 2-4)

See `references/tank-json-anatomy.md` for the full schema of each field.
See `references/worked-examples.md` for concrete bundle walkthroughs.
