# Prioritization Frameworks

Sources: Intercom RICE framework, MoSCoW (DSDM Consortium), Eisenhower Matrix, ICE scoring methodology

Covers: RICE scoring, ICE scoring, MoSCoW method, Eisenhower matrix, framework selection, software task prioritization.

## RICE Scoring

The RICE framework is a quantitative system for prioritizing ideas by evaluating four factors: Reach, Impact, Confidence, and Effort. It is designed to minimize bias and provide a data-driven score for comparing disparate features.

### The RICE Formula

The total score is calculated as follows:
Score = (Reach x Impact x Confidence) / Effort

### Component Definitions

*   **Reach**: The number of people or events affected per time period (e.g., users per month, transactions per week).
*   **Impact**: A subjective score representing the contribution to a key goal. Use the following scale:
    *   3: Massive Impact
    *   2: High Impact
    *   1: Medium Impact
    *   0.5: Low Impact
    *   0.25: Minimal Impact
*   **Confidence**: A percentage expressing certainty about the other three estimates (Reach, Impact, and Effort).
    *   100%: High Confidence. Estimates are backed by quantitative usage data, direct user research, and technical feasibility spikes.
    *   80%: Medium Confidence. Based on qualitative feedback, analogous features in similar products, or clear stakeholder requirements.
    *   50%: Low Confidence. Based on intuition, market trends, or unverified assumptions. Requires a "Confidence Discount" on the total score.
    *   Under 50%: Total "Moonshot". Estimates are effectively guesses. These tasks should be de-prioritized in favor of discovery tasks (e.g., prototyping) to increase confidence.

### Calculating Reach

Reach measures the number of distinct entities (users, events, or objects) affected by a change within a specific time window. Accurate reach calculation prevents over-estimating "loud" features that only benefit a tiny subset of power users.

*   **Software Users**: Number of unique active users who interact with the feature monthly.
*   **Transactions**: Number of API calls, database writes, or financial transactions affected.
*   **Developers**: If an internal tool, the number of engineers whose workflow is improved.
*   **Time Period**: Standardize on a "per month" or "per quarter" basis across all items for consistency.

#### Reach Calculation Example: Feature "Search Bar Autocomplete"
*   Total Monthly Active Users: 50,000
*   Percentage of users who use the Search Bar: 40% (20,000 users)
*   Percentage of searchers who will benefit from autocomplete: 100%
*   **Reach**: 20,000 users per month.
*   **Effort**: The total amount of time the task will require from all team members, measured in person-months (or person-days for granular backlogs).

### Worked Example: Social Login Implementation

Task: Add "Sign in with Google" to the mobile app.

| Factor | Value | Rationale |
| :--- | :--- | :--- |
| Reach | 10,000 | Projected new users per month who currently drop off at registration. |
| Impact | 2.0 | High impact on conversion rates for onboarding. |
| Confidence | 0.8 | 80% confidence based on competitor analysis and user requests. |
| Effort | 1.5 | Person-months for frontend, backend, and security review. |

**Calculation**: (10,000 x 2.0 x 0.8) / 1.5 = 10,666
**Score**: 10,666

### When to Use RICE

*   Use RICE when you have access to usage metrics and historical data.
*   Ideal for established products with data-driven teams.
*   Best for grooming large backlogs where stakeholders have conflicting "gut feelings."

### Limitations

*   Requires significant time to estimate all four factors accurately.
*   Complex for small, rapid tasks or bug fixes.
*   Can lead to "analysis paralysis" if data is unavailable.

## ICE Scoring

The ICE framework is a faster, simpler alternative to RICE, often used by growth teams and startups for rapid experimentation.

### The ICE Formula

Score = (Impact + Confidence + Ease) / 3

### Component Definitions (1-10 Scale)

*   **Impact**: How much will this project improve the metric we are targeting?
*   **Confidence**: How sure am I that this will work?
*   **Ease**: How easy is this to implement? (Note: Higher score = less effort).

### Worked Example: Landing Page Headline Test

Task: A/B test a new value proposition on the homepage.

| Factor | Value | Rationale |
| :--- | :--- | :--- |
| Impact | 7 | High potential to lift click-through rate. |
| Confidence | 5 | Unsure if the new copy resonates better than the old one. |
| Ease | 9 | Only requires a CMS change and starting the test. |

**Calculation**: (7 + 5 + 9) / 3 = 7
**Score**: 7

### When to Use ICE

