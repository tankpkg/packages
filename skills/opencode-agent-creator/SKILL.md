---
name: "@tank/opencode-agent-creator"
deprecated: true
superseded_by: "@tank/agent-creator"
description: |
  DEPRECATED: Use @tank/agent-creator instead for harness-agnostic agent
  creation. This skill is OpenCode-specific; @tank/agent-creator covers
  the generic Tank agent atom format that works across all harnesses.

  Original: Create specialized OpenCode agents that assume specific roles —
  frontend architect, DevOps SRE, database specialist, code reviewer, or any
  domain expert. Covers agent anatomy (markdown and JSON formats), role design
  (persona, expertise, behavioral directives), system prompt engineering,
  tool permissions, oh-my-opencode integration (categories, skill injection,
  delegation wiring), and converting existing Tank skills into standalone
  agents. Synthesizes OpenCode source (sst/opencode), oh-my-opencode v3.x
  agent system, and production agent analysis.

  Trigger phrases: "create agent", "opencode agent", "new agent",
  "convert skill to agent", "make an agent", "agent from skill",
  "custom agent", "specialized agent", "agent template", "agent for",
  "agent configuration", "agent role", "create a specialist",
  "build agent", ".opencode/agent"
---

# OpenCode Agent Creator

## Core Philosophy

1. **Role-first, not prompt-first** — Define WHO the agent is before WHAT
   it says. Identity drives behavior.
2. **Agents have opinions** — Effective agents push back, refuse out-of-scope
   work, and have strong preferences. Bland agents waste tokens.
3. **Minimum viable agent** — Start with 20 lines. Add complexity only when
   the agent fails at real tasks. Over-engineered prompts confuse models.
4. **Skills supplement, agents act** — Skills inject knowledge. Agents assume
   roles. Use both together for maximum effectiveness.

## Quick-Start: Create an Agent

### "I need a specialist agent for [DOMAIN]"

1. Determine the role archetype:
   → See `references/role-design.md` for archetypes table

2. Choose agent properties:
   - **Mode**: `all` for versatile, `subagent` for delegation-only
   - **Model**: Match complexity to role (see model selection guide)
   - **Temperature**: 0.0-0.3 for precision, 0.3-0.5 for creative
   - **Permissions**: Restrict tools based on role

3. Write the agent file:
   → Use `assets/agent-template.md` as starter
   → See `references/prompt-engineering.md` for prompt structure

4. Deploy:
   - Global: `~/.config/opencode/agent/<name>.md`
   - Project: `.opencode/agent/<name>.md`

5. Test with 5 patterns:
   - In-domain task → competent response
   - Out-of-scope request → polite refusal
   - Ambiguous request → asks clarifying question
   - Anti-pattern proposal → pushes back
   - Complex multi-step task → structured approach

### "I want to convert a skill into an agent"

1. Read the skill's SKILL.md and references
2. Extract: domain scope, decision frameworks, anti-patterns, workflows
3. Transform passive knowledge into active role directives
4. Add personality, boundaries, and tool restrictions
   → See `references/skill-to-agent-conversion.md`

### "Agent exists but isn't working well"

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Too generic/bland | No personality defined | Add opinions and preferences |
| Does things it shouldn't | No boundary section | Add "Outside Your Scope" |
| Asks too many questions | No decision framework | Add conditional directives |
| Ignores its restrictions | Prompt contradicts permissions | Align prompt with frontmatter |
| Doesn't appear in `@` menu | Wrong file location | Move to `~/.config/opencode/agent/` |
| Sisyphus doesn't delegate to it | Poor description | Add `<example>` tags to description |

## Agent File Format

Markdown file with YAML frontmatter. Filename = agent name.

```markdown
---
description: >-
  Use this agent when [TRIGGER CONDITION].
  Includes [TASK 1], [TASK 2], [TASK 3].
  
  <example>
  user: "[request]"
  assistant: "I'll use [agent] to [action]."
  </example>
mode: all
model: provider/model-id
temperature: 0.1
color: "#HEX"
permission:
  edit: allow|ask|deny
  bash:
    "*": ask
    "specific command": allow
---

[System prompt — the agent's role, expertise, and behavioral rules]
```

→ See `references/agent-anatomy.md` for complete property reference.

## Decision Trees

### Archetype Selection

| Need | Archetype | Key Config |
|------|-----------|------------|
| Writes code in a domain | Specialist | `edit: allow`, low temp |
| Reviews but doesn't modify | Reviewer | `edit: deny`, read-only bash |
| Gathers information | Researcher | `edit: deny`, `bash: deny`, `webfetch: allow` |
| Creates plans, not code | Planner | `edit: ask`, read-only bash |
| Coordinates other agents | Orchestrator | Full permissions, task tool |

### Model Tier Selection

| Role Complexity | Model Tier | Examples |
|----------------|-----------|----------|
| Deep reasoning / architecture | Opus / GPT-5.2+ | Solution architect, security auditor |
| Code generation / editing | Sonnet / GPT-5.2 | Frontend engineer, API developer |
| Fast search / simple tasks | Haiku / Flash | Explorer, formatter, triage |

### Where to Deploy

| Scope | Path | When |
|-------|------|------|
| All projects | `~/.config/opencode/agent/` | Personal workflow agents |
| One project | `.opencode/agent/` | Project-specific specialists |
| omo override | `oh-my-opencode.json` → `agents` | Modify built-in omo agents |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| "Be helpful and thorough" | Vacuous instructions | Specific behavioral directives |
| Agent does everything | No focus, mediocre at all tasks | Narrow to 1-2 domains |
| 200+ line prompt | Model loses focus | Under 150 lines, use skills for knowledge |
| No NEVER rules | Agent makes domain-specific mistakes | Add 3-5 hard constraints |
| Copying skill text verbatim | Passive knowledge, no agency | Transform into behavioral directives |
| No description examples | Primary agents can't route to it | Add 3-5 `<example>` tags |

## Reference Files

| File | Contents |
|------|----------|
| `references/agent-anatomy.md` | Full OpenCode agent schema, both formats, all properties, permission system, file locations |
| `references/role-design.md` | Role archetypes, persona construction, behavioral directives, decision frameworks, common mistakes |
| `references/prompt-engineering.md` | System prompt structure, directive patterns, tool restrictions, testing strategies, anti-patterns |
| `references/skill-to-agent-conversion.md` | When to convert, transformation process, patterns (specialist, reviewer, planner), verification |
| `references/omo-integration.md` | oh-my-opencode overrides, category system, skill injection, multi-model orchestration, deployment |
