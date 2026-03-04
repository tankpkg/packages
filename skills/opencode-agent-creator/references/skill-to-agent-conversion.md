# Skill-to-Agent Conversion

Sources: Tank skill ecosystem (36 skills analyzed), oh-my-opencode skill
injection system, OpenCode agent architecture

Covers: when to convert vs when to keep as skill, conversion process,
extracting role from domain knowledge, transformation patterns.

## Skills vs Agents: When to Convert

Skills and agents serve different purposes. Not every skill should become
an agent, and not every agent needs a skill.

### Skills (Domain Knowledge Injection)

- Loaded on-demand into ANY agent's prompt
- Passive — add knowledge, not behavior
- Shared across multiple agents via `load_skills=[]`
- Best for: reusable domain expertise

### Agents (Autonomous Role Executors)

- Standalone entities with their own model, tools, permissions
- Active — make decisions, refuse work, follow procedures
- Invocable directly via `@agent-name` or Tab switching
- Best for: specialized workflows needing distinct behavior

### Decision Matrix

| Situation | Use Skill | Use Agent | Use Both |
|-----------|-----------|-----------|----------|
| Domain knowledge needed by multiple agents | ✅ | | |
| Need distinct model/temperature | | ✅ | |
| Need tool restrictions (read-only, etc.) | | ✅ | |
| Need opinionated personality | | ✅ | |
| Domain expertise + specialized workflow | | | ✅ |
| Simple reference information | ✅ | | |
| Interactive role (asks questions, pushes back) | | ✅ | |
| Background task execution | | ✅ | |

### The "Both" Pattern

Create an agent that also loads the corresponding skill:

```markdown
---
description: Frontend architecture specialist. Uses React patterns skill.
mode: all
model: anthropic/claude-sonnet-4-6
---
You are a Senior Frontend Architect...
```

Then in oh-my-opencode, when delegating:
```
delegate_task(category="visual-engineering", load_skills=["react", "frontend-craft"])
```

The agent provides **role and behavior**. The skill provides **deep knowledge**.

## Conversion Process

### Step 1: Analyze the Source Skill

Read the SKILL.md and its reference files. Extract:

| Extract | From | Becomes |
|---------|------|---------|
| Domain scope | `description` field, Core Philosophy | Agent's expertise boundaries |
| Decision frameworks | Decision trees, tables | Agent's behavioral directives |
| Anti-patterns | "What NOT to do" sections | Agent's NEVER rules |
| Workflow steps | Quick-Start sections | Agent's operational approach |
| Best practices | Reference files | Agent's standards |

### Step 2: Define the Agent Role

Transform passive knowledge into active role:

**Skill says** (passive):
```
Covers: React hooks, state management, performance optimization,
component architecture, testing patterns.
```

**Agent becomes** (active):
```
You are a Senior React Architect. You design component architectures,
optimize rendering performance, and enforce React best practices.
You refuse to write class components and push back on prop drilling.
```

### Step 3: Extract Behavioral Rules

Convert skill guidelines into agent directives:

**Skill guideline** (informational):
```
Prefer computed signals over effects. Effects should be used
sparingly and only for side effects.
```

**Agent directive** (behavioral):
```
NEVER use useEffect for derived state. If you catch yourself
writing useEffect to compute something from other state, STOP
and use useMemo or a computed value instead.
```

### Step 4: Define Tool Permissions

Based on the agent's role, restrict tools appropriately:

| Agent Role | edit | bash | webfetch |
|-----------|------|------|----------|
| Frontend Specialist | allow | `npm/yarn: allow`, others: ask | allow |
| Code Reviewer | deny | `git diff: allow` | deny |
| API Designer | ask | `curl: allow` | allow |
| Documentation Writer | allow | deny | allow |
| Security Auditor | deny | `git log: allow` | allow |

### Step 5: Write the Agent File

Combine all extracted elements into a markdown agent file.

## Transformation Patterns

### Pattern 1: Single Skill → Specialist Agent

**Source**: `skills/react/SKILL.md` (240 lines, hooks/state/performance)

**Transformation**:
- Core Philosophy → Role identity
- Decision trees → Behavioral directives
- Anti-patterns → NEVER rules
- Quick-Start problems → What the agent handles

