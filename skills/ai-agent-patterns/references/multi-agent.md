# Multi-Agent Orchestration

Sources: LangGraph (Multi-Agent Documentation, 2025), CrewAI (Documentation, 2025), AutoGen/AG2 (Microsoft Research, 2024), Anthropic (Building Effective Agents, 2024), Google Research (Scaling Agent Systems, 2025), AWS (Agentic AI in Financial Services, 2025)

Covers: orchestration patterns (supervisor, hierarchical, sequential, parallel, swarm), agent communication, state management, failure handling, and framework-specific implementations.

## When to Go Multi-Agent

Multi-agent systems boost performance up to 81% on parallel tasks but can degrade it by 70% on sequential tasks if misapplied. Add multi-agent complexity only when:

| Signal | Why Multi-Agent |
|--------|----------------|
| Task spans multiple specialized domains | Each agent can be expert in its domain |
| Security boundaries required | Agents run with different permission sets |
| Independent subtasks benefit from parallelism | Concurrent execution reduces latency |
| Different models optimal for different subtasks | Route cheap model for simple, expensive for complex |
| Single agent context window insufficient | Distribute state across agents |

Do NOT go multi-agent for:
- Tasks a single agent handles well (adds coordination overhead)
- Sequential tasks with tight data dependencies (coordination cost > parallelism benefit)
- Prototype/MVP stage (validate single-agent first)

## Orchestration Patterns

### 1. Supervisor (Router)

One supervisor agent receives all tasks and routes them to specialized worker agents. The supervisor synthesizes worker outputs into a final response.

```
User Query → Supervisor Agent
               ├── route to → Agent A (Database queries)
               ├── route to → Agent B (Code analysis)
               └── route to → Agent C (Documentation)
             ← synthesize results ← Worker outputs
```

#### Implementation Skeleton

```typescript
async function supervisor(query: string, agents: Map<string, Agent>): Promise<string> {
  // Step 1: Classify and route
  const routing = await routerLLM.generate({
    prompt: `Given this query, which specialist(s) should handle it?
    Available specialists: ${Array.from(agents.keys()).join(", ")}
    Query: ${query}
    Respond with JSON: { "agents": ["name1", "name2"], "subtasks": ["task1", "task2"] }`,
  });

  const plan = JSON.parse(routing);

  // Step 2: Dispatch to workers
  const results = await Promise.all(
    plan.agents.map((name, i) =>
      agents.get(name).execute(plan.subtasks[i])
    )
  );

  // Step 3: Synthesize
  return await synthesizerLLM.generate({
    prompt: `Original query: ${query}\nSpecialist results:\n${
      results.map((r, i) => `${plan.agents[i]}: ${r}`).join("\n")
    }\nSynthesize a complete response.`,
  });
}
```

#### Characteristics

| Dimension | Value |
|-----------|-------|
| Coordination cost | 2 extra LLM calls (routing + synthesis) |
| Scalability | Add workers without changing supervisor logic |
| Failure handling | Supervisor can retry or re-route on worker failure |
| Best for | Dynamic task routing, heterogeneous capabilities |

### 2. Hierarchical Teams

Multi-level supervision where team leads manage specialized agents, and a top-level supervisor coordinates team leads. Used for complex workflows spanning multiple departments or domains.

```
Top Supervisor
├── Team Lead: Research
│   ├── Web Searcher
│   └── Document Analyst
├── Team Lead: Engineering
│   ├── Code Writer
│   └── Code Reviewer
└── Team Lead: QA
    ├── Test Generator
    └── Test Runner
```

#### When to Use Hierarchical

| Signal | Recommendation |
|--------|---------------|
| 2-4 agents total | Flat supervisor (no hierarchy needed) |
| 5-10 agents | Single-level hierarchy with team leads |
| 10+ agents | Multi-level hierarchy (rare in practice) |
| Cross-team dependencies | Add explicit handoff protocols between team leads |

