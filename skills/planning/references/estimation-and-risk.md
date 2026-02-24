# Estimation and Risk Assessment

Sources: Agile Estimating and Planning (Cohn), PMBOK risk management, Shape Up (Basecamp), Software Estimation (McConnell)

Covers: T-shirt sizing, story points, PERT estimation, risk matrices, uncertainty handling, when estimation matters.

## The Psychology of Estimation

Estimation is as much a psychological challenge as a technical one. Human (and AI) biases often lead to significant underestimation or over-conservative padding. Understanding these cognitive traps is the first step toward accurate planning.

### Common Cognitive Biases in Estimation

| Bias | Description | Impact |
| :--- | :--- | :--- |
| **Planning Fallacy** | The tendency to underestimate the time, costs, and risks of future actions while at the same time overestimating the benefits. | Projects finish late and over budget. |
| **Anchoring** | The tendency to rely too heavily on the first piece of information offered (the "anchor") when making decisions. | If a user says "This should take 5 minutes," your estimate will likely stay near that number. |
| **Optimism Bias** | The belief that we are at less risk of experiencing a negative event compared to others. | Ignoring potential bugs or integration issues. |
| **Parkinson's Law** | The adage that "work expands so as to fill the time available for its completion." | Inefficient use of allocated time. |
| **Confirmation Bias** | Seeking out data that supports your initial estimate while ignoring data that contradicts it. | Refusal to adjust estimates when risks appear. |

### Mitigation Strategies
- **Reference Class Forecasting**: Look at how long similar tasks actually took in the past, rather than imagining how long this specific task will take. Use the codebase history as your primary reference.
- **Outside-In View**: Ask "If an average developer were doing this, how long would it take?" to distance yourself from your own optimism.
- **Silent Estimation**: In a team setting, estimate independently before sharing to avoid anchoring on the first person's number.
- **Pre-Mortem**: Imagine the project has failed and ask "What went wrong?" This forces you to identify risks you might otherwise ignore.

## When Estimation Matters vs When It's Waste

Estimation is a tool for decision-making, not a prediction of the future. It provides the data necessary to determine if a task is worth its "appetite" (the cost one is willing to pay) and to flag items requiring decomposition or research.

### Value and Waste Analysis

| Context | Value Provided | Decision Action |
| :--- | :--- | :--- |
| **Release Planning** | Sets stakeholder expectations for milestones. | Adjust roadmap scope. |
| **Comparing Options** | Determines if Approach A is cheaper than B. | Choose implementation path. |
| **Size Identification** | Flags tasks that are too large (XL) for a single work unit. | Trigger decomposition. |
| **Risk Flagging** | High variance indicates missing information. | Schedule "spike" or research. |
| **Resource Allocation** | Helps in deciding which developer works on what. | Match task complexity to skill level. |
| **Budgeting** | Provides a basis for financial commitments. | Approve or reject project funding. |
| **Trivial Tasks** | Waste: Estimation takes longer than the fix. | Skip estimation; just execute. |
| **Known Contexts** | Waste: Task is identical to previous work. | Use historical actuals. |
| **No Deadlines** | Waste: Single developer working on open-ended R&D. | Use time-boxing (appetite). |

### The "Appetite" Philosophy
Adopt the Shape Up approach when precise estimates are impossible. Instead of asking "How long will this take?", ask "How much time are we willing to spend on this?" This fixes the time (the appetite) and makes the scope variable. This is particularly useful for AI agents where the path to a solution may be non-linear.

## T-Shirt Sizing

T-shirt sizing is the primary technique for rapid, high-level estimation. It categorizes effort into buckets based on ranges rather than specific numbers, which prevents false precision.

### Sizing Scale for Software Tasks

| Size | Range | Detailed Examples |
| :--- | :--- | :--- |
| **XS** | < 30 min | Typo fixes, simple config changes, single-line docs, dependency version bump, adding a comment. |
| **S** | 30 min - 2 hr | Modifying a single endpoint, adding a unit test, updating a UI component's CSS, adding a log line. |
| **M** | 2 - 8 hr | Implementing a new feature with tests, refactoring a module, API integration, fixing a complex bug. |
| **L** | 1 - 3 days | Multi-component feature, database migrations, complex state logic, performance tuning. |
| **XL** | 3+ days | Architecture changes, large-scale refactors, new sub-systems, platform migrations, security audits. |

### Sizing Rules
1. **The XL Rule**: If a task is sized as XL, it is too large for a single execution cycle. You must decompose it into smaller (S/M/L) sub-tasks before proceeding with implementation.
2. **Contextual Scaling**: Size is relative to the current codebase knowledge. A task that is "S" in a familiar project may be "M" or "L" in a legacy codebase without documentation.
3. **The Complexity Multiplier**: A task with high complexity but low volume of code (e.g., a regex or concurrency fix) should be sized higher than its line count suggests.

