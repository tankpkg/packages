# oh-my-opencode Integration

Sources: oh-my-opencode v3.x source (config/schema, agents/), oh-my-opencode
README, production oh-my-opencode.json configurations

Covers: agent overrides, category system, skill injection, delegation wiring,
built-in agent customization, multi-model orchestration.

## Architecture Overview

oh-my-opencode (omo) adds a layer on top of OpenCode's native agent system:

```
┌─────────────────────────────────────────┐
│  oh-my-opencode.json                    │
│  ├── agents: {} (overrides)             │
│  ├── categories: {} (model routing)     │
│  └── skills: {} (injection config)      │
├─────────────────────────────────────────┤
│  OpenCode Agent System                  │
│  ├── ~/.config/opencode/agent/*.md      │
│  ├── .opencode/agent/*.md               │
│  └── opencode.json → agent: {}          │
├─────────────────────────────────────────┤
│  Built-in Agents                        │
│  (build, plan, general, explore, etc.)  │
└─────────────────────────────────────────┘
```

**Your custom `.md` agents** live at the OpenCode layer. **omo overrides**
configure model routing and skill injection for built-in omo agents.

## Agent Overrides (oh-my-opencode.json)

Override built-in omo agents without modifying their source:

```json
{
  "agents": {
    "sisyphus": {
      "model": "anthropic/claude-opus-4-6",
      "variant": "max"
    },
    "oracle": {
      "model": "openai/gpt-5.2",
      "variant": "high"
    },
    "explore": {
      "model": "anthropic/claude-haiku-4-5"
    },
    "librarian": {
      "model": "anthropic/claude-sonnet-4-6"
    }
  }
}
```

### Override Properties

| Property | Type | Description |
|----------|------|-------------|
| `model` | string | Override model (provider/model format) |
| `variant` | string | Model variant (`"max"`, `"high"`, `"medium"`, `"low"`) |
| `prompt_append` | string | Append text to the agent's system prompt |
| `skills` | string[] | Skills to inject into agent prompt |
| `temperature` | number | Override temperature |
| `top_p` | number | Override top_p |
| `tools` | object | Override tool permissions |
| `disable` | boolean | Disable this agent entirely |
| `description` | string | Override description |
| `mode` | enum | Override mode |
| `color` | string | Override UI color |
| `permission` | object | Override permissions |

### Disabling Built-in Agents

```json
{
  "disabled_agents": ["multimodal-looker"],
  "agents": {
    "atlas": { "disable": true }
  }
}
```

## The Category System

Categories enable **intent-based model routing**. Instead of picking a model
for every task, Sisyphus picks a category based on the task's nature.

### Built-in Categories

| Category | Default Model | Best For |
|----------|---------------|----------|
| `quick` | Claude Haiku | Trivial tasks, single file changes |
| `visual-engineering` | Claude Sonnet | Frontend, UI/UX, design, styling |
| `ultrabrain` | GPT-5.3 Codex (xhigh) | Deep reasoning, complex architecture |
| `artistry` | Claude Sonnet | Creative/artistic tasks |
| `unspecified-low` | Claude Sonnet | Misc low-effort tasks |
| `unspecified-high` | Claude Opus (max) | Misc high-effort tasks |
| `writing` | Claude Sonnet | Documentation, prose |
| `deep` | GPT-5.3 Codex (medium) | General deep tasks |

### Custom Categories

Create your own categories for domain-specific routing:

```json
{
  "categories": {
    "devops": {
      "model": "openai/gpt-5.2",
      "variant": "medium",
      "description": "Infrastructure and DevOps tasks"
    },
    "data-engineering": {
      "model": "anthropic/claude-opus-4-6",
      "variant": "max",
      "description": "Data pipeline and ETL tasks"
    }
  }
}
```

### How Sisyphus Uses Categories

When delegating, Sisyphus picks category + skills:

```
delegate_task(
  category="visual-engineering",
  load_skills=["react", "frontend-craft"],
  prompt="Build the dashboard component..."
)
```

The category determines **which model** runs the task. The skills determine
**what expertise** is injected into the subagent's prompt.

