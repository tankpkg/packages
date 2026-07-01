# Role Design for Tank Agent Atoms

Sources: Tank Contributing Standard (AGENTS.md), quality-gate bundle patterns, multi-agent system design principles, production agent analysis

Covers: designing effective agent roles — identity-first definition, tool scoping with least-privilege, readonly vs read-write decisions, single-responsibility per agent, composing multiple agents in one bundle, and common role design mistakes.

## Identity-First Role Definition

The `role` field is the most important field in an agent atom. It determines
how the agent behaves, what it prioritizes, and how it communicates.

### The Three-Part Role Pattern

Effective roles follow a three-part structure:

1. **Identity declaration** — WHO the agent is
2. **Task scope** — WHAT it does (and does not do)
3. **Output contract** — HOW it reports results

```
"role": "[IDENTITY]. [TASK SCOPE]. [OUTPUT CONTRACT]."
```

Example from the quality-gate bundle:

```
"Senior code reviewer. Review ONLY the modified files/hunks provided.
Categorize every issue as critical, high, medium, or low. Focus on bugs,
security, correctness, and maintainability. Do NOT review
style/formatting — linters handle that. Be concise: one line per issue
with file, line, severity, and what's wrong."
```

Breaking this down:
- Identity: "Senior code reviewer"
- Task scope: "Review ONLY the modified files/hunks provided" + focus areas + exclusions
- Output contract: "one line per issue with file, line, severity, and what's wrong"

### Identity Archetypes

Choose an identity that signals expertise level and behavioral expectations:

| Archetype | Role Prefix | Behavioral Signal |
|-----------|------------|-------------------|
| Reviewer | "Senior code reviewer" | Opinionated, flags issues, does not fix |
| Auditor | "Security auditor" | Thorough, risk-focused, conservative |
| Maintainer | "Documentation maintainer" | Keeps artifacts in sync with code |
| Specialist | "Performance specialist" | Deep expertise in one domain |
| Generator | "Test generator" | Produces new artifacts from specifications |
| Fixer | "Bug fixer" | Receives issue reports, produces patches |
| Orchestrator | "Task coordinator" | Delegates to other agents, tracks progress |
| Scout | "Dependency scout" | Explores, reports findings, never modifies |

### Role Length Guidelines

| Model Tier | Max Role Length | Reasoning |
|-----------|----------------|-----------|
| `fast` | 2-3 sentences | Fast models lose focus on long prompts |
| `balanced` | 3-5 sentences | Room for nuance without overload |
| `powerful` | 5-8 sentences | Complex roles need more context |

Exceeding these limits does not cause errors but degrades agent quality.
Move detailed instructions to a companion `instruction` atom instead.

## Tool Scoping: Least-Privilege

Every tool granted to an agent is a capability and a risk. Apply
least-privilege rigorously.

### The Tool Audit Process

For each tool in the `tools` array, answer:

1. Does the agent's role REQUIRE this tool to function?
2. Can the agent achieve the same result with a less powerful tool?
3. What is the worst outcome if the agent misuses this tool?

If any answer raises concern, remove the tool.

### Tool Privilege Levels

Tools are not equal in risk. Order from least to most privilege:

| Level | Tools | Risk Profile |
|-------|-------|-------------|
| Observe | `read`, `grep`, `glob` | Read-only file access, zero mutation risk |
| Analyze | `lsp`, `fetch` | Read-only with external dependencies |
| Mutate | `write`, `edit` | Creates or modifies files |
| Execute | `bash` | Arbitrary command execution |
| Delegate | `task` | Can spawn other agents |
| External | `mcp`, `browser` | Interacts with external systems |

### Common Tool Sets by Role

| Agent Role | Tool Set | Rationale |
|-----------|----------|-----------|
| Code reviewer | `read`, `grep`, `glob`, `lsp` | Needs to navigate and understand code |
| Security auditor | `read`, `grep`, `glob` | Must not execute or modify anything |
| Doc updater | `read`, `write`, `grep`, `glob` | Reads code, writes documentation |
| Code fixer | `read`, `write`, `edit`, `grep`, `glob`, `lsp` | Full code modification capabilities |
| Test writer | `read`, `write`, `edit`, `grep`, `glob`, `bash` | Writes tests, runs them to verify |
| Dependency scout | `read`, `grep`, `glob`, `fetch` | Reads lockfiles, checks registries |
| Orchestrator | `read`, `grep`, `task` | Reads context, delegates work |

### Tools to Avoid Granting

| Tool | Avoid For | Reason |
|------|----------|--------|
| `bash` | Reviewers, auditors, scouts | Execution risk, not needed for analysis |
| `write` | Reviewers, auditors | Reviewers observe, they do not modify |
| `browser` | Most agents | Slow, expensive, rarely necessary |
| `mcp` | Agents without specific MCP needs | Broad capability, hard to constrain |
| `task` | Leaf agents | Only orchestrators need delegation |

## Readonly vs Read-Write

The `readonly` field is a coarse-grained safety control. When `true`,
platform adapters strip or block write-capable tools regardless of the
`tools` array.

### Decision Framework

