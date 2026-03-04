# Agent Prompt Engineering

Sources: Production oh-my-opencode agents analysis, OpenCode agent system,
Anthropic prompt engineering guidelines, real agent prompts from
smart-programmer.md and web-productivity-assistant.md

Covers: system prompt structure, sections anatomy, effective directives,
tool restriction patterns, prompt anti-patterns, testing strategies.

## System Prompt Structure

An agent's system prompt is the body of the markdown file (after frontmatter).
It defines WHO the agent is and HOW it behaves.

### Recommended Section Order

```markdown
# ROLE DEFINITION
One paragraph: title, experience, specialty.

## Your Expertise
Bulleted list of domain capabilities.

## Outside Your Scope
What you refuse to do. Critical for role boundaries.

## Operational Directives
How you work: approach, standards, decision rules.

## Communication Style
How you interact with the user.

## Output Format
What your deliverables look like.

## Rules (CRITICAL)
Hard constraints. Things you must ALWAYS or NEVER do.
```

Not every agent needs every section. Minimal agents can be 10-20 lines.
Complex specialists might be 80-120 lines. Never exceed 150 lines — beyond
that, the agent loses focus.

## Writing Effective Role Definitions

### The Opening Paragraph

The first lines set the agent's identity. Be specific and authoritative.

**Weak**:
```
You are a helpful coding assistant.
```

**Strong**:
```
You are a Senior DevOps SRE with 12+ years shipping production
infrastructure. You specialize in Kubernetes, AWS, Terraform, and
observability. You think in systems — every change has blast radius.
```

**Strongest** (with personality):
```
You are an opinionated Senior Frontend Architect. 15+ years.
You've shipped 50+ production apps and have strong views on
component architecture, performance, and developer experience.
You write code that other engineers enjoy reading.
```

### Expertise Lists

Use bulleted lists. Be specific enough that the agent knows its boundaries:

```markdown
## Your Expertise
- Kubernetes cluster management (EKS, GKE, self-hosted)
- Terraform infrastructure-as-code (modules, state management)
- CI/CD pipelines (GitHub Actions, ArgoCD, Flux)
- Observability stack (Prometheus, Grafana, Loki, Tempo)
- Incident response and post-mortem processes
- Cost optimization for cloud infrastructure
```

### Boundary Definitions

Equally important as expertise. Prevents role drift:

```markdown
## Outside Your Scope (Delegate These)
- Application code changes → developer should handle
- Database schema design → database architect
- Frontend work → frontend specialist
- Security audits → security specialist
- Cost decisions beyond $1000/month → need human approval
```

## Directive Patterns

### Imperative Directives (Do This)

Direct commands the agent must follow:

```markdown
## Operational Directives
1. Read existing infrastructure code before proposing changes
2. Always use `terraform plan` before `terraform apply`
3. Create rollback plans for every infrastructure change
4. Tag all resources with team, environment, and cost-center
5. Use modules for repeated patterns — never copy-paste
```

### Constraint Directives (Never Do This)

Hard limits that prevent dangerous actions:

```markdown
## Rules (CRITICAL — NEVER VIOLATE)
- NEVER run destructive commands without `--dry-run` first
- NEVER store secrets in plain text, environment variables, or git
- NEVER modify production directly — always through IaC
- NEVER skip the approval step for infrastructure changes
- NEVER use `latest` tags in production — pin all versions
```

### Conditional Directives (If X Then Y)

Decision rules for common situations:

```markdown
## Decision Framework
- If task involves production → require explicit user confirmation
- If error occurs during apply → immediately stop and show state
- If cost estimate exceeds $100/month → warn user before proceeding
- If existing module covers the need → use it, don't create new
- If unsure about blast radius → ask before acting
```

### Priority Directives (Ranking)

When rules conflict, which wins:

```markdown
## Priority Order (highest first)
1. Safety — never break production
2. Correctness — code must work
3. Maintainability — others must understand it
4. Performance — optimize when measured
5. Elegance — nice to have, not required
```

## Tool Restriction Patterns

Tools available to agents depend on permission config in frontmatter.
The prompt should reinforce these restrictions with behavioral instructions.

### Read-Only Agent Pattern

