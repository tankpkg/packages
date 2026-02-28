# Tool Use and Agents

Sources: Huyen (AI Engineering, ch. 6 & 10), Lanham (AI Agents in Action), Arsanjani & Bustos (Agentic Architectural Patterns), 2025–2026 production patterns

Covers: tool design, function calling mechanics, parallel execution, error recovery, agent architecture spectrum, multi-agent orchestration patterns, planning strategies, failure modes.

## Tool Design Principles

A tool is any capability the model can invoke: API calls, database queries, calculations, file reads, web searches. Well-designed tools are the difference between a useful agent and an unreliable one.

### Design Rules

| Rule | Rationale |
|------|-----------|
| One tool does one thing | Compound tools obscure failure attribution; hard to retry partial steps |
| Use verb_noun naming | `search_documents`, `get_user`, `send_email` — unambiguous to the model |
| Type all parameters explicitly | JSON schema prevents the model guessing argument types |
| Write descriptions as instructions | "Returns the top 5 documents matching the query" — tell the model what to expect |
| Return structured data, not prose | The model processes JSON better than free-text tool results |
| Include error states in return type | `{success: bool, data: ..., error: str \| null}` — never raise exceptions that halt the loop |
| Make tools idempotent when possible | Safe to retry on failure without side effects |

### Tool Definition Pattern

```
Tool definition:
    name:        "search_documents"
    description: "Search the knowledge base for documents relevant to a query.
                  Returns up to k document chunks with their source metadata."
    parameters:
        query:   {type: string,  description: "Search terms or natural language question"}
        k:       {type: integer, description: "Number of results to return (1–20)", default: 5}
        filters: {type: object,  description: "Optional metadata filters (e.g., {doc_type: 'policy'})"}
    returns:
        results: [{content: string, source: string, score: float}]
        error:   string | null
```

The description field is critical — models select tools based on descriptions, not names. Write descriptions as if explaining to a smart colleague who has never seen your codebase.

## Function Calling Mechanics

### Request → Execute → Continue Loop

```
1. Send messages + tool definitions to model
2. Model responds with one of:
   a. tool_call(s): model wants to execute tools
   b. text response: model has enough information to answer
3. If tool_call(s):
   a. Execute each tool (see parallel execution below)
   b. Append tool_result(s) to messages
   c. Send messages back to model (go to step 2)
4. If text response: return to user
```

This loop continues until the model produces a text response or a max_steps limit is hit.

### Message Thread Structure

```
messages = [
    {role: "system",    content: "You are a helpful assistant with access to tools."},
    {role: "user",      content: "What are our refund policies?"},
    {role: "assistant", tool_calls: [{id: "call_1", name: "search_documents", input: {query: "refund policy"}}]},
    {role: "tool",      tool_call_id: "call_1", content: {results: [...], error: null}},
    {role: "assistant", content: "Based on the documents, our refund policy is..."},
]
```

Always maintain the full message thread. The model uses tool results to generate the final response.

## Parallel Tool Calls

When the model returns multiple tool_calls in a single response, execute them concurrently unless there is an explicit dependency between them.

### When to Parallelize

| Scenario | Parallelize? |
|----------|-------------|
| Independent lookups (get_user + get_order) | Yes |
| Sequential dependency (search → then filter results) | No |
| Same tool with different arguments | Yes |
| Tool B uses output of Tool A | No |

```
parallel execution pattern:
    tool_calls = [call_1, call_2, call_3]
    results = await Promise.all([
        execute(call_1),
        execute(call_2),
        execute(call_3),
    ])
    # All three finish in max(latency_1, latency_2, latency_3) instead of sum
```

3 independent tools at 300ms each: 900ms sequential → 300ms parallel. Always parallelize independent calls.

## Tool Error Recovery

Errors are inevitable. Design the recovery strategy at the tool level, not in the LLM loop.

### Recovery Decision Table

| Error Type | Return to Model | Retry | Escalate |
|------------|----------------|-------|----------|
| Validation error (bad arguments) | Yes — with schema hint | After model corrects args | Never |
| Not found (empty result) | Yes — return null with context | No | If critical |
| Permission denied | Yes — explain limitation | No | To user or admin |
| Rate limit (429) | No — retry silently | Yes, with backoff | After 3 fails |
| Timeout | Yes — return partial or error | Once | After 2 fails |
| Service unavailable | No — retry silently | Yes | After 3 fails |
| Tool logic error (bug) | Yes — return error message | No | Alert on-call |

### Max Steps Guard

Always set a maximum number of tool call iterations. Without it, a confused model can loop indefinitely.

```
max_steps = 10
steps = 0

while steps < max_steps:
    response = model.generate(messages, tools=tools)
    if response.type == "text":
        return response.content
    execute_tools(response.tool_calls)
    messages.append(tool_results)
    steps += 1

return fallback_response("Maximum steps reached. Could not complete the task.")
```

## Agent Architecture Spectrum

Not every task needs a fully autonomous agent. Match architecture to task complexity.

### Architecture Options

| Architecture | Control Flow | Predictability | Use When |
|-------------|-------------|---------------|----------|
| Single LLM call | Fixed | Highest | Simple Q&A, classification |
| LLM + tools (1 loop) | Semi-structured | High | Lookup + generate |
| ReAct agent | LLM-directed | Medium | Open-ended, multi-step |
| Multi-agent | LLM-orchestrated | Lower | Complex, parallelizable |