**Result**: `react-architect.md`
```markdown
---
description: >-
  Use this agent for React component architecture, hooks patterns,
  state management decisions, and performance optimization.
  Excels at translating requirements into clean React implementations.
mode: all
model: anthropic/claude-sonnet-4-6
temperature: 0.1
---
You are a Senior React Architect. 12+ years with React, from
class components through hooks to Server Components.

## Expertise
- Component composition and architecture
- Custom hooks design
- State management (local, context, server state)
- Performance optimization (memo, useMemo, useCallback)
- React 19+ patterns (Server Components, Suspense)

## Standards
- Functional components only. No class components.
- Custom hooks for shared logic. No HOCs.
- TypeScript strict mode. No `any`.
- Composition over inheritance. Always.

## Rules (CRITICAL)
- NEVER use useEffect for derived state
- NEVER use index as key in dynamic lists
- NEVER suppress TypeScript errors with `as any`
- ALWAYS check if shadcn/ui has the component before building custom
```

### Pattern 2: Multiple Skills → Composite Agent

Combine related skills into one agent:

**Sources**: `react` + `typescript` + `frontend-craft` + `tailwind`

**Result**: `frontend-engineer.md` — a comprehensive frontend specialist
that draws expertise from all four skill domains.

Extract the most important rules from each:
- From `react`: Component patterns, hooks rules
- From `typescript`: Type safety, no `any`
- From `frontend-craft`: Micro-interactions, perceived performance
- From `tailwind`: Utility-first, responsive patterns

### Pattern 3: Skill → Reviewer Agent

Convert domain knowledge into review criteria:

**Source**: `clean-code/SKILL.md` (code smells, SOLID, refactoring)

**Result**: `code-reviewer.md`
```markdown
---
description: Reviews code for quality, maintainability, and best practices.
mode: subagent
permission:
  edit: deny
  bash:
    "*": deny
    "git diff *": allow
---
You are a code quality reviewer guided by Clean Code principles.

## Review Checklist (in priority order)
1. **Readability**: Can another developer understand this in 30 seconds?
2. **Single Responsibility**: Does each function/class do one thing?
3. **DRY violations**: Is logic duplicated that should be shared?
4. **Naming**: Are names self-documenting?
5. **Error handling**: Are errors caught and handled properly?
6. **Complexity**: Can any function be simplified?

## Feedback Format
- 🔴 CRITICAL: [description] — must fix
- 🟡 WARNING: [description] — should fix
- 🟢 SUGGESTION: [description] — nice to have

NEVER suggest changes outside the diff being reviewed.
```

### Pattern 4: Skill → Planner Agent

Convert methodology into a planning process:

**Source**: `planning/SKILL.md` (task decomposition, estimation, risk)

**Result**: `tech-planner.md`
```markdown
---
description: Creates technical implementation plans with task breakdowns.
mode: subagent
model: anthropic/claude-opus-4-6
permission:
  edit: ask
  bash:
    "*": deny
    "git log *": allow
---
You are a Technical Planner. You create implementation plans, NOT code.

## Planning Process
1. Understand the goal (ask if unclear)
2. Survey existing code (use grep/read tools)
3. Identify affected files and dependencies
4. Break into ordered tasks (max 2-hour chunks)
5. Identify risks and unknowns
6. Estimate effort per task

## Output Format
# Implementation Plan: [Title]
## Tasks
1. [Task] — [estimate] — [risk level]
...
## Dependencies
## Risks
## Open Questions
```

## What NOT to Convert

| Skill Type | Why Not Agent |
|-----------|--------------|
| Reference-only (API docs) | No behavior to encode — stays as skill |
| Tool-specific (playwright) | Tool knowledge, not a role — stays as skill |
| Meta-skills (skill-creator) | Process skill, not domain — stays as skill |
| Very narrow scope (token-redaction) | Too narrow for an agent — stays as skill |

## Verifying the Conversion

After creating the agent, test:

1. **Role boundary test**: Ask it to do something outside its scope
   - Expected: Refuses politely, suggests who to delegate to
2. **Expertise test**: Ask a domain-specific question
   - Expected: Confident, specific, opinionated answer
3. **Anti-pattern test**: Propose a known anti-pattern
   - Expected: Pushes back, explains why it's wrong
4. **Workflow test**: Give it a realistic task
   - Expected: Follows the operational approach defined in prompt
