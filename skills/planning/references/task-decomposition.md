# Task Decomposition

Sources: Shape Up (Basecamp), Agile Estimating and Planning (Cohn), obra/superpowers methodology, PMBOK WBS standard

Covers: work breakdown structures, micro-task granularity, dependency mapping, decomposition decision trees, Shape Up shaping.

Decomposition is the process of breaking down a complex project or feature into smaller, manageable components until the work is defined at a level of detail that allows for confident execution and verification. For AI agents, this level of detail must be significantly higher than traditional human-to-human project management to account for context window limits and the need for frequent state verification.

## Work Breakdown Structure (WBS)

The Work Breakdown Structure is a hierarchical decomposition of the total scope of work to be carried out by the project team. It serves as the foundation for planning, execution, and control.

### The 100% Rule and MECE Principle
The WBS must include 100% of the work defined by the project scope. This is often guided by the MECE principle: Mutually Exclusive, Collectively Exhaustive.
- Mutually Exclusive: No overlap between work packages. If a task is in one branch, it should not appear in another. This prevents double-counting and confusion.
- Collectively Exhaustive: The sum of the children must equal the parent. No work is "hidden" or "implied." If a task is not in the WBS, it is not in the project.

### Decomposition Levels
1. Project: The highest level representing the entire effort (e.g., E-commerce Checkout).
2. Deliverables: Major components or milestones (e.g., Cart Logic, Payment Integration).
3. Sub-deliverables: Intermediate components (e.g., Stripe API Implementation).
4. Work Packages: The lowest level where work can be managed (e.g., Handle Stripe Webhook).

### Stopping Criteria: Traditional vs AI Agent
Traditional project management uses the 8-80 hour rule. For AI agents, the stopping criterion is "The Step Level." A task is decomposed enough when it represents a single, atomic change to the codebase that can be verified with a single command.

| Metric | Traditional WBS | AI Agent WBS |
|---|---|---|
| Granularity | 8 - 80 hours | 2 - 5 minutes |
| Objective | Resource allocation | Atomic execution and verification |
| Verification | Weekly status | Step-by-step terminal output |
| Context | Human memory / documentation | Short-term context window |
| Change Unit | Feature / User Story | Commit / File change |

### Detailed Example WBS (Checkout Flow)
1. E-commerce Checkout Flow (Project)
   1.1. Order Processing (Deliverable)
      1.1.1. Cart Validation (Sub-deliverable)
         1.1.1.1. Check stock availability (Work Package)
         1.1.1.2. Calculate taxes and shipping (Work Package)
      1.1.2. Database Persistence (Sub-deliverable)
         1.1.2.1. Create Order record (Work Package)
         1.1.2.2. Create OrderItems records (Work Package)
   1.2. Payment Integration (Deliverable)
      1.2.1. Stripe Integration (Sub-deliverable)
         1.2.1.1. Create PaymentIntent (Work Package)
         1.2.1.2. Handle success/failure callbacks (Work Package)
   1.3. User Notifications (Deliverable)
      1.3.1. Email Confirmation (Sub-deliverable)
         1.3.1.1. Generate email template (Work Package)
         1.3.1.2. Send via SMTP/Mailgun (Work Package)

## Micro-Task Granularity (obra/superpowers)

Micro-task granularity ensures that the agent never loses its way during execution. It transforms a "plan" into a "checklist of certainties."

### The 2-5 Minute Action Rule
Every step in an execution plan should take 2-5 minutes. If a task takes longer, it is likely a "Compound Task" that hides complexity or potential failure points. Breaking these down ensures that the "Blast Radius" of a failure is minimal.

### Context Window Budgeting
Each micro-task must be small enough to fit within a single turn's context. 
- Large task: "Implement the entire checkout controller" (Risks: 2000+ lines of context, high hallucination risk).
- Micro-task: "Add the `validateStock` method to CheckoutController" (Low risk: 50 lines of context, high accuracy).

### Verifiable Outcomes
A micro-task is only complete when its outcome is verified. 
- Bad: "Fix the bug in the login flow."
- Good: "Update line 42 of login.js to use strict equality, then run `npm test login` and verify 100% pass rate."

### Specification Format for Execution
For every micro-task in the final plan, specify:
1. Target File: The absolute path of the file to modify.
2. Context: The specific function or line range.
3. Action: The precise change (e.g., "Add parameter `timeout` to `fetchData`").
4. Verification: The exact command to run (e.g., `pytest tests/test_api.py::test_timeout`).
5. Commit: The atomic commit message.