### 3. Sequential Chains

Agents execute in sequence where each builds on the previous output. Simple, predictable, easy to debug.

```
Query → Agent A (Research) → Agent B (Draft) → Agent C (Review) → Final Output
```

#### Implementation

```python
async def sequential_chain(query: str, agents: list[Agent]) -> str:
    current_input = query
    for agent in agents:
        current_input = await agent.execute(current_input)
    return current_input
```

#### Characteristics

| Dimension | Value |
|-----------|-------|
| Coordination cost | Zero (no routing, no synthesis) |
| Latency | Sum of all agent latencies (serial) |
| Failure handling | Pipeline stops on first failure |
| Best for | Content pipelines (research, draft, edit, publish) |

### 4. Parallel Dispatch

Multiple agents process independent subtasks simultaneously. Results are merged at the end.

```
Query → Task Decomposer
          ├── Agent A (Subtask 1) ──┐
          ├── Agent B (Subtask 2) ──┼── Merger → Final Output
          └── Agent C (Subtask 3) ──┘
```

#### Implementation

```python
async def parallel_dispatch(query: str, agents: dict[str, Agent]) -> str:
    # Decompose
    plan = await decomposer.generate(
        f"Split this into independent subtasks for: {list(agents.keys())}\n"
        f"Query: {query}"
    )
    subtasks = parse_subtasks(plan)

    # Execute in parallel
    results = await asyncio.gather(*[
        agents[name].execute(task)
        for name, task in subtasks.items()
    ])

    # Merge
    return await merger.generate(
        f"Query: {query}\nResults:\n" +
        "\n".join(f"{name}: {result}" for name, result in zip(subtasks.keys(), results))
    )
```

#### Characteristics

| Dimension | Value |
|-----------|-------|
| Coordination cost | 2 LLM calls (decompose + merge) |
| Latency | Max of all agent latencies (parallel) |
| Speedup | Near-linear for independent subtasks |
| Best for | Multi-factor analysis, comparison tasks |

### 5. Swarm Pattern

Agents dynamically hand off control to each other based on context. No central supervisor — agents self-organize using handoff functions.

```
Agent A → (detects need for Agent B's expertise) → Agent B
Agent B → (detects need for Agent C's expertise) → Agent C
Agent C → (task complete) → Return to User
```

#### When to Use Swarm

| Signal | Recommendation |
|--------|---------------|
| Predictable routing rules | Swarm works well |
| Complex, dynamic routing | Swarm works well |
| Need central oversight/logging | Supervisor pattern better |
| Compliance/audit requirements | Supervisor pattern better |

### 6. Debate / Consensus

Multiple agents independently solve the same problem, then debate or vote on the best solution. High cost, high quality.

```
Query → Agent A (Solution 1) ─┐
     → Agent B (Solution 2) ──┼── Judge Agent → Best Solution
     → Agent C (Solution 3) ─┘
```

#### Characteristics

| Dimension | Value |
|-----------|-------|
| Cost | 3-5x single agent (N solutions + judge) |
| Quality | Highest — multiple perspectives |
| Best for | Critical decisions, research, code review |
| Weakness | Expensive; judge introduces single point of failure |

## Agent Communication Patterns

### Message-Based

Agents communicate through structured messages added to a shared conversation history. Simple, traceable, but context window grows quickly.

### State-Based (LangGraph)

Agents read from and write to a shared state object. State graph defines which agent runs next based on current state.

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    current_agent: str
    task_status: str
    results: dict