Prefer workflows (predefined code paths) over agents for production. Workflows are auditable, debuggable, and predictable. Agents excel at tasks where the path is genuinely unknown at design time.

### ReAct Loop (Reason + Act)

The fundamental single-agent pattern. The model alternates between reasoning about the current state and taking an action (tool call).

```
Thought: I need to find the user's order history to answer this question.
Action: get_order_history(user_id="u_123", limit=10)
Observation: [order_1, order_2, order_3]
Thought: The user's most recent order is order_1. Now I need the tracking status.
Action: get_shipment_status(order_id="order_1")
Observation: {status: "shipped", eta: "2026-03-02"}
Thought: I have all the information needed.
Response: Your most recent order ships on March 2nd.
```

## Multi-Agent Orchestration Patterns

### 1. Orchestrator-Worker

```
Orchestrator (central planner)
    ├─ Worker A (retrieval specialist)
    ├─ Worker B (code executor)
    └─ Worker C (summarizer)
```

**Topology**: Hub and spoke. Orchestrator receives the task, decomposes it, delegates to specialized workers, aggregates results.

**Use when**: Task has distinct phases requiring different expertise. Orchestrator enforces sequencing and handles failures.

**Failure mode**: Orchestrator becomes a bottleneck; single point of failure. Fix: make orchestrator stateless; retry at orchestration level.

### 2. Sequential Pipeline

```
Agent A → output → Agent B → output → Agent C → final result
```

**Topology**: Linear chain. Each agent receives the previous agent's output.

**Use when**: Task is a defined sequence of transformations (extract → classify → enrich → format).

**Failure mode**: Cascading errors. A bad output from Agent A corrupts all downstream agents. Fix: validate output schema at each stage before passing forward.

### 3. Fan-Out / Gather (Parallel)

```
Orchestrator
    ├─ Worker 1 (subtask 1) ─┐
    ├─ Worker 2 (subtask 2) ─┼─ Aggregator → final result
    └─ Worker 3 (subtask 3) ─┘
```

**Use when**: Task decomposes into independent subtasks (research 5 competitors simultaneously, process 100 documents in parallel).

**Failure mode**: Partial failure — some workers succeed, some fail. Fix: define quorum (e.g., 3/5 required), use partial results if acceptable.

### 4. Generator-Critic (Reflection)

```
Generator agent → draft
Critic agent → critique → Generator agent → revised draft → ...
```

**Use when**: Output quality matters more than speed. Code review, document editing, plan validation.

**Failure mode**: Infinite refinement loop. Fix: hard limit on iterations (3–5 max); accept-or-escalate after limit.

### 5. Human-in-the-Loop

```
Agent operates autonomously
    → Reaches decision gate (irreversible action, high stakes)
    → Pauses, surfaces to human
    → Human approves/rejects/modifies
    → Agent continues
```

**Use when**: Actions are irreversible (send email, make purchase, delete records) or high-stakes (financial, legal, medical).

**Implementation**: Define approval gates explicitly. Log every human decision with context for audit.

## Planning Strategies

How agents decompose complex tasks before acting.

| Strategy | Approach | When to Use |
|----------|----------|-------------|
| Zero-shot | Model selects tools directly based on tool descriptions | Simple, well-defined tasks |
| Chain-of-thought | Model reasons step-by-step before each tool call | Complex, multi-step tasks |
| Plan-then-execute | Generate full plan upfront, execute sequentially | Tasks with known structure |
| Adaptive planning | Revise plan based on intermediate tool results | Tasks with uncertain paths |

For high-stakes tasks, use plan-then-execute and validate the plan before execution. For exploratory tasks, use adaptive planning.

## Agent Failure Modes

### Common Failures and Fixes

| Failure Mode | Detection | Fix |
|-------------|-----------|-----|
| Wrong tool selected | Tool results irrelevant to task | Improve tool descriptions; reduce tool count |
| Bad tool arguments | Tool returns validation error | Stricter parameter schemas; add argument examples |
| Hallucinated tool name | Tool_call references non-existent tool | Validate tool name before execution; return error to model |
| Context overflow | Generation quality drops in long sessions | Summarize conversation history at regular intervals |
| Infinite loop | Same tool called repeatedly with same args | Track call history; break if (tool, args) pair repeats |
| Unnecessary tool calls | Retrieval for questions the model already knows | Teach the model when NOT to retrieve (self-RAG prompt) |
| Cascading error | Early tool failure corrupts later steps | Validate and sanitize each tool result before appending |

### Loop Detection

```
call_history = {}

before executing tool_call(name, args):
    key = hash(name + JSON(args))
    if key in call_history and call_history[key] >= 2:
        abort("Loop detected: same tool call repeated 2+ times")
    call_history[key] += 1
```

## Tool Count Guidelines

| Tool Count | Model Behavior | Strategy |
|-----------|---------------|----------|
| 1–10 | Reliable selection | Include all tools in every request |
| 10–30 | Occasional confusion | Group tools by task; prefilter by intent |
| 30+ | Frequent tool selection errors | Dynamic tool loading: select 5–10 tools relevant to current task |

For large tool libraries, add a tool-routing step before the main agent loop: classify the user intent, load only the relevant subset of tools.