*   Use ICE for early-stage products with limited data.
*   Best for growth hacking, marketing experiments, and internal tools.
*   Ideal when speed of decision-making is more valuable than precision.

### ICE vs RICE Comparison

| Feature | ICE | RICE |
| :--- | :--- | :--- |
| Complexity | Low | High |
| Precision | Subjective | Quantitative |
| Input | Gut check / Intuition | Data / Metrics |
| Speed | Very Fast | Moderate |
| Use Case | Growth / Experiments | Product Roadmap |

## MoSCoW Method

The MoSCoW method categorizes requirements based on their necessity for a successful delivery. It is a qualitative approach used to build consensus among stakeholders.

### The Categories

*   **Must Have**: Critical requirements. The project fails or is illegal/unsafe without these. No viable workaround exists.
*   **Should Have**: Important but not vital. The project can launch without them, though it may be painful. Workarounds usually exist.
*   **Could Have**: Desirable features that increase satisfaction but have minimal impact if omitted. "Nice-to-haves."
*   **Won't Have**: Items explicitly excluded from the current scope/iteration. Helps prevent scope creep.

### Decision Questions

*   **Must Have**: "What happens if this is not included?" (If the answer is "We cannot ship," it is a Must).
*   **Should Have**: "Can we manually handle this for the first two weeks?" (If yes, it is a Should).
*   **Could Have**: "Will the user even notice this is missing?" (If no, it is a Could).

### Rule of Thumb: The 60/20/20 Rule

To ensure project agility, aim for:
*   Must-Haves: < 60% of total effort.
*   Should-Haves: ~20% of total effort.
*   Could-Haves: ~20% of total effort.

### Worked Example: E-commerce MVP

| Category | Item | Rationale |
| :--- | :--- | :--- |
| Must Have | Add to Cart | Fundamental commerce functionality. |
| Must Have | Secure Checkout | Cannot legalise sales without payment processing. |
| Should Have | Product Search | Essential for usability, but users could navigate categories. |
| Could Have | Product Reviews | Valuable for social proof, but not required for a transaction. |
| Won't Have | Gift Cards | Too complex for initial launch; postponed to V2. |

## Eisenhower Matrix

The Eisenhower Matrix focuses on urgency and importance to manage time and tasks effectively.

### The 2x2 Grid

| | Urgent | Not Urgent |
| :--- | :--- | :--- |
| **Important** | **Q1: Do Now** | **Q2: Schedule** |
| | Crises, Deadlines, Critical Bugs | Planning, Architecture, Prevention |
| **Not Important** | **Q3: Delegate** | **Q4: Eliminate** |
| | Interruptions, Most Emails | Time Wasters, Busy Work |

### Quadrant Details

*   **Q1 (Urgent + Important)**: Tasks that demand immediate attention. If ignored, they cause immediate failure (e.g., production server down).
*   **Q2 (Not Urgent + Important)**: High-value work that contributes to long-term goals. Because they aren't urgent, they are often neglected. **Key Insight: Most sustainable value is created here.**
*   **Q3 (Urgent + Not Important)**: Tasks that feel pressing but don't contribute to goals. Usually involve other people's priorities.
*   **Q4 (Not Urgent + Not Important)**: Low-value activities that provide zero return on investment.

### Worked Example: Developer Daily List

Task: Managing a developer's inbox and task queue.

| Task | Category | Action |
| :--- | :--- | :--- |
| Patch security vulnerability in Production | Q1 (Urgent/Important) | **Do Now**: High-priority immediate action. |
| Code review for a non-blocking feature | Q3 (Urgent/Not Important) | **Delegate/Defer**: Pressing for the author, but not your goal. |
| Research new testing framework for Q3 | Q2 (Not Urgent/Important) | **Schedule**: High-value long-term improvement. |
| Scrolling through non-technical Slack channels | Q4 (Not Urgent/Not Important) | **Eliminate**: Distraction with zero ROI. |

### Key Insight: The Q2 Trap
Most high-performing developers fail because they spend 90% of their time in Q1 and Q3. Successful prioritization requires carving out "Deep Work" time for Q2 tasks (e.g., refactoring, documentation, learning) before they become Q1 crises.

## Framework Selection Decision Tree

Use this table to determine which framework to apply based on your current constraints and environment.

| Situation | Best Framework |
| :--- | :--- |
| You have usage data and need a roadmap | RICE |
| You need a quick gut-check for experiments | ICE |
| You have a fixed deadline or regulatory audit | MoSCoW |
| You are managing your own daily task list | Eisenhower |
| You need to align multiple stakeholders on scope | MoSCoW or RICE |
| You are in an early-stage startup with no data | ICE |
| You are grooming a massive backlog of 100+ items | RICE |

