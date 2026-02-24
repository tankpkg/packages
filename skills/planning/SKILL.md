---
name: planning
description: |
  Comprehensive planning methodology for complex software tasks. Covers task
  decomposition (WBS, micro-tasks), plan writing (zero-context specs), plan
  execution (batched with checkpoints), prioritization (RICE, MoSCoW, ICE),
  estimation, risk assessment, and persistent context management.

  Synthesized from: Shape Up (Basecamp), Agile Estimating and Planning (Cohn),
  obra/superpowers planning methodology, ReAct/Plan-and-Solve AI patterns.

  Trigger phrases: "plan", "planning", "break down", "decompose", "task
  breakdown", "prioritize", "estimate", "risk assessment", "project plan",
  "implementation plan", "work breakdown", "what order", "dependencies",
  "scope", "how to approach", "complex task", "multi-step"
---

# Planning

## Core Philosophy

1. **Plan before code** — Never start a complex task without a written plan. Non-negotiable.
2. **Zero-context plans** — Write as if the reader has no project knowledge. Exact file paths, complete code, expected outputs.
3. **Micro-task granularity** — Each step is 2-5 minutes of work. If you cannot estimate it, decompose further.
4. **Filesystem is memory** — Context window is volatile RAM. Anything important goes to disk immediately.
5. **Adapt, don't abandon** — Plans change when reality hits. Replan when blocked, never restart from scratch.

## Quick-Start: Which Planning Level?

| Task Complexity | Planning Level | Action |
|-----------------|---------------|--------|
| Single file, known location | None | Execute directly |
| 2-3 files, clear approach | Light | Mental plan, use TodoWrite |
| 4+ files or uncertain approach | Standard | Create `task_plan.md` with phases |
| Large feature or unfamiliar domain | Full | Brainstorm → Design doc → Implementation plan |
| Multi-day or multi-person effort | Comprehensive | Full plan + estimation + risk assessment |

## The Planning Workflow

### Phase 1: Understand

1. Parse the request — what is actually being asked?
2. Identify constraints — time, dependencies, existing patterns, risks
3. Clarify ambiguities — ask ONE focused question if unclear
4. Explore codebase — understand existing patterns before planning

→ For context management techniques: See `@references/context-management.md`

### Phase 2: Decompose

1. Break into major components (top-down)
2. Decompose each component into tasks
3. Decompose each task into steps (2-5 minutes each)
4. Map dependencies — what must happen first?
5. Flag unknowns — mark tasks requiring research

→ For decomposition techniques: See `@references/task-decomposition.md`

### Phase 3: Prioritize

1. Identify the critical path (longest dependency chain)
2. Separate must-have from nice-to-have
3. Order by: dependencies first, then priority, then risk
4. For competing priorities, apply a scoring framework

→ For prioritization frameworks: See `@references/prioritization.md`

### Phase 4: Write the Plan

1. Create plan document with header (goal, architecture, tech stack)
2. Write each task with: files to touch, steps, verification, commit message
3. Include complete code snippets — never write "add validation logic"
4. Specify exact commands with expected outputs
5. Save plan to `task_plan.md` in project root

→ For plan document structure: See `@references/plan-writing.md`
→ For plan template: Copy from `@assets/task-plan-template.md`

### Phase 5: Execute

1. Execute in batches of 3 tasks
2. Verify after each task (run tests, check output)
3. Report progress between batches
4. Commit after each task passes verification

→ For execution workflow: See `@references/plan-execution.md`

### Phase 6: Adapt

1. After each batch, reassess the remaining plan
2. If blocked: try an alternative approach, never repeat the same failing action
3. After 3 failures on same task: stop, replan, or escalate
4. Update plan document with actuals vs estimates

## Decision Trees

### When to Replan vs Push Forward

| Signal | Action |
|--------|--------|
| Task taking 2x estimated effort | Pause. Reassess approach |
| New dependency discovered | Update plan, adjust ordering |
| Approach fundamentally flawed | Replan from Phase 2 |
| 3 consecutive failures on same task | Stop. Escalate to user |
| Scope creep detected | Flag it. Get user approval before expanding |
| New information changes assumptions | Update plan, continue |

### Estimation Quick Reference

| Size | Effort | Example |
|------|--------|---------|
| XS | < 30 min | Fix a typo, update config |
| S | 30 min - 2 hr | Add a simple endpoint |
| M | 2 - 8 hr | New feature with tests |
| L | 1 - 3 days | Multi-component feature |
| XL | 3+ days | Architecture change |

→ For detailed estimation: See `@references/estimation-and-risk.md`

## Critical Rules

### 1. The 2-Action Rule

> After every 2 tool operations, save key findings to disk.

Prevents information loss from context window overflow. Especially critical after viewing images, PDFs, or browser content.

### 2. Never Repeat Failures

```
if action_failed:
    next_action != same_action
```

Track what you tried. Mutate the approach each time.

### 3. Read Before Decide

Before major decisions, re-read the plan file. This refreshes goals in the attention window and prevents drift.

### 4. Log ALL Errors

Every error goes in the plan file with the attempted resolution. Builds knowledge and prevents repetition.

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Start coding without a plan | Create plan first, even a minimal one |
| Write vague task descriptions | Specify exact files, code, commands, expected output |
| Estimate in hours | Use relative sizing (XS/S/M/L/XL) or story points |
| Plan everything upfront | Plan one phase ahead in detail, sketch the rest |
| Skip verification steps | Verify after every task before moving on |
| Repeat failed approaches | Track attempts, change strategy each time |
| Keep plan only in context window | Write to `task_plan.md` immediately |
| Ignore scope creep | Flag every addition, get explicit approval |

## Integration with Other Skills

| Situation | Skill to Use |
|-----------|-------------|
| Writing tests for planned tasks | `tdd-workflow` |
| Debugging a failing task | `systematic-debugging` |
| Committing completed tasks | `git-master` |

## AI Planning Patterns

For AI-specific planning strategies (ReAct, Chain-of-Thought, Plan-and-Solve, Tree-of-Thoughts):

→ See `@references/ai-planning-patterns.md`

## Reference Files

| File | When to Load |
|------|-------------|
| @references/task-decomposition.md | Breaking complex work into actionable micro-tasks |
| @references/plan-writing.md | Creating plan documents with proper structure and specs |
| @references/plan-execution.md | Executing plans with batching, checkpoints, and review |
| @references/prioritization.md | Deciding what to do first (RICE, MoSCoW, ICE, Eisenhower) |
| @references/estimation-and-risk.md | Estimating effort and assessing risks |
| @references/context-management.md | Managing context with filesystem as working memory |
| @references/ai-planning-patterns.md | AI-specific planning strategies and reasoning patterns |

## Templates

| Template | Purpose |
|----------|---------|
| @assets/task-plan-template.md | Plan document with phases, tasks, and verification |
| @assets/findings-template.md | Research findings storage |
| @assets/progress-template.md | Session progress logging |