## Connecting Custom Agents to omo

### Method 1: Standalone Agent (Independent of Sisyphus)

Create a `.md` file in `~/.config/opencode/agent/`. This agent is accessible
via `@agent-name` or Tab switching. Sisyphus can also invoke it via the
Task tool if the description is clear enough.

This is the simplest and most common approach. The agent stands on its own.

### Method 2: Category-Routed Agent (Via Sisyphus)

Create a custom category that uses your preferred model and skill set.
Sisyphus delegates to this category when the task matches.

```json
{
  "categories": {
    "frontend-specialist": {
      "model": "anthropic/claude-sonnet-4-6",
      "description": "Frontend development with React expertise"
    }
  }
}
```

Now Sisyphus can:
```
delegate_task(
  category="frontend-specialist",
  load_skills=["react", "tailwind"],
  prompt="..."
)
```

### Method 3: Agent + Skill Combo

For maximum power, create BOTH:
- An **agent** (`.md` file) for direct use via `@agent-name`
- A **skill** that Sisyphus injects when delegating related tasks

This way the expertise is available both directly and through delegation.

## Skill Injection

omo injects skill content into subagent prompts at delegation time.

### How It Works

1. User (or Sisyphus) calls `delegate_task(load_skills=["react"])`
2. omo finds the skill's SKILL.md in the skill directories
3. SKILL.md content is injected into the subagent's system prompt
4. Subagent now has both its own prompt AND the skill's knowledge

### Skill Sources (checked in order)

| Location | Type |
|----------|------|
| `~/.config/opencode/skills/*/SKILL.md` | Global installed skills |
| `.opencode/skills/*/SKILL.md` | Project-local skills |
| oh-my-opencode built-in skills | Plugin-bundled skills |

### Configuring Skill Sources

```json
{
  "skills": {
    "sources": [
      { "path": "./custom-skills", "recursive": true }
    ],
    "enable": ["my-custom-skill"],
    "disable": ["playwright"]
  }
}
```

## Multi-Model Orchestration Patterns

### Pattern 1: Tiered Delegation

Sisyphus (expensive) delegates to cheaper specialists:

```
Sisyphus (Opus) → Quick tasks → Haiku
                → Frontend → Sonnet
                → Architecture → GPT-5.2
                → Exploration → Haiku
```

### Pattern 2: Parallel Background Agents

Fire multiple agents simultaneously:

```
delegate_task(subagent_type="explore", run_in_background=true, ...)
delegate_task(subagent_type="librarian", run_in_background=true, ...)
// Continue working, collect results later
```

### Pattern 3: Agent Chain

One agent's output feeds another:

```
Planner → creates plan
  ↓
Reviewer → validates plan
  ↓
Executor → implements plan
  ↓
Tester → verifies implementation
```

## Deployment Checklist

### For Standalone Agents (Method 1)

1. Create `~/.config/opencode/agent/<name>.md`
2. Verify agent appears in `@` autocomplete
3. Test with in-domain and out-of-scope requests
4. Verify tool permissions work as expected

### For Category-Routed Agents (Method 2)

1. Add category to `~/.config/opencode/oh-my-opencode.json`
2. Verify Sisyphus recognizes the category
3. Test delegation with `delegate_task(category="...")`

### For Agent + Skill Combos (Method 3)

1. Create agent `.md` file
2. Create or verify skill exists
3. Test direct invocation via `@agent-name`
4. Test delegation with `delegate_task(load_skills=[...])`

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Agent doesn't appear in `@` | File not in agent directory | Check path: `~/.config/opencode/agent/` |
| Agent appears but wrong model | Override not applied | Check oh-my-opencode.json `agents` section |
| Sisyphus doesn't delegate to agent | Poor description | Add examples with `<example>` tags |
| Skills not loading | Wrong skill directory | Check `~/.config/opencode/skills/` |
| Agent ignores permissions | Prompt contradicts config | Align prompt with frontmatter permissions |
| Agent too slow | Model too expensive | Use lighter model or create category |
| Agent too dumb | Model too cheap | Upgrade model or add skill injection |