```yaml
# Frontmatter
permission:
  edit: deny
  bash:
    "*": deny
    "git log *": allow
    "git diff *": allow
    "git show *": allow
```
```markdown
# Prompt reinforcement
You are a read-only agent. You CANNOT and SHOULD NOT modify any files.
Your job is to analyze, review, and provide feedback.

If the user asks you to make changes, respond with specific instructions
they can give to a coding agent instead.
```

### Scoped Executor Pattern

```yaml
# Frontmatter
permission:
  edit: ask
  bash:
    "*": ask
    "npm test *": allow
    "npm run lint *": allow
    "npm run build": allow
```
```markdown
# Prompt reinforcement
You can freely run tests, linting, and builds. For any other commands
or file modifications, the system will ask the user for confirmation.
Plan your work to minimize permission prompts.
```

### Delegator Pattern

```yaml
# Frontmatter
permission:
  edit: deny
  bash:
    "*": deny
tools:
  task: true
```
```markdown
# Prompt reinforcement
You do NOT write code yourself. You analyze requirements and delegate
to specialist agents using the task tool. Your job is to:
1. Understand what needs to be done
2. Break it into delegatable chunks
3. Pick the right specialist for each chunk
4. Verify results
```

## Prompt Length Guidelines

| Agent Complexity | Prompt Lines | When |
|-----------------|-------------|------|
| Minimal | 10-20 | Simple, focused task (reviewer, formatter) |
| Standard | 30-60 | Typical specialist agent |
| Complex | 60-100 | Multi-domain or highly opinionated agent |
| Maximum | 100-150 | Orchestrator with complex rules |

**Beyond 150 lines**: Split into multiple agents or use skills for domain
knowledge injection.

## Advanced Prompt Techniques

### Protocol Triggers

Define special keywords that change behavior:

```markdown
## The "ULTRATHINK" Protocol
When the user says "ULTRATHINK":
- Suspend brevity mode
- Engage exhaustive multi-dimensional analysis
- Consider: psychological, technical, accessibility, scalability angles
- Never use surface-level logic
```

### Format Switching

Different output formats for different contexts:

```markdown
## Response Format

**Normal mode**: Code first, 1-sentence rationale.

**When user asks "explain"**: Detailed reasoning chain, then code.

**When reviewing**: Severity-tagged feedback list:
- 🔴 CRITICAL: Must fix before merge
- 🟡 WARNING: Should fix, not blocking
- 🟢 SUGGESTION: Optional improvement
```

### Self-Verification Instructions

Force the agent to check its own work:

```markdown
## Before Responding
1. Re-read the user's request — did you address ALL parts?
2. Check code compiles (no obvious syntax errors)
3. Verify types are correct (no `any` or unsafe casts)
4. Confirm imports exist (no phantom imports)
5. If you modified a function, verify all callers still work
```

## Common Prompt Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| "Be helpful and thorough" | Vacuous — agent already tries to be | Specific directives |
| "Write clean code" | Too vague — means nothing | "Follow Airbnb style guide" |
| Repeating tool descriptions | Wastes tokens, agent knows its tools | Focus on WHEN to use tools |
| Explaining what agent IS | Identity section, not explanation | "You are X" not "You are an AI that..." |
| Multiple competing personas | Agent can't decide who it is | One clear identity |
| Long examples in prompt | Bloats prompt, reduces focus | Move to description's `<example>` tags |
| No anti-patterns listed | Agent makes domain-specific mistakes | Add "NEVER" section |
| Instructions for every case | Prompt becomes rigid, can't adapt | Principles over procedures |

## Testing Agent Prompts

### Quick Validation

After creating an agent, test with these patterns:

1. **In-domain request**: "Do [core task]" — verify competent response
2. **Out-of-scope request**: "Do [thing outside boundaries]" — verify refusal
3. **Ambiguous request**: "Help with [vague thing]" — verify asks for clarity
4. **Push-back test**: "Just do [bad practice]" — verify the agent objects
5. **Multi-step test**: "Do [complex thing]" — verify structured approach

### Iteration Cycle

```
Write prompt → Test 5 patterns → Note failures →
Adjust specific section → Retest failures → Deploy
```

Common first-iteration fixes:
- Add missing boundary (agent did something it shouldn't)
- Strengthen a directive (agent ignored a soft suggestion)
- Add decision rule (agent asked user for something it should decide)
- Remove verbose section (agent was overly cautious/wordy)
