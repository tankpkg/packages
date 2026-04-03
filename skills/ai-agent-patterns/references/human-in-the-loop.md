# Human-in-the-Loop Patterns

Sources: LangGraph (Interrupts Documentation, 2025), Anthropic (Building Effective Agents, 2024), CrewAI (Human Input Documentation, 2025), OpenAI (Agents Best Practices, 2025), AWS (Agentic AI Patterns, 2025)

Covers: approval gates, interrupt patterns, review cycles, escalation strategies, confidence thresholds, feedback loops, and framework-specific implementations.

## Why Human-in-the-Loop

Agents make mistakes. Some mistakes are recoverable (wrong search query); others are not (sending an email to the wrong person, deleting production data, making a financial transaction). Human-in-the-loop (HITL) adds oversight at critical decision points.

### When to Add Human Oversight

| Signal | HITL Required | Reasoning |
|--------|--------------|-----------|
| Irreversible actions | Yes | Cannot undo: emails, payments, deletions |
| High-stakes decisions | Yes | Financial, legal, medical, security-critical |
| Regulated industry | Yes | Compliance mandates human review |
| Low agent confidence | Yes | Agent signals uncertainty |
| Ambiguous user intent | Yes | Agent cannot determine correct action |
| Reversible, low-risk actions | No | File reads, searches, calculations |
| Deterministic operations | No | Format conversion, data transformation |
| High-frequency repetitive tasks | No | Human fatigue reduces review quality |

### HITL Design Principles

1. **Minimize interruptions** — Every interrupt breaks user flow. Only interrupt for actions that justify the cost of human attention.
2. **Present actionable context** — Show the agent's reasoning, the proposed action, and its confidence. Do not ask "Is this OK?" without context.
3. **Default to safe** — If the human does not respond within the timeout, reject the action (not approve it).
4. **Learn from approvals** — Track which actions get approved/rejected. Tune confidence thresholds to reduce unnecessary interrupts over time.

## Pattern 1: Approval Gates

Block execution before a specific action until a human approves.

### Implementation

```typescript
interface ApprovalRequest {
  actionType: string;        // "send_email", "delete_record", "make_payment"
  description: string;       // Human-readable summary of what the agent wants to do
  reasoning: string;         // Why the agent chose this action
  confidence: number;        // 0-1, agent's self-assessed confidence
  parameters: Record<string, any>;  // The action parameters
  timeout: number;           // Seconds to wait for approval
  defaultOnTimeout: "reject" | "approve";  // Almost always "reject"
}

interface ApprovalResponse {
  approved: boolean;
  feedback?: string;         // Optional human feedback for the agent
  modifiedParameters?: Record<string, any>;  // Human can adjust parameters
}

async function executeWithApproval(
  request: ApprovalRequest,
  executor: (params: Record<string, any>) => Promise<any>
): Promise<any> {
  const response = await requestHumanApproval(request);

  if (!response.approved) {
    return {
      status: "rejected",
      feedback: response.feedback,
      suggestion: "Adjust approach based on feedback and try again"
    };
  }

  const params = response.modifiedParameters || request.parameters;
  return await executor(params);
}
```

### Approval Gate Placement

| Action Category | Gate Placement | Example |
|----------------|---------------|---------|
| Data mutation | Before write/delete operations | "Delete 47 records matching criteria X?" |
| External communication | Before send | "Send this email to client@example.com?" |
| Financial operations | Before transaction | "Transfer $500 to account Y?" |
| Configuration changes | Before apply | "Update production config: timeout=30s?" |
| Code deployment | Before deploy | "Deploy commit abc123 to production?" |

## Pattern 2: Interrupt and Resume

Pause the agent's execution at a checkpoint, allow human input, then resume from where it stopped. Requires state persistence.

### LangGraph Interrupt Pattern

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

def research_agent(state):
    """Agent researches and proposes an action."""
    results = search(state["query"])
    proposed_action = plan_action(results)
    return {
        **state,
        "proposed_action": proposed_action,
        "status": "awaiting_approval"
    }

