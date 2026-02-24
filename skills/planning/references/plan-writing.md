# Plan Writing

Sources: obra/superpowers methodology, Agile Estimating and Planning (Cohn), Shape Up (Basecamp)

Covers: plan document structure, zero-context principle, task specification format, completeness checklist, plan granularity levels.

## The Zero-Context Principle

The Zero-Context Principle is the core philosophy of modern agentic coding. It mandates that every plan and task be written as if the reader has no access to previous discussions, project goals, or tribal knowledge. This ensures that the plan remains executable even when context is lost or when tasks are delegated to fresh subagents.

### Core Tenets

1. Self-Containment: A task must contain 100% of the information required for its completion. If an agent needs to "scroll up" or "search history," the task is poorly specified.
2. No Assumptions: Never assume the reader has never seen the codebase. Provide paths, function names, and variable types explicitly.
3. Subagent Context Isolation: In multi-agent systems, subagents often start with a "blank slate." A zero-context task allows these agents to start work immediately without a lengthy context-loading phase.
4. Future-Proofing: Write for your future self. Three months from now, you will have zero context on why a specific architectural decision was made. The plan should serve as a historical record.
5. Taste and Intent: Do not assume the reader shares your "taste." Define exactly what "good" looks like for each task (e.g., "Use functional patterns, avoid classes").

### Why It Matters

* Drastic Reduction in Hallucination: Agents hallucinate when they lack specific information. Zero-context tasks provide the "ground truth" required for accurate code generation.
* Parallelization: When tasks are self-contained, they can be distributed across multiple agents or developers without coordination overhead.
* Auditability: A zero-context plan makes it easy to review why a specific change was made, as the intent is documented alongside the instructions.

## Plan Document Structure

A standard implementation plan follows a hierarchical structure designed for maximum clarity and ease of tracking.

### Required Header

Every plan file must begin with this standardized block. This metadata is essential for agents to understand the high-level constraints before diving into tasks.

```text
# [Feature Name] Implementation Plan

Goal: [One sentence describing the business or technical objective.]
Architecture: [2-3 sentences describing the technical approach and major components.]
Tech Stack: [Comma-separated list of key technologies, libraries, and frameworks.]
Estimated Effort: [XS/S/M/L/XL based on complexity and time.]
```

### Plan Lifecycle Sections

1. Research & Discovery: Initial tasks to explore the codebase or document requirements.
2. Foundation & Data: Setting up models, database schemas, and core utilities.
3. Core Logic & API: Implementing the business logic and external interfaces.
4. UI & Integration: Connecting the frontend to the backend or integrating external services.
5. Hardening & Cleanup: Refactoring, performance tuning, and final test coverage.

### Task Numbering and Dependencies

Use the `Phase.Task` format (e.g., 1.1, 1.2, 2.1). If a task has a specific prerequisite, mention it explicitly in the "Steps" section (e.g., "Prerequisite: Task 1.1 must be completed").

### Out of Scope

Explicitly listing what is NOT being done is as important as listing what IS. This prevents "feature creep" and keeps the agent focused on the primary goal.

### Tracking and Documentation Tables

Include these tables at the end of the document. They must be updated during execution.

#### Decisions Made
| Date | Decision | Rationale |
| :--- | :--- | :--- |
| YYYY-MM-DD | Use Redis for caching | Required for <100ms latency goal |
| YYYY-MM-DD | Store passwords as Argon2id | Industry standard for security |

#### Errors Encountered
| Task | Error | Resolution |
| :--- | :--- | :--- |
| 1.2 | Database migration failed | Updated schema to allow null on 'bio' field |
| 2.1 | API Timeout in CI | Increased Jest timeout to 10000ms |

## Task Specification Format

A task specification is the bridge between design and implementation. It must be so detailed that the execution becomes purely mechanical.

### Required Task Sections

1. Files: List every file involved. Use project-relative paths. Categorize by: Create, Modify, Delete, or Test.
2. Steps: Numbered actions. Each step should be actionable in under 5 minutes.
3. Code: Provide the complete code snippets. Never use placeholders like "// implement here".
4. Verification: The exact command and the specific output that proves success.
5. Commit: The exact git command with a conventional commit message.

### Example 1: Standard API Task

#### Task 2.1: Add GET /users/:id Endpoint
**Files:**
- Modify: `src/routes/userRoutes.ts`
- Modify: `src/controllers/userController.ts`
- Test: `tests/api/users.test.ts`

**Steps:**
1. Define the route in `userRoutes.ts`.
2. Implement the `getUserById` function in `userController.ts`.
3. Add a test case for fetching an existing user.
4. Add a test case for a non-existent user (404).

**Code:**
```typescript
// src/controllers/userController.ts
export const getUserById = async (req: Request, res: Response) => {
  const user = await db.user.findUnique({ where: { id: req.params.id } });
  if (!user) return res.status(404).json({ error: 'User not found' });
  return res.json(user);
};
```

**Verification:**
```bash
npm test tests/api/users.test.ts
```
Expected Output: `PASS tests/api/users.test.ts (2 tests passed)`.

**Commit:**
```bash
git add . && git commit -m "feat(users): add get user by id endpoint"
```

### Example 2: Complex Migration Task

#### Task 1.2: Add 'role' Column to User Table
**Files:**
- Create: `prisma/migrations/20240224_add_role_to_user/migration.sql`
- Modify: `prisma/schema.prisma`

**Steps:**
1. Update the Prisma schema with the `role` enum and field.
2. Generate the SQL migration file.
3. Run the migration against the local database.

**Code:**
```prisma
// prisma/schema.prisma
enum Role {
  USER
  ADMIN
}

model User {
  id    String @id @default(uuid())
  role  Role   @default(USER)
}
```