## Prioritizing Software Development Tasks (Practical AI Guide)

For AI agents executing a plan, use this simplified five-step logic to determine the sequence of operations.

### Step 1: Identify Dependencies
Locate "must-do-first" tasks. These are foundational elements (e.g., setting up a database schema, installing core libraries). No other work can proceed without them.

### Step 2: Identify Blockers
Locate tasks that unblock the highest volume of downstream work. For example, implementing Authentication often unblocks every other protected API route.

### Step 3: Identify Risk
Locate tasks with the most unknowns or external integrations. Tackle these early to fail fast or adjust the plan before sinking effort into easier tasks.

### Step 4: Identify Quick Wins
Locate high-value, low-effort tasks (e.g., updating a config file that fixes a major UI bug). These provide immediate momentum.

### Step 5: Recommended Execution Order
1.  **Dependencies**: The "Pipe-cleaning" phase.
2.  **Blockers**: The "Throughput" phase.
3.  **Risky Tasks**: The "De-risking" phase.
4.  **Quick Wins**: The "Value-delivery" phase.
5.  **Remaining Backlog**: The "Cleanup" phase.

### Practical AI Execution Table

| Type | Example | Priority | Rationale |
| :--- | :--- | :--- | :--- |
| Dependency | `npm install`, DB migration | Highest | Foundation for all code execution. |
| Blocker | Auth Middleware, Shared State | High | Enables parallel development of sub-features. |
| Risk | Stripe Integration, WebSockets | Medium-High | High probability of technical blockers or plan changes. |
| Quick Win | CSS fix, Error logging | Medium | Provides immediate feedback/value with zero complexity. |
| Feature | User Profile Page | Low-Medium | Standard feature development once plumbing is done. |
| Refactor | Cleaning up variable names | Lowest | Necessary for long-term health, but non-functional today. |

## AI Agent Prioritization Checklist

When an AI agent is tasked with planning a complex implementation, it must run this checklist to verify its task ordering:

1.  **Foundation First**: Have I identified all environment setup tasks? (Dependencies)
2.  **Bottleneck Identification**: Which task, if delayed, prevents the most other tasks from starting? (Blockers)
3.  **Third-Party Reality Check**: Does this plan rely on an API or library I haven't used before? (Risk)
4.  **Value Momentum**: Is there a "low-hanging fruit" task I can finish in under 5 minutes to show progress? (Quick Wins)
5.  **Linearity Check**: Are these tasks strictly sequential, or can any be executed in parallel?
6.  **Scope Scrub**: Have I identified any "Won't Have" items that I should skip to save tokens and time?

## Stack Ranking

Stack ranking is the process of ordering every item in a list from 1 to N. It is a "forced-choice" mechanism that prevents the "everything is high priority" trap.

### The Mechanism

*   No two items can have the same rank.
*   Use pairwise comparison: "If I can only finish one of these two today, which one is it?"
*   Continue until the entire list is linear.

### When to Use

*   When a backlog has too many "P0" or "Must-Have" items.
*   When resources (time, compute, developers) are extremely constrained.
*   When an AI agent has a list of 5 tasks to do in one turn.

## Summary Comparison Table

| Framework | Best For | Data Needed | Speed | Precision | Team Size |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RICE | Roadmap Grooming | High (Usage) | Slow | High | Large |
| ICE | Rapid Testing | Low (Intuition) | Very Fast | Low | Small |
| MoSCoW | Fixed Scope/MVP | Medium (Policy) | Moderate | Medium | Medium |
| Eisenhower | Daily Productivity | Low (Judgment) | Fast | Low | Individual |

## Prioritization Anti-Patterns

| Don't | Do |
| :--- | :--- |
| Prioritize based on the loudest person. | Use a scoring framework (RICE/ICE). |
| Mark every task as "P0" or "Urgent." | Use Stack Ranking or MoSCoW. |
| Ignore technical debt in favor of features. | Use Eisenhower Q2 to schedule maintenance. |
| Start with the "easiest" tasks first. | Start with Dependencies and Blockers. |
| Prioritize based on sunk cost. | Evaluate current Impact and Confidence. |
| Neglect the "Won't Have" list. | Explicitly define scope boundaries. |
| Ignore Confidence in your estimates. | Discount scores based on uncertainty. |
| Trust gut feeling over user data. | Validate Impact assumptions with Reach. |