```
Does the agent's role produce FILE OUTPUT?
  ├── No  → readonly: true
  │         (reviewers, auditors, scouts, analyzers)
  └── Yes → Does it CREATE new files or MODIFY existing ones?
            ├── Creates new → readonly: false, tools: ["write", ...]
            └── Modifies existing → readonly: false, tools: ["edit", ...]
```

### Readonly Agents (readonly: true)

These agents observe, analyze, and report. They never modify the
filesystem.

Characteristics:
- Output is text (reports, issue lists, recommendations)
- Tools are limited to `read`, `grep`, `glob`, `lsp`, `fetch`
- Safe to run on any codebase without risk
- Can be composed as pre-checks before mutating agents

### Read-Write Agents (readonly: false or omitted)

These agents produce file artifacts. They modify the codebase as part
of their role.

Characteristics:
- Output includes file changes (new files, patches, rewrites)
- Tools include `write`, `edit`, or `bash`
- Require review after execution (pair with a reviewer agent)
- Higher risk — test thoroughly before deployment

### The Readonly Paradox

Granting `readonly: true` while including `write` or `edit` in tools
creates a contradiction. Platform adapters handle this by:

1. Stripping the conflicting tools from the granted set
2. Logging a warning at install time
3. The `readonly` flag always wins

Avoid this contradiction by aligning `tools` with `readonly`.

## Single-Responsibility Principle

Each agent atom solves ONE problem. This is the most violated principle
in agent design.

### Signs of a Multi-Responsibility Agent

| Signal | Example | Fix |
|--------|---------|-----|
| Role has "and" connecting unrelated tasks | "Review code and update docs" | Split into reviewer + doc-updater |
| Tools span observe and mutate categories | `["read", "grep", "write", "bash"]` on a "reviewer" | Remove mutation tools from reviewer |
| Role describes multiple output formats | "Produce a review report and then fix the issues" | Reviewer reports, fixer fixes |
| Agent name contains "and" or "multi" | `"review-and-fix"` | Two agents: `reviewer`, `fixer` |

### The Composition Alternative

Instead of one complex agent, compose focused agents:

```json
{
  "atoms": [
    {
      "kind": "agent",
      "name": "reviewer",
      "role": "Review code. Report issues by severity.",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    },
    {
      "kind": "agent",
      "name": "fixer",
      "role": "Fix critical and high issues reported by the reviewer.",
      "tools": ["read", "write", "edit", "grep", "glob", "lsp"],
      "model": "balanced"
    }
  ]
}
```

Benefits:
- Each agent is simpler and more predictable
- Reviewer can be `fast` model, fixer needs `balanced`
- Reviewer is `readonly`, fixer is read-write
- Failures are isolated — reviewer failure does not corrupt files
- Agents can be reused independently in other bundles

## Composing Multi-Agent Bundles

Bundles that contain multiple agent atoms are the most powerful Tank
pattern. They enable workflows where agents hand off to each other.

### Composition Patterns

#### Sequential: Agent A then Agent B

Agent A runs first, produces output. Agent B consumes it.

Use case: reviewer identifies issues, fixer resolves them.

Coordination: a hook atom triggers Agent A, reads its output, then
triggers Agent B if needed.

#### Parallel: Agent A and Agent B simultaneously

Both agents run on the same input independently.

Use case: security auditor and performance reviewer both analyze the
same changeset.

Coordination: a hook atom triggers both, aggregates results.

#### Gated: Agent A decides if Agent B runs

Agent A acts as a filter. Agent B only runs if Agent A's output meets
a condition.

Use case: triage agent classifies the task, specialist agent handles
it if relevant.

Coordination: a rule atom evaluates Agent A's output, triggers Agent B
conditionally.

### Bundle Structure for Multi-Agent Packages

```json
{
  "name": "@tank/my-workflow",
  "version": "1.0.0",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" },
    { "kind": "hook", "event": "pre-stop", "handler": { "type": "js", "entry": "./hooks/orchestrate.ts" } },
    { "kind": "agent", "name": "agent-a", "role": "...", "tools": [...], "readonly": true },
    { "kind": "agent", "name": "agent-b", "role": "...", "tools": [...] },
    { "kind": "rule", "event": "pre-stop", "policy": "block", "reason": "Unresolved issues" }
  ]
}
```

### Agent Naming in Multi-Agent Bundles

| Principle | Example | Anti-Example |
|-----------|---------|-------------|
| Names describe function | `reviewer`, `fixer`, `scanner` | `agent-1`, `agent-2` |
| Names are unique per bundle | `security-auditor`, `perf-reviewer` | `reviewer`, `reviewer` |
| Names use kebab-case | `doc-updater` | `docUpdater`, `DocUpdater` |
| Names are short | `scanner` | `comprehensive-security-vulnerability-scanner` |

## Common Role Design Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| "Be helpful and thorough" | Vacuous — every agent is "helpful" | State specific expertise and constraints |
| Role describes tools, not behavior | "Uses grep to find patterns" | "Identify security patterns in code" |
| No negative constraints | Agent does everything, poorly | Add "Do NOT" clauses for adjacent tasks |
| Copying skill text as role | Passive knowledge, not active behavior | Transform knowledge into directives |
| Role references specific files | Breaks when used in different repos | Use generic patterns |
| Role contains platform-specific logic | Breaks portability | Move to `extensions` |