## Story Points and Relative Sizing

Story points measure the total effort required to implement a work item, including work volume, complexity, and uncertainty.

### Fibonacci Sequence
Use the Fibonacci sequence (1, 2, 3, 5, 8, 13, 21) to reflect the increasing uncertainty as tasks grow larger.
- **1, 2, 3**: Small, well-understood tasks.
- **5, 8**: Significant features with some unknowns.
- **13, 21**: High uncertainty; these must be broken down.

### Anchor Points
Identify a "Reference Story"—a task that everyone understands and agrees is a "3". Compare all other tasks to this anchor.

### Mapping Story Points to T-Shirt Sizes

| Story Points | T-Shirt Size | Rationalization |
| :--- | :--- | :--- |
| 1 | XS | Near-instant execution. |
| 2 | S | Minor effort, zero complexity. |
| 3 | S/M | Standard task, well-defined. |
| 5 | M | Multi-hour task with standard complexity. |
| 8 | L | Multi-day task; requires significant focus. |
| 13+ | XL | High risk/effort; requires decomposition. |

### Velocity and Planning
- **Velocity**: The average number of story points completed per sprint.
- **Stabilization**: Velocity typically stabilizes after 3-4 sprints.
- **Formula**: `Total Points / Average Velocity = Number of Sprints Needed`.

## PERT Estimation (Three-Point)

Program Evaluation and Review Technique (PERT) uses a weighted average to account for uncertainty.

### The PERT Formula
1. **Expected Value (E)** = `(Optimistic + 4 x Most Likely + Pessimistic) / 6`
2. **Standard Deviation (SD)** = `(Pessimistic - Optimistic) / 6`

### Worked Example: API Integration
- **Optimistic (O)**: 2 hours (Everything works first try).
- **Most Likely (M)**: 4 hours (Typical debugging).
- **Pessimistic (P)**: 12 hours (Auth issues, rate limiting).

**Calculation**:
- E = `(2 + (4 * 4) + 12) / 6` = `30 / 6` = **5 hours**
- SD = `(12 - 2) / 6` = **1.67 hours**

### Confidence Intervals
- **68% Confidence**: Expected +/- 1 SD (3.33h to 6.67h)
- **95% Confidence**: Expected +/- 2 SD (1.66h to 8.34h)

## The Cone of Uncertainty

The Cone of Uncertainty describes how accuracy improves as a project progresses.

### Uncertainty Table

| Project Phase | Potential Variance | Implication |
| :--- | :--- | :--- |
| **Initial Concept** | 0.25x to 4.0x | Do not commit to dates. |
| **Approved Requirements** | 0.50x to 2.0x | Useful for high-level roadmaps. |
| **Detailed Design** | 0.67x to 1.5x | Suitable for budget allocation. |
| **Coding Started** | 0.80x to 1.25x | High precision for sprint commits. |
| **Testing/QA** | 0.90x to 1.10x | Nearly certain completion time. |

## Risk Assessment

Risk management identifies and responds to potential problems early.

### Risk Matrix (5x5)
Score = Likelihood (1-5) x Impact (1-5).

| Score Range | Classification | Required Action |
| :--- | :--- | :--- |
| **15-25** | High | Immediate mitigation or plan change. |
| **8-14** | Medium | Prepare contingency plans (Plan B). |
| **1-7** | Low | Accept and monitor. |

### Risk Register Template

| Risk ID | Description | Likelihood | Impact | Score | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R-001 | Dependency API change | 2 | 5 | 10 | Version lock and use wrappers. |
| R-002 | Vague Requirements | 5 | 3 | 15 | Request written acceptance criteria. |
| R-003 | Env setup failure | 3 | 4 | 12 | Test setup in clean Docker. |
| R-004 | Regression risk | 3 | 5 | 15 | Increase unit test coverage. |
| R-005 | Security vulnerability | 2 | 5 | 10 | Run automated security scanners. |
| R-006 | Data loss during migration | 1 | 5 | 5 | Perform migration on staging first. |

### Common Software Project Risks and Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Technical Debt** | Allocate 20% of effort to refactoring. |
| **Scope Creep** | Strict change control; time-box features. |
| **Knowledge Silos** | Enforce peer reviews and documentation. |
| **Ambiguous Docs** | Spend 1h mapping code before starting. |
| **Single Point of Failure** | Cross-train team members on critical systems. |

## Risk Identification for AI Agents

AI agents face specific risks related to context and tool reliability.

### AI Risk Categories