def execute_action(state):
    """Execute the approved action."""
    result = perform(state["proposed_action"])
    return {**state, "result": result, "status": "completed"}

# Build graph with interrupt
graph = StateGraph(AgentState)
graph.add_node("research", research_agent)
graph.add_node("execute", execute_action)
graph.add_edge("research", "execute")

# Compile with checkpointing and interrupt
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["execute"]  # Pause before execution
)

# Run until interrupt
config = {"configurable": {"thread_id": "task-123"}}
result = app.invoke({"query": "Find and fix the bug"}, config)
# Agent pauses here — state is persisted

# Later: human reviews and resumes
# Option A: approve and continue
app.invoke(None, config)  # Resume from checkpoint

# Option B: modify state and continue
app.update_state(config, {"proposed_action": modified_action})
app.invoke(None, config)
```

### Interrupt Placement Strategies

| Strategy | Description | Use When |
|----------|-------------|----------|
| interrupt_before | Pause before a node executes | Need approval before action |
| interrupt_after | Pause after a node executes | Need review of output |
| Conditional interrupt | Pause only when condition met | Confidence below threshold |
| Periodic interrupt | Pause every N steps | Long-running tasks needing checkpoints |

### Conditional Interrupt

```python
def should_interrupt(state) -> bool:
    """Interrupt only for high-risk or low-confidence actions."""
    if state["action_type"] in HIGH_RISK_ACTIONS:
        return True
    if state["confidence"] < CONFIDENCE_THRESHOLD:
        return True
    if state["estimated_cost"] > COST_THRESHOLD:
        return True
    return False

# In the graph
def maybe_interrupt(state):
    if should_interrupt(state):
        # Signal the framework to pause
        raise InterruptRequest(
            reason=f"Action '{state['action_type']}' requires approval",
            context=state
        )
    return state
```

## Pattern 3: Review Cycles

Agent produces output, human reviews and provides feedback, agent revises. Repeats until human approves or max iterations reached.

### Implementation

```
Cycle:
  1. Agent generates output (draft, plan, analysis)
  2. Present output to human with "Approve / Request Changes / Reject"
  3a. Approved → proceed to next step
  3b. Request Changes → agent receives feedback, regenerates (go to 1)
  3c. Rejected → agent abandons this approach, tries alternative
  Max cycles: 3 (prevent infinite revision loops)
```

### Review Interface Template

```
## Agent Output for Review

**Task:** {task_description}
**Approach:** {reasoning_summary}
**Confidence:** {confidence_score}/1.0

### Proposed Output
{agent_output}

### Actions:
- [Approve] — Proceed with this output
- [Request Changes] — Provide feedback for revision
  Feedback: _______________
- [Reject] — Abandon this approach
```

### When to Use Review Cycles

| Scenario | Review Cycles? | Reasoning |
|----------|---------------|-----------|
| Content creation (blog posts, reports) | Yes | Subjective quality, tone matters |
| Code generation for production | Yes | Correctness and style review |
| Customer-facing communications | Yes | Brand voice, accuracy critical |
| Internal data analysis | Sometimes | Review if decisions based on output |
| Automated data processing | No | Review adds latency without value |

## Pattern 4: Escalation

Agent detects it cannot handle a situation and escalates to a human with full context.

### Escalation Triggers

| Trigger | Detection Method |
|---------|-----------------|
| Repeated failure | Same tool fails 3+ times |
| Confidence below threshold | Self-assessed confidence < 0.3 |
| Out-of-scope request | Query doesn't match any tool/capability |
| Contradictory information | Sources disagree, agent cannot resolve |
| User frustration detected | Negative sentiment in repeated queries |
| Safety/compliance concern | Content policy triggered |

### Escalation Context Package

When escalating, provide the human with everything needed to take over:

```typescript
interface EscalationPackage {
  reason: string;              // Why the agent is escalating
  attemptsSummary: string;     // What the agent tried and why it failed
  currentState: any;           // Full agent state for context
  relevantHistory: Message[];  // Conversation excerpt
  suggestedActions: string[];  // What the agent thinks the human should try
  priority: "low" | "medium" | "high" | "critical";
  timeConstraint?: string;     // "User waiting" or "Batch, no rush"
}
```

## Pattern 5: Confidence-Based Routing

Route actions through different oversight levels based on agent confidence.

### Routing Table

| Confidence | Route | Latency Impact |
|------------|-------|---------------|
| 0.9 - 1.0 | Auto-execute, log for audit | None |
| 0.7 - 0.9 | Auto-execute, flag for review | None (async review) |
| 0.4 - 0.7 | Execute after lightweight approval | Low (quick yes/no) |
| 0.0 - 0.4 | Full human review before execution | High (detailed review) |

### Confidence Estimation

Models can self-assess confidence, but calibration varies. Improve confidence estimates by:

```
1. Ask the model: "Rate your confidence in this action from 0 to 1. 
   Consider: Do you have all needed information? Are there ambiguities?
   Is the action reversible?"
