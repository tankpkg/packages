# Prompt Patterns for Code Generation

Sources: vibecoding.app (Prompt Engineering Guide, 2026), Anthropic prompt engineering documentation, chand1012 (Agentic Coding Best Practices, 2025), dev.to practitioner guides (2025-2026), Waseem et al. (Vibe Coding in Practice, arXiv 2512.11922)

Covers: prompt engineering techniques for AI code generation, the Research-Plan-Implement framework, iterative prompting strategies, role assignment, context referencing, and anti-patterns.

## The Fundamental Shift

In vibe coding, prompts replace syntax. The quality of generated code correlates directly with prompt quality. A vague prompt produces generic, assumption-laden code. A specific prompt produces code aligned with intent.

The shift from traditional prompt engineering to code-generation prompting:

| Traditional Prompting | Code Generation Prompting |
|----------------------|--------------------------|
| Optimize for text quality | Optimize for correctness and consistency |
| Single-turn completions | Multi-turn iterative refinement |
| Context is the conversation | Context is the codebase + conversation |
| Success = good answer | Success = working, reviewed, tested code |

## The Five Prompt Principles

### 1. Context First

Most AI code generation failures happen because the AI lacks context about the codebase.

```
Bad:  "Fix the login bug."
Good: "@auth.ts @login-form.tsx Fix the bug where the user session
       doesn't persist after page refresh. The session token is set
       in the cookie but not read back on the server side."
```

Reference specific files with @ mentions. Name the files, the functions, the data shapes. The more precise the context, the more precise the output.

### 2. Describe Why and What, Not How

State the goal and let the AI choose implementation. It may find a better approach.

```
Bad:  "Write a for loop that filters the array and maps it to objects."
Good: "Filter active users and transform them into UserSummary objects
       for the dashboard sidebar. Should be performant for 10k+ users."
```

Include constraints (performance, UX feel, compatibility) rather than prescribing implementation details.

### 3. Chain of Thought for Complex Tasks

For multi-step features, ask the AI to plan before implementing.

```
"I want to add real-time notifications using WebSockets.
First, analyze the existing codebase:
- How do we currently handle server-sent events?
- Where should the WebSocket server live?
- What existing patterns should we follow?
Summarize your findings before proposing any code."
```

This surfaces assumptions and misunderstandings before they become hundreds of lines of wrong code.

### 4. Role Assignment

Assign a specific role to constrain the AI's perspective.

```
"Act as a senior backend engineer focused on API security.
Review this authentication endpoint and identify vulnerabilities."
```

Effective roles for code generation:

| Role | Use For |
|------|---------|
| Senior [framework] engineer | Architecture decisions, code review |
| Performance engineer | Optimization, profiling analysis |
| Security engineer | Vulnerability review, hardening |
| QA engineer | Test generation, edge case identification |
| DevOps engineer | CI/CD, deployment, infrastructure |

### 5. Iterate in Small Steps

One feature per prompt. Build incrementally.

```
Step 1: "Scaffold the basic database schema for a project management app."
Step 2: "Add the API endpoints for CRUD operations on projects."
Step 3: "Create the React components for the project list view."
Step 4: "Add form validation to the create project form."
Step 5: "Write integration tests for the project API endpoints."
```

Each step is reviewable, revertible, and builds on verified output from the previous step.

## The Research-Plan-Implement Framework

This three-phase framework catches mistakes early, when they are cheap to fix.

### Phase 1: Research

Have the AI explore the codebase before writing code.

```
"I want to add a payment system with Stripe. Before implementing:
1. Analyze our existing user and subscription models
2. Check how we currently handle webhooks
3. Review our error handling patterns
4. Identify any existing Stripe-related code
Summarize findings — no code yet."
```

Cost of catching a misunderstanding at this phase: ~30 seconds to clarify.

### Phase 2: Plan

Request a step-by-step implementation plan.

```
"Based on your analysis, create an implementation plan:
1. List every file that needs to be created or modified
2. Describe the changes for each file
3. Identify dependencies and ordering constraints
4. Note potential risks or edge cases
Don't write code — just the plan."
```