| Category | Risk Signal | Mitigation Action |
| :--- | :--- | :--- |
| **Technical** | Unfamiliar syntax/API. | 30-min research "spike". |
| **Integration** | 3+ system data flow. | Draw sequence diagram first. |
| **Knowledge** | No legacy documentation. | Read source and tests for 1h. |
| **Tool Failure** | Inconsistent LSP data. | Verify with manual `read` calls. |
| **Context Overload** | 20+ files in context. | Decompose into isolated modules. |
| **Hallucination** | Complex logic without tests. | Write failing test cases first (TDD). |

## Estimation for AI Agents (Practical Workflow)

Agents should size tasks to determine the necessary planning rigor.

### Quick Estimation Protocol
1. **Compare**: Find similar tasks in the codebase history.
2. **Count Files**: 1-2 (S), 3-5 (M), 6+ (L).
3. **Count Unknowns**: Each major unknown bumps the size one bucket.
4. **Determine Appetite**: Ask user for their time budget.
5. **Finalize T-Shirt Size**: Communicate this to the user.

### Planning Level Selection
- **XS/S**: Skip formal plan. Just steps + execution.
- **M**: Create light plan (todo list).
- **L**: Create detailed plan + risk assessment.
- **XL**: Propose decomposition into smaller PRs.

## Step-by-Step Worked Example: Decomposing an XL Task

**Scenario**: User asks to "Migrate the entire notification system from SendGrid to Postmark."

1. **Initial Assessment**:
   - Files involved: ~25
   - Unknowns: Postmark API, current template structure, error handling logic.
   - Size: **XL**
   - Risk: High (Likelihood 4, Impact 5 = Score 20)

2. **Decomposition Strategy**:
   - **Task 1 (M)**: Research Postmark API and create a prototype "Send" script.
   - **Task 2 (M)**: Create an abstraction layer (interface) for notifications.
   - **Task 3 (L)**: Migrate existing SendGrid implementation to use the new interface.
   - **Task 4 (L)**: Implement the Postmark provider for the interface.
   - **Task 5 (M)**: Switch providers and monitor for 24 hours.

3. **Revised Estimates**:
   - Total effort is now 5 smaller, manageable tasks. The agent can commit to Task 1 immediately.

## Communication Framework

Sharing estimates with humans requires clarity on the "Why" behind the number.

### The "Estimate-Rationale-Risk" Formula
Never share just a number. Use this structure:
1. **The Number**: "I estimate this as a Medium (4-8 hours)."
2. **The Rationale**: "This involves changing 3 files and adding 1 new API endpoint."
3. **The Risk**: "However, if the database migration fails, it could take longer (up to 12 hours)."

### Managing Expectations
- **Range over Point**: Always say "2-4 days" instead of "Tuesday."
- **Confidence Level**: "I am 80% confident in this estimate."
- **The "No-Go" Signal**: If the risk score is > 15, tell the user: "I cannot estimate this reliably without 1 hour of research first."

## Estimation and Risk Anti-Patterns

1. **Precision as Accuracy**: Providing "4.32 hours." **Fix**: Use ranges or buckets.
2. **The Golden Path**: Ignoring testing and CI. **Fix**: Add 40% overhead for non-coding.
3. **Negotiated Estimates**: Cutting time because of pressure. **Fix**: Offer scope reduction.
4. **Estimating for Others**: Agent estimating for humans. **Fix**: Only estimate for yourself.
5. **The "Just A" Fallacy**: Underestimating "simple" tasks. **Fix**: Treat "simple" with skepticism.
6. **Anchoring**: Sticking to a user's guess. **Fix**: Start with a "clean sheet" estimate.
7. **Ignoring Technical Debt**: Estimating as if code is clean. **Fix**: Factor in pre-factoring.
8. **Sandbagging**: Padding by 3x. **Fix**: Use honest estimates + contingency label.
9. **90% Done Syndrome**: Claiming 90% completion for 50% of time. **Fix**: Measure by tests passed.
10. **Mythical Man-Month**: Adding agents to a late project. **Fix**: Reduce scope instead.
11. **Silver Bullet Fallacy**: Assuming a new tool will cut time in half. **Fix**: Tooling changes have learning curves.
12. **Sunk Cost Fallacy**: Continuing a high-risk path because "we already started." **Fix**: Re-evaluate at milestones.

## Glossary of Estimation Terms

- **Appetite**: The amount of time/resources a team is willing to spend on a problem.
- **Backlog Grooming**: The process of reviewing, refining, and estimating items in the project backlog.
- **Burndown Chart**: A graphical representation of work left to do versus time.
- **Contingency Buffer**: Extra time added to an estimate to account for identified risks.
- **Feature Creep**: The tendency for a project to grow in scope as it progresses.
- **Relative Sizing**: Comparing the size of a new task to previously completed tasks.
- **Spike**: A time-boxed research task used to reduce uncertainty.
- **Velocity**: The rate at which a team completes work, usually measured in story points.
