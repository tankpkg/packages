# Plan Execution

Sources: obra/superpowers executing-plans methodology, LangGraph plan-and-execute, BabyAGI task management

Covers: batch execution, checkpoint protocol, adaptation rules, progress tracking, two-stage review, failure recovery.

## Pre-Execution Review

Before executing the first task, perform a critical analysis of the entire plan. Do not assume the plan is perfect simply because it exists. Execution failure often stems from architectural flaws or dependency oversights that were visible during the planning phase but ignored.

### Critical Review Checklist
1.  **Dependency Mapping**: Verify that no task requires an output from a later task. Check for circular dependencies.
2.  **Tool Availability**: Ensure all required tools (LSP, compilers, test runners, API keys) are functional for the specific tasks listed.
3.  **Feasibility**: Identify any tasks that seem overly optimistic or vague. If a task says "Implement feature X" without sub-steps, it is a high-risk item.
4.  **Impossible Ordering**: Look for "teleportation" errors—tasks that assume a state exists before the task to create that state has been run.
5.  **State Verification**: Confirm the current environment matches the starting assumptions of the plan.

If concerns are identified, raise them immediately. Do not start execution on a flawed plan. If the plan is solid, initialize the tracking mechanism (TodoWrite) and proceed.

## Batch Execution Pattern

Execute tasks in logical batches rather than one by one or all at once. Batching balances momentum with the need for frequent oversight.

### The Power of Three
The default batch size is **3 tasks**.
- **Small enough to review**: Errors are localized and easy to roll back.
- **Large enough for momentum**: Prevents the overhead of constant context switching and reporting.
- **Critical path visibility**: 3 tasks usually cover a meaningful functional unit.

### Adjusting Batch Size
| Scenario | Recommended Size | Rationale |
| :--- | :--- | :--- |
| Complex/Experimental | 1 Task | High uncertainty requires immediate verification and checkpointing. |
| Repetitive/Boilerplate | 5 Tasks | Low risk, high predictability; efficiency is prioritized. |
| Critical Infrastructure | 1 Task | Foundation work must be perfect before building upward. |
| Standard Implementation | 3 Tasks | The balanced default for most coding work. |

### Batch Process Flow
1.  **Load**: Identify the next 3 tasks from the plan.
2.  **Execute**: Move through the tasks sequentially using the Task Execution Loop.
3.  **Validate**: Run comprehensive tests for the entire batch.
4.  **Report**: Summarize progress and show verification output.
5.  **Pivot**: Determine if the next batch size needs adjustment based on results.

## Task Execution Loop

For every task within a batch, follow a strict internal loop to ensure atomic success and clear state management.

### The Loop Steps
1.  **Mark in_progress**: Use the TodoWrite tool to signal active work. This prevents the orchestrator or user from wondering about the current state.
2.  **Follow Exactly**: Implement the logic as specified in the plan. Do not deviate or "gold-plate" the solution during this phase.
3.  **Verify**: Run the exact verification commands specified in the task description.
4.  **Commit**: If verification passes, create a git commit. Include the task name in the commit message for traceability.
5.  **Mark completed**: Update the TodoWrite status immediately.

### Verification Failure
If verification fails, you have a maximum of **3 attempts** to fix the issue within the task loop:
- **Attempt 1**: Direct fix based on error message.
- **Attempt 2**: Check for environmental issues or missing dependencies.
- **Attempt 3**: Review the implementation against the original spec for logic errors.
If it still fails after 3 attempts, transition to the Failure Recovery protocol.

## Checkpoint Protocol

Checkpoints are formal synchronization points between the agent and the system (or user). They prevent "hallucination loops" and ensure work remains aligned with the goal.

### Mandatory Checkpoint Triggers
- Completion of a batch.
- Encountering a blocker that cannot be resolved in 3 attempts.
- Discovery of a fundamental flaw in the plan.
- Before any destructive action (e.g., `rm -rf`, force-pushing, large-scale refactor).

### The Checkpoint Report
A high-quality checkpoint report must include:
1.  **Status Summary**: What was completed vs. what was planned.
2.  **Verification Proof**: Snippets of test results or build logs.
3.  **Remaining Work**: The updated task list for the next batch.
4.  **Deviations**: Any minor changes made to the plan during execution and why.
5.  **Blocked items**: Clear description of what is stopping progress.

## Two-Stage Review

Adopt the obra/superpowers pattern for reviewing finished work. This separates the "what" from the "how."

### Stage 1: Spec Compliance
- **Question**: Does the code do exactly what the plan asked for?
- **Focus**: Functionality, requirements, interface matching.
- **Goal**: Prevent under-building or missing core features.
- **Checklist**:
    - All requirements in the task description met?
    - Inputs and outputs match the specified signatures?
    - Edge cases defined in the task handled?