**Verification:**
```bash
npx prisma migrate dev --name add_role_to_user
```
Expected Output: `Your database is now in sync with your schema`.

**Commit:**
```bash
git add prisma/schema.prisma prisma/migrations && git commit -m "db: add role column to user table"
```

## Completeness Checklist

A plan is only as good as its weakest task. Use this table to audit your plan before execution.

| Criterion | Check | Description |
| :--- | :--- | :--- |
| Exact Paths | [ ] | Every file path is absolute or project-relative (no "the index file"). |
| No Placeholders | [ ] | Code blocks contain final, executable code, not descriptions. |
| Verification Commands | [ ] | Every task has a command that can be run in the terminal. |
| Expected Output | [ ] | The result of the verification command is explicitly stated. |
| Commit Steps | [ ] | Every task ends with a specific git commit command. |
| Atomicity | [ ] | Each task represents one logical unit of work (<30 mins). |
| Dependency Flow | [ ] | Tasks are ordered correctly (Foundation -> Logic -> UI). |
| Error Handling | [ ] | The plan addresses common failure points for complex tasks. |

## Plan Granularity Levels

Match the plan's detail level to the task's complexity and your familiarity with the domain.

| Level | When to Use | Deliverables |
| :--- | :--- | :--- |
| **Sketch** | Trivial tasks, brainstorming, or when working in a highly familiar environment. | High-level goal, list of files, rough bullet points for steps. No code. |
| **Standard** | 80% of development work. Standard features and bug fixes. | Full header, numbered tasks, key code snippets, verification, and commits. |
| **Detailed** | High-risk changes (migrations, security), unfamiliar libraries, or legacy code. | Comprehensive code for every file, multi-step verification, rollback steps. |

### Transitioning Between Levels
If a "Standard" task turns out to be more complex than expected during execution, pause and upgrade the plan to "Detailed" for the remaining steps. Never try to "wing it" when a plan proves insufficient.

## When to Write Plans vs Just Execute

Planning has a cost. Use this decision matrix to determine the appropriate investment.

| Signal | Complexity | Action |
| :--- | :--- | :--- |
| Single file, obvious fix, no logic change. | Low | Execute immediately. Record in git history only. |
| Familiar pattern, 1-3 files involved. | Medium | Use `todowrite` tool for a light, internal plan. |
| New feature, multi-file changes, or logic updates. | Medium-High | Create a `plan.md` file using the Standard format. |
| New library, legacy refactor, or critical system. | High | Create a Detailed `plan.md` and include a "Research" phase. |
| Architectural shift or breaking API changes. | Critical | Write a Design Doc first, then a Detailed Plan. |

## Plan Evolution and Maintenance

A plan is a living document, not a static artifact. It must evolve as the implementation reveals new complexities or constraints.

### The Maintenance Loop

1. Execute: Perform the task as specified in the plan.
2. Observe: If the task succeeds, mark it complete. If it fails or reveals new information, stop.
3. Patch: Update the `plan.md` immediately with the discovery. Do not keep "mental notes."
4. Re-plan: If the discovery affects future tasks, re-sequence them or update their specifications.

### Handling Discovery

Implementation often reveals that the "Architecture" or "Tech Stack" in the header was slightly wrong. When this happens, update the header first. This ensures the Zero-Context Principle is maintained for all remaining tasks.

## Collaborative Planning

When multiple agents or humans collaborate on a single plan, additional discipline is required to maintain consistency.

### Peer Review Criteria

* Verification Consistency: Do all verification commands follow the same style? (e.g., all use `curl` or all use a custom test script).
* Naming Alignment: Are file names and variable names consistent across different phases of the plan?
* Prerequisite Clarity: Are dependencies between tasks assigned to different executors explicitly documented?

### The "Subagent Hand-off" Test

Before assigning a task from the plan to a subagent, ask: "If I only gave the subagent the Header and this specific Task Specification, could they complete it perfectly?" If the answer is "No," the task requires more detail.

## Plan Review Checklist

Before hitting "Start," perform a final pass for these logical errors:

* Circular Dependencies: Task A needs B, but B needs A.
* Shadow Work: Tasks that change files not listed in the "Files" section.
* Missing Clean-up: Tasks that leave temporary files or debug logs behind.
* Test Gap: Features implemented without a corresponding test file update.
* Inconsistent Naming: Variables or files named differently across different tasks.
* Unrealistic Timing: Tasks that clearly take longer than the 30-minute atomicity goal.

## Anti-Patterns

| Don't | Do Instead |
| :--- | :--- |
| Write "Update the controller logic." | Specify exactly which lines or functions to change. |
| Use "See previous task for details." | Duplicate relevant info or link directly to the task ID. |
| Assume the `.env` is correctly configured. | Include a task to verify or update environment variables. |
| Write tasks that modify 10+ files. | Break into smaller, atomic tasks focused on one subsystem. |
| Forget the `git add` step in the commit command. | Always include `git add [files]` or `git add .`. |
| Use vague verification like "Check if it works." | Provide a specific `curl`, `npm test`, or `ls` command. |
| Ignore "Out of Scope" items. | Explicitly list what you are ignoring to avoid distractions. |
| Mix refactoring with feature development. | Create separate phases for refactoring and new features. |
| Omit the "Tech Stack" from the header. | List every library you intend to use to avoid surprises later. |
| Write plans in the chat instead of a file. | Persistent files (e.g., `plan.md`) are easier to track and update. |
| Leave "placeholder" tasks for later. | Every task in an active phase must be fully specified. |
| Use relative paths like `../file.js`. | Use project-root-relative paths like `src/utils/file.js`. |