## Dependency Mapping

Dependencies dictate the order of operations. Failure to map dependencies leads to "The Wall" — reaching a task that cannot be started because a prerequisite was forgotten.

### Dependency Types and Applications
- Finish-to-Start (FS): Task B cannot start until Task A finishes. (Implementation -> Test).
- Start-to-Start (SS): Task B can start as soon as Task A starts. (Data migration -> Progress monitoring).
- Finish-to-Finish (FF): Task B finishes when Task A finishes. (API implementation -> Integration docs).
- Start-to-Finish (SF): Task B cannot finish until Task A starts. (Legacy system shutdown -> New system start).

### Critical Path Identification
The Critical Path is the longest chain of dependencies. If any task on this path slips, the whole plan slips.
1. List all tasks in a table.
2. Map all FS dependencies for each task.
3. Sum durations along each possible path from start to end.
4. Identify the path with zero slack (the longest sequence).

### Parallel vs Sequential Decision Table

| Scenario | Relationship | Reason |
|---|---|---|
| Task B uses output from Task A | FS | Data dependency |
| Task B edits file X, Task A edits file Y | Independent | No resource contention |
| Task B edits file X, Task A edits file X | FS | Merge conflict risk |
| Task B is a refactor, Task A is a feature | FS | Refactor should be baseline |
| Task B is a UI mock, Task A is an API | SS | UI can use mock while API builds |
| Task B is a unit test, Task A is implementation | FS | Code must exist to be tested |

### Dependency Notation for Plans
Use brackets to denote dependencies in text-based plans for AI clarity.
- [T1] Setup DB schema
- [T2] Create Model (Depends: T1)
- [T3] Create Controller (Depends: T2)
- [T4] Create View (Depends: none)
- [T5] Integrate View and Controller (Depends: T3, T4)

## Shape Up: Shaping

Shaping is the process of defining the "boundaries of the pitch" before players start the game.

### The Appetite vs The Estimate
An estimate is "How long will this take?" An appetite is "How much time do we want to spend?"
- Small Batch: 1-2 weeks for humans, 5-10 turns for agents.
- Big Batch: 6 weeks for humans, 30-50 turns for agents.
If a solution cannot fit into the appetite, it must be "pared down" in scope, not "estimated longer" in time.

### Breadboarding and Fat Markers
- Breadboarding: Define the functional flow without UI. Use text nodes and arrows to show state transitions.
  Example: [Search Bar] -> (Input) -> [Results List] -> (Click) -> [Product Detail]
- Fat Marker Sketches: Use a "fat marker" to sketch UI. This prevents over-specifying layouts and styles. Focus on placement of major elements (Title, Image, CTA).

### The Circuit Breaker
If a project is not finished within the appetite, the "Circuit Breaker" trips. The project is cancelled or reshaped. Do not automatically grant extensions; extensions are the primary cause of project bloat and technical debt.

### Rabbit Holes and No-Gos
- Rabbit Holes: Deep technical risks (e.g., "We might need to upgrade the entire ORM to support this query"). These must be investigated during the shaping phase, not the building phase.
- No-Gos: Explicit exclusions (e.g., "This feature will NOT include PDF export"). This prevents scope creep during execution.

### Shaping Checklist
1. Is the problem clearly defined?
2. Is there a "Fat Marker" sketch or Breadboard?
3. Have all "Rabbit Holes" been addressed?
4. Are the "No-Gos" documented?
5. Does the solution fit the Appetite?

## Decomposition Decision Tree

Use this logic to evaluate any task before adding it to an execution plan.

1. Can the task be completed in < 10 minutes?
   - Yes: Proceed to step 2.
   - No: Split into sub-tasks.
2. Does the task have a single, binary verification command?
   - Yes: Proceed to step 3.
   - No: Define a specific verification (test, grep, or log check).
3. Does the task touch more than 2 files?
   - Yes: Split by file responsibility (e.g., Task 1 for Model, Task 2 for View).
   - No: Proceed to step 4.
4. Are all dependencies for this task already marked "Completed"?
   - Yes: Task is ready for "in_progress".
   - No: Move task later in the plan or move dependencies earlier.

### Signals for Further Decomposition