Review the plan. Does it match your mental model? Did it miss anything? Correct misalignments before code exists.

Cost of catching a misunderstanding at this phase: ~2 minutes to adjust.

### Phase 3: Implement

Execute the approved plan step by step.

```
"The plan looks good. Implement step 1: create the Stripe webhook
handler in /app/api/webhooks/stripe/route.ts following our existing
webhook patterns in /app/api/webhooks/."
```

If something diverges from the plan, stop and course-correct immediately.

Cost of catching a misunderstanding at this phase: ~20 minutes to debug.

### When to Use RPI

| Complexity | Approach |
|-----------|----------|
| Trivial (add a button, fix a typo) | Direct prompt |
| Simple (new page, basic CRUD) | Plan + implement |
| Medium (new feature touching 5+ files) | Full RPI |
| Complex (new system, migration, refactor) | Full RPI with checkpoints |

## Prompt Templates

### New Feature

```
Feature: [name]
User story: As a [role], I want to [action] so that [benefit].
Data model: [describe entities and relationships]
UI: [describe the interface]
Constraints: [performance, security, compatibility]
Reference: @[existing-similar-file] for patterns
```

### Bug Fix

```
Bug: [description of incorrect behavior]
Expected: [what should happen]
Actual: [what currently happens]
Reproduction: [steps to reproduce]
Files: @[file1] @[file2]
```

### Refactor

```
Goal: [what you want to improve]
Current state: @[files to refactor]
Target state: [describe the desired architecture]
Constraints: [must maintain backward compatibility, etc.]
Approach: [incremental vs. big bang]
```

### Code Review

```
Review @[file] for:
1. Security vulnerabilities (injection, auth bypass, data exposure)
2. Error handling gaps (unhandled promises, missing try/catch)
3. Performance issues (N+1 queries, unnecessary re-renders)
4. Naming and readability
5. Test coverage gaps
Prioritize by severity.
```

## Anti-Patterns

### Vague Prompts

```
Bad:  "Build me a dashboard."
Good: "Build a dashboard for a freelance designer showing monthly
       revenue (bar chart), active projects by client (table),
       and pending invoices sorted by due date (list with status badges).
       Use the existing ChartJS setup in /lib/charts.ts."
```

### Monolithic Prompts

A 500-word prompt describing an entire application produces uncontrollable output. Features get simplified, pages get merged, and intent drifts.

Break into sequential prompts of increasing specificity.

### Missing Data Model Context

```
Bad:  "Build a project management tool."
Good: "Build a project management tool. Data model:
       - Users have projects (many-to-many via team membership)
       - Projects have tasks
       - Tasks: title, description, deadline, status (todo/progress/done),
         assigned user (FK to users)
       - Users can be members of multiple projects"
```

### Ignoring Conversation Drift

After 20-30 messages, the AI's context window pushes out earlier decisions. It starts contradicting itself.

**Prevention:**
- Start fresh conversations for major new features
- Reference previous decisions explicitly: "Keep the existing auth system. Add a new analytics page..."
- Periodically restate key constraints
- Use rules files for persistent context instead of relying on conversation history

### Over-Specifying Implementation

```
Bad:  "Write a for loop from index 0 to array.length, and inside the
       loop create a new object with..."
Good: "Transform this array of raw API responses into UserCard props.
       Handle null avatars with a fallback initial."
```

Prescribing implementation line-by-line defeats the purpose. State the transformation and constraints; let the AI choose the approach.

## Measuring Prompt Effectiveness

| Signal | Good Prompts | Bad Prompts |
|--------|-------------|-------------|
| First-generation accuracy | Code works with minor edits | Code needs major rewrite |
| Iteration count | 1-3 rounds per feature | 5+ rounds of "no, I meant..." |
| AI asking clarifying questions | Rare — prompt was clear | Frequent — prompt was ambiguous |
| Consistency across sessions | Same conventions every time | Different patterns each session |
| Review burden | Quick scan, minor fixes | Line-by-line inspection needed |