graph = StateGraph(AgentState)
graph.add_node("researcher", researcher_agent)
graph.add_node("writer", writer_agent)
graph.add_node("reviewer", reviewer_agent)
graph.add_edge("researcher", "writer")
graph.add_edge("writer", "reviewer")
graph.add_conditional_edges("reviewer", route_after_review)
```

### Event-Based

Agents publish events to a shared bus. Other agents subscribe to relevant event types. Decoupled, scalable, harder to debug.

| Pattern | Coupling | Observability | Scalability |
|---------|----------|---------------|-------------|
| Message-based | High | High (full trace) | Limited by context |
| State-based | Medium | Medium (state snapshots) | Good (graph structure) |
| Event-based | Low | Low (requires tracing) | Best (add subscribers) |

## State Management

### Shared State Principles

1. Define state schema upfront — TypedDict, Pydantic, or Zod
2. Each agent writes to its own namespace in state (prevents conflicts)
3. Checkpoint state after each agent step (enables resumption)
4. Include metadata: timestamps, agent IDs, step counts

### State Conflict Resolution

| Conflict | Resolution |
|----------|-----------|
| Two agents write same field | Last-write-wins with timestamp |
| Agent reads stale state | Read-before-write locking |
| State grows unbounded | Summarize completed sections |

## Failure Handling

### Per-Agent Failure

| Strategy | Implementation |
|----------|---------------|
| Retry | Re-run failed agent with same input (max 2 retries) |
| Fallback | Route to backup agent or simpler model |
| Skip | Mark subtask as incomplete, continue with partial results |
| Escalate | Flag for human review (see `references/human-in-the-loop.md`) |

### Cascade Failure Prevention

```
1. Set timeout per agent (prevent indefinite hangs)
2. Set token budget per agent (prevent runaway costs)
3. Circuit breaker: if agent fails N times in M minutes, disable temporarily
4. Partial results: return what succeeded, flag what failed
```

### Deadlock Prevention

- Avoid circular dependencies between agents
- Set maximum total iterations for the system
- Add a watchdog that terminates if no progress for N seconds

## CrewAI-Specific Patterns

CrewAI organizes agents into crews with role-based task assignment.

### Crew Structure

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Senior Research Analyst",
    goal="Find comprehensive and accurate information",
    backstory="Expert researcher with 20 years of experience...",
    tools=[search_tool, web_scraper],
    llm="gpt-4o"
)

writer = Agent(
    role="Technical Writer",
    goal="Create clear, engaging technical content",
    backstory="Award-winning technical writer...",
    tools=[],
    llm="claude-sonnet-4-20250514"
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process="sequential",  # or "hierarchical"
    memory=True,
    verbose=True
)
```

### CrewAI Memory System

| Memory Type | Purpose | Persistence |
|-------------|---------|-------------|
| Short-term | Current task context | Session only |
| Long-term | Cross-session knowledge | Persistent |
| Entity | Structured facts about entities | Persistent |
| External | RAG integration | External store |

## Scaling Considerations

| Agents | Coordination Overhead | Recommendation |
|--------|----------------------|----------------|
| 2-3 | Minimal | Simple orchestration works fine |
| 4-7 | Moderate | Add explicit routing and state management |
| 8-15 | Significant | Hierarchical structure required |
| 15+ | Dominates | Reconsider design — likely overdecomposed |

### Cost Scaling

Total cost = (N agents * avg LLM calls per agent) + coordination overhead

```
Single agent:  5 calls * $0.01 = $0.05
3 agents:      (3 * 5 + 2 coordination) * $0.01 = $0.17
5 agents:      (5 * 5 + 4 coordination) * $0.01 = $0.29
```

Coordination overhead grows linearly with supervisor, quadratically with mesh communication. Avoid mesh communication — use supervisor or sequential patterns.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Starting with multi-agent | Wasted complexity | Validate single-agent first |
| Mesh communication | O(n^2) message passing | Supervisor or sequential |
| No state checkpointing | Cannot resume on failure | Checkpoint after each step |
| Same model for all agents | Over-paying for simple tasks | Route by task complexity |
| No timeout per agent | One stuck agent blocks all | Set per-agent timeouts |
| Vague agent role descriptions | Overlapping responsibilities | Define clear boundaries |