| Signal | Evaluation | Action |
|---|---|---|
| "And" in the title | Multiple responsibilities | Split the task |
| "Refactor and Add" | Mixing concerns | Refactor first, then add |
| "Check if..." | Vague outcome | Replace with specific command |
| "Setup X" | Too broad | List specific setup steps |
| Task takes > 2 agent turns | Stalled | Stop and re-decompose |
| "Integrate X with Y" | Complex interface | Break into X prep, Y prep, then join |

## Implementation Recipes (The "Methods" Library)

Use these standard decomposition patterns for common software tasks.

### Recipe: New API Endpoint
1. Create request validation schema/class.
2. Define route in router file.
3. Create controller method (empty skeleton).
4. Write failing integration test for the route.
5. Implement controller logic.
6. Verify with integration test.

### Recipe: Database Migration
1. Create migration file.
2. Verify migration SQL (dry run).
3. Run migration.
4. Verify schema in DB console.
5. Update model/ORM mapping.

### Recipe: Frontend Component
1. Create component file (stub).
2. Add component to parent layout.
3. Define props/state interface.
4. Add basic HTML structure.
5. Apply styling/CSS classes.
6. Add interactivity logic.
7. Verify visually or with unit test.

## Hierarchical Task Networks (HTN) for AI

HTN planning allows an agent to maintain a high-level goal while executing low-level primitives.

### Elements of HTN
- Primitive Tasks: Atomic actions like `edit_file` or `run_command`.
- Compound Tasks: High-level objectives like `implement_auth`.
- Methods: The logic that breaks a Compound Task into sub-tasks.
- Operators: The tools used to execute Primitives.
- Sensors: Tools used to gather state (e.g., `ls`, `read`, `grep`).

### The "Recursive Decomposition" Pattern
1. Take a Compound Task from the pending list.
2. Select a Method based on current system state (Sensors).
3. Decompose into sub-tasks.
4. If a sub-task is Compound, push to top of stack and repeat.
5. If a sub-task is Primitive, execute immediately.
6. Update system state and repeat until stack is empty.

## Task Verification Framework

| Task Type | Verification Strategy | Example Command |
|---|---|---|
| File Creation | Existence check | `ls path/to/file` |
| Code Change | Grep check | `grep "function_name" path/to/file` |
| Feature Logic | Unit Test | `npm test -- path/to/test` |
| API Route | CURL request | `curl -i -X POST localhost:3000/api` |
| DB Schema | SQL Query | `sqlite3 db.sqlite ".schema users"` |
| Dependencies | Build check | `npm run build` |
| Linting | Lint command | `eslint path/to/file` |

## Risk Mitigation Strategies

When a "Rabbit Hole" is detected, add these specific tasks to the plan:
1. "Discovery: Read documentation for library X" (Time-boxed).
2. "Spike: Create minimal reproduction of integration point" (Discardable).
3. "Fallback: Identify alternative approach if X fails".
4. "Checkpoint: Verify feasibility before proceeding to step Y".

## Anti-Patterns in Task Decomposition

| Anti-Pattern | Consequence | Corrective Action |
|---|---|---|
| Functional Silos | "Finished" BE but FE is blocked | Plan by Feature Slices (Vertical) |
| Vague Verbs | Agent "wanders" in the code | Use specific verbs (Rename, Insert, Run) |
| Missing Verification | Silent failures propagate | Mandatory verification command for every step |
| Hidden Dependencies | Plan fails halfway through | Explicit dependency mapping in plan phase |
| Planning without Reading | Decomposing a task that doesn't exist | Run `ls` and `read` before `todowrite` |
| Monolithic Tasks | High context usage, high error rate | Enforce the 2-5 minute micro-task rule |
| Optimistic Planning | Ignoring "Rabbit Holes" | Add risk mitigation tasks upfront |
| Tool-Agnostic Planning | Plan cannot be executed by tools | Map every task to a specific tool call |
| Ignoring Side Effects | "Fixed" one thing, broke five | Add "Run regression tests" as a task |
| Over-planning Triviality | Planning takes longer than doing | Skip `todowrite` for single-step trivial fixes |
| Circular Dependencies | Deadlock in execution | Break cycles by introducing an interface |
| Under-specified Verify | Verification passes falsely | Use strict, automated tests over manual checks |

Decomposition is not about making the work easier; it is about making the work predictable. A perfectly decomposed plan is a sequence of inevitable successes. It allows the agent to move with speed because the "thinking" was done during the planning phase, leaving only the "doing" for the execution phase.