2. Calibrate: Track actual success rate per confidence bucket
3. Adjust thresholds: If 0.7 confidence only succeeds 50% of time,
   lower the auto-execute threshold
```

## Feedback Loops

Human oversight generates valuable training signal. Capture and use it.

### Feedback Collection

| Event | Capture |
|-------|---------|
| Approval | Action type, parameters, confidence → "good action" |
| Rejection | Action type, parameters, feedback → "bad action, here's why" |
| Modified parameters | Original vs modified → "close but needed adjustment" |
| Escalation resolution | Human's solution → "this is what should have happened" |

### Applying Feedback

```
Short-term: Add feedback to agent's working memory for current session
Medium-term: Store in semantic memory for future similar situations
Long-term: Use feedback to tune prompts, tool descriptions, confidence thresholds
```

## Production Considerations

### Timeout Handling

| Scenario | Timeout | Default Action |
|----------|---------|---------------|
| Synchronous (user waiting) | 60-120 seconds | Reject and notify |
| Asynchronous (batch job) | 24 hours | Queue for next business day |
| Critical (security alert) | 15 minutes | Escalate to on-call |

### Notification Channels

| Urgency | Channel |
|---------|---------|
| Low | Dashboard/email — review at convenience |
| Medium | Slack/Teams notification |
| High | Push notification + Slack |
| Critical | PagerDuty/on-call rotation |

### Audit Trail

Log every HITL interaction for compliance and improvement:

```typescript
interface AuditEntry {
  timestamp: string;
  agentId: string;
  actionType: string;
  proposedAction: any;
  confidence: number;
  humanDecision: "approved" | "rejected" | "modified" | "escalated";
  feedback?: string;
  responseTime: number;    // How long the human took
  reviewer: string;        // Who reviewed
}
```

## Framework-Specific Implementation

### LangGraph

- Built-in `interrupt_before` and `interrupt_after` on graph nodes
- State persisted via checkpointers (memory, SQLite, PostgreSQL)
- Resume with `invoke(None, config)` or `update_state()` then `invoke()`
- Supports streaming partial results while waiting for approval

### CrewAI

- `human_input=True` on Task enables approval before task completion
- Crew-level `human_input` for all tasks
- Custom callback functions for approval logic

### Mastra

- Workflow steps can suspend and resume
- Built-in human approval step type
- Webhook-based notification for async approval

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Interrupting for every action | Human fatigue, slow throughput | Confidence-based routing — only interrupt when needed |
| No timeout on approval requests | Agent hangs indefinitely | Set timeout, default to reject |
| Approving on timeout | Unsafe actions slip through | Always default to reject on timeout |
| No context in approval request | Human cannot make informed decision | Include reasoning, parameters, and confidence |
| Not learning from feedback | Same unnecessary interrupts repeat | Track approval rates, tune thresholds |
| Blocking on async-appropriate reviews | User waits for non-urgent review | Queue low-priority reviews asynchronously |