### Stage 2: Code Quality
- **Question**: Is the code maintainable, clean, and idiomatic?
- **Focus**: Performance, readability, test coverage, naming conventions.
- **Goal**: Prevent technical debt and "hacks."
- **Checklist**:
    - Variable and function names are descriptive?
    - No duplicated logic?
    - LSP diagnostics are clean?
    - Performance is within acceptable bounds?

## Adaptation Rules

Execution is rarely linear. Use the following decision table to determine how to adapt when reality diverges from the plan.

| Signal | Adaptation Action |
| :--- | :--- |
| Task success, no surprises | Continue to next task in batch. |
| Minor error, easily fixed | Fix, verify, note in findings.md, continue. |
| Missing minor dependency | Add task to the current batch, execute, continue. |
| Tooling failure (e.g., LSP down) | Attempt restart; if failed, checkpoint and wait. |
| Fundamental logic error | Stop execution. Mark task as blocked. Replan. |
| Strategy proves impossible | Escalate to user with full context and alternatives. |
| Multiple (3+) task failures | Stop. Perform a 5-Question Reboot. |

## Progress Tracking

Use the Hill Chart mental model (from Basecamp/Shape Up) to understand the nature of the work remaining.

### The Hill Chart
- **Uphill (Figuring it out)**: Research, prototyping, resolving unknowns. Progress is slow and unpredictable. Tasks here are high risk.
- **Downhill (Executing)**: Implementation, styling, refactoring known patterns. Progress is linear and predictable.

### The 5-Question Reboot Test
When feeling lost or after a major failure, answer these five questions to regain orientation:
1.  **Where am I?**: Identify the current phase (Uphill/Downhill) and specific task.
2.  **Where am I going?**: Restate the immediate next milestone.
3.  **What is the goal?**: Review the header of the original plan to ensure the "Why" is still valid.
4.  **What have I learned?**: Read the findings.md or learnings.md for new constraints found during execution.
5.  **What have I done?**: Review progress.md to see the path of successful commits.

## Failure Recovery

If a task fails verification after the 3 internal attempts, move to the 3-Strike Failure Recovery Protocol.

### The 3-Strike Protocol
- **Strike 1: Diagnosis**: Read the full error message and stack trace. Use Grep to find relevant code. Don't guess; find the root cause.
- **Strike 2: Alternative Approach**: If the initial fix failed, try a different implementation path. Use a different tool or library if appropriate.
- **Strike 3: Broader Rethink**: Step back. Is the task itself flawed? Is the assumption behind the task wrong? Search the web or documentation for similar issues.

**After Strike 3**: If the task still fails, you must escalate. Provide the user with the failed code, the error messages, and a summary of the three approaches you tried. Never repeat the same failing action more than three times.

## Subagent Dispatch Pattern

For large, complex plans with independent modules, use the Subagent Dispatch Pattern to parallelize or isolate implementation.

### Dispatch Requirements
1.  **Isolation**: Each subagent gets a specific, self-contained task.
2.  **Context Injection**: Provide the subagent with the full task text, the relevant file paths, and the high-level plan goals.
3.  **Boundaries**: Define exactly what the subagent is allowed to modify.
4.  **Review Loop**: The orchestrator must review the subagent's output (Stage 1 and Stage 2) before incorporating it into the main branch.

### Best Use Cases
- Implementing a suite of independent UI components.
- Writing unit tests for a stable API.
- Refactoring multiple files for a consistent naming convention.
- Data migration scripts where the schema is well-defined.

## Anti-Patterns

Avoid these common execution behaviors that lead to project failure.

| Anti-Pattern | Description | Consequence |
| :--- | :--- | :--- |
| **The Tunnel Vision** | Executing a plan even when a better way is discovered. | Suboptimal code and wasted effort. |
| **Silent Failure** | Ignoring small errors or warnings to maintain "progress." | Cascading failures that are harder to debug. |
| **Gold-Plating** | Adding unrequested features or complexity during a task. | Scope creep and schedule delays. |
| **Commit-Squashing** | Committing 5-10 tasks at once instead of atomically. | Impossible to revert specific changes if bugs are found. |
| **Context Leaking** | Carrying over "hacks" from one task into the next. | Corrupted codebase architecture. |
| **The Ghost Report** | Reporting completion without providing verification proof. | Loss of trust and high risk of hidden bugs. |
| **Batch Overflow** | Attempting to execute 10+ tasks without a checkpoint. | Massive rework if a fundamental error is found late. |
| **Assumption Jump** | Skipping a setup task because you "think" it's done. | Environment mismatch and build failures. |
