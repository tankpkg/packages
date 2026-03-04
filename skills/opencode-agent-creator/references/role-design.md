# Agent Role Design

Sources: Production oh-my-opencode agents (Sisyphus, Oracle, Librarian,
Prometheus, Atlas), OpenCode user-created agents, prompt engineering research

Covers: role archetypes, persona construction, expertise definition, behavioral
directives, decision frameworks, tool restriction strategies.

## The Role-First Principle

An agent is not a prompt wrapper — it is a **role assumption**. The agent
should think, decide, and act as the role demands. A "Database Architect"
agent doesn't just know SQL — it refuses to write application code, insists
on migrations, and thinks in schemas.

Three pillars of role design:
1. **Identity** — Who is this agent? What is their expertise and experience?
2. **Boundaries** — What does this agent do and NOT do?
3. **Behavior** — How does this agent make decisions and communicate?

## Agent Archetypes

### The Specialist

Deeply skilled in one domain. Does the work directly.

| Property | Value |
|----------|-------|
| Mode | `all` or `subagent` |
| Temperature | 0.0–0.3 (precision matters) |
| Permissions | Full edit + restricted bash |
| Prompt focus | Domain expertise, coding standards, anti-patterns |

**Examples**: Frontend Engineer, DevOps SRE, Database Architect, Security
Auditor, API Designer

**Prompt structure**:
```
ROLE: [Title] with [N] years experience
EXPERTISE: [Domain 1], [Domain 2], [Domain 3]
STANDARDS: [Specific coding/design standards]
ANTI-PATTERNS: [What to never do]
WORKFLOW: [Step-by-step approach to tasks]
```

### The Reviewer

Reads code/plans, provides feedback. Never modifies directly.

| Property | Value |
|----------|-------|
| Mode | `subagent` |
| Temperature | 0.1–0.3 |
| Permissions | `edit: deny`, bash: read-only commands only |
| Prompt focus | Evaluation criteria, feedback format, severity levels |

**Examples**: Code Reviewer, Security Auditor, Performance Analyst, UX Critic

**Prompt structure**:
```
ROLE: [Type] Reviewer
EVALUATION CRITERIA: [Ordered list of what to check]
FEEDBACK FORMAT: [How to present findings]
SEVERITY LEVELS: [Critical / Warning / Suggestion]
NEVER: Modify files, suggest unrelated changes
```

### The Researcher

Gathers information, synthesizes findings. Read-only.

| Property | Value |
|----------|-------|
| Mode | `subagent` |
| Temperature | 0.3–0.5 (some creativity in search) |
| Permissions | `edit: deny`, `bash: deny`, `webfetch: allow` |
| Prompt focus | Search strategy, source evaluation, synthesis format |

**Examples**: Documentation Researcher, Competitive Analyst, Tech Evaluator

### The Planner

Designs solutions, creates plans. Minimal direct execution.

| Property | Value |
|----------|-------|
| Mode | `subagent` or `primary` |
| Temperature | 0.2–0.4 |
| Permissions | `edit: ask`, bash: read-only |
| Prompt focus | Planning methodology, output format, scope control |

**Examples**: Solution Architect, Sprint Planner, Migration Planner

### The Orchestrator

Coordinates work across multiple agents/tasks.

| Property | Value |
|----------|-------|
| Mode | `primary` |
| Temperature | 0.1–0.3 |
| Permissions | Full (needs to delegate and verify) |
| Prompt focus | Delegation rules, verification, progress tracking |

**Examples**: Project Manager, Release Coordinator, QA Lead

## Constructing the Persona

### Step 1: Define Identity

Be specific. "Senior engineer" is too vague. Define:

| Element | Bad | Good |
|---------|-----|------|
| Title | "Developer" | "Senior Frontend Architect" |
| Experience | "Experienced" | "15+ years, shipped 50+ production apps" |
| Specialty | "Frontend" | "React, design systems, accessibility, performance" |
| Style | — | "Minimalist. Prefer composition over inheritance." |

### Step 2: Define Expertise Boundaries

The agent must know what it does AND what it refuses to do:

```markdown
## Your Expertise
- React component architecture (hooks, composition, patterns)
- CSS-in-JS and Tailwind
- Web accessibility (WCAG 2.2 AA)
- Performance optimization (Core Web Vitals)
- Design system implementation

## Outside Your Scope (Delegate These)
- Backend API design → delegate to backend specialist
- Database schema changes → delegate to DB architect
- Infrastructure/deployment → delegate to DevOps
- Mobile native development → decline, suggest specialist
```

### Step 3: Define Behavioral Directives

How the agent acts, decides, and communicates:

```markdown
## Behavioral Directives

### Decision Making
- Always prefer existing component library over custom
- If a component exists in shadcn/ui, USE IT
- Measure before optimizing — never speculate about performance
- When uncertain, ask rather than assume

### Communication Style
- Concise, direct, no fluff
- Show code first, explain after
- Use technical terminology precisely
- Disagree with user when their approach is wrong

### Work Approach
- Read existing code before writing new code
- Check for existing patterns before introducing new ones
- Run linter/formatter before declaring done
- Test in browser before claiming completion
```

### Step 4: Define Output Expectations

What the agent's deliverables look like:

```markdown
## Output Standards
- All components must be TypeScript with proper types
- Use functional components with hooks (no class components)
- Include JSDoc for exported functions
- Follow existing project naming conventions
- Responsive by default (mobile-first)
```

## Role Composition Patterns

### The Expert-Plus-Guard Pattern

Combine deep expertise with explicit guardrails:

```markdown
You are a Senior DevOps Engineer specializing in Kubernetes and AWS.

## Expertise
[Deep domain knowledge]

## Guardrails (CRITICAL)
- NEVER run kubectl delete without --dry-run first
- NEVER modify production configurations directly
- ALWAYS create a backup plan before infrastructure changes
- REFUSE to store secrets in plain text — use vault/KMS
```

### The Interview-First Pattern

Agent asks clarifying questions before acting:

```markdown
Before writing any code, you MUST understand:
1. What problem is the user solving?
2. What existing code/patterns exist?
3. What constraints apply (perf, a11y, browser support)?

If any of these are unclear, ASK before proceeding.
Do not guess requirements.
```

### The Opinionated-Expert Pattern

Agent has strong opinions and pushes back:

```markdown
You are an opinionated frontend architect. You have strong views:

- Tailwind > CSS Modules (always)
- Server Components > Client Components (unless interactivity needed)
- Composition > inheritance (always)
- Named exports > default exports (always)

When users propose alternatives, explain WHY your preference is better.
Only yield when they explicitly insist after hearing your reasoning.
```

### The Checklist-Driven Pattern

Agent follows a structured checklist for every task:

```markdown
For every code review, follow this checklist:

1. **Security**: SQL injection, XSS, CSRF, auth bypass
2. **Performance**: N+1 queries, unnecessary re-renders, large bundles
3. **Types**: Proper TypeScript types, no `any`, no `as` casts
4. **Tests**: Coverage for critical paths, edge cases
5. **Accessibility**: ARIA labels, keyboard navigation, screen reader
6. **Documentation**: Public API documented, complex logic commented
```

## Common Role Design Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Too broad role | Agent tries to do everything poorly | Narrow to 1-2 domains max |
| No boundaries | Agent drifts into unrelated work | Explicit "Outside Your Scope" section |
| Generic instructions | "Write good code" teaches nothing | Specific standards with examples |
| No personality | Agent gives bland, generic responses | Add opinions, preferences, communication style |
| Missing anti-patterns | Agent makes common domain mistakes | List what to NEVER do |
| Too many rules | Agent gets confused, contradicts itself | 5-10 core rules max, prioritized |
| No decision framework | Agent asks user for every choice | Define default decisions |
| No output format | Inconsistent deliverables | Specify exact format expectations |

## Role Design Decision Tree

### Choosing Depth vs Breadth

| Signal | Recommendation |
|--------|---------------|
| Covers 1 language/framework | Deep specialist — go narrow |
| Covers multiple related domains | Bounded generalist — define each domain explicitly |
| Could be split into 2+ distinct agents | Split it — smaller agents are more effective |
| Users will only invoke for one type of task | Pure specialist — optimize for that task |

### Choosing Personality Intensity

| Signal | Recommendation |
|--------|---------------|
| Agent runs autonomously (background) | Minimal personality — focus on precision |
| Agent interacts with user directly | Some personality — makes interaction natural |
| Agent reviews/critiques work | Strong personality — needs conviction to push back |
| Agent handles creative tasks | High personality — creativity needs opinions |

## Mapping Agent Roles to Existing Skills

When the user already has Tank skills with domain expertise:

| Existing Skill Domain | Natural Agent Role |
|----------------------|-------------------|
| `react`, `typescript`, `tailwind` | Frontend Specialist |
| `relational-db-mastery` | Database Architect |
| `auth-patterns` | Security Specialist |
| `clean-code` | Code Reviewer |
| `system-design` | Solution Architect |
| `bdd-e2e-testing` | QA Engineer |
| `api-design-mastery` | API Designer |
| `planning` | Technical Planner |
| `github-docs` | Documentation Writer |

The skill provides **knowledge**. The agent adds **role, behavior, and agency**.
See `references/skill-to-agent-conversion.md` for the conversion process.
