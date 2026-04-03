# Agent Architectures

Sources: Yao et al. (ReAct, 2022), Shinn et al. (Reflexion, 2023), Wang et al. (Plan-and-Solve, 2023), Zhou et al. (LATS, 2023), Xu et al. (REWOO, 2023), Kim et al. (LLMCompiler, 2023), Anthropic (Building Effective Agents, 2024), Redis (AI Agent Architecture Patterns, 2026)

Covers: core single-agent and multi-agent architecture patterns, selection criteria, trade-offs, and implementation approaches.

## The Architecture Spectrum

Agent architectures form a spectrum from simple to complex. Each added layer increases capability but also increases cost, latency, and failure surface. Start at the simplest pattern that satisfies requirements and escalate only when evaluation shows measurable gaps.

```
Single LLM call → ReAct → Plan-and-Execute → Reflexion → LATS → Multi-Agent
(simplest)                                                       (most complex)
```

## ReAct (Reasoning + Acting)

ReAct alternates between thinking and doing in a loop: reason about current state, take an action, observe the result, then reason again based on what happened. The loop continues until the task completes or a maximum iteration count is reached.

### The Loop

```
while not done and iterations < max_iterations:
    thought = llm.generate(system_prompt + history + "Think step by step")
    action = llm.generate(thought + "What action should I take?")
    observation = execute_tool(action)
    history.append(thought, action, observation)
    done = check_completion(observation)
```

### Characteristics

| Dimension | Value |
|-----------|-------|
| LLM calls per task | 5-7 (each reason-act-observe cycle) |
| Adaptability | High (re-reasons after each observation) |
| Transparency | High (explicit reasoning trace) |
| Cost | Higher than planning (more LLM calls) |
| Best for | Tool-heavy workflows, single domain, dynamic tasks |
| Weakness | Context window fills quickly; struggles with multi-domain |

### Context Management

Tool schemas and instructions consume tens of thousands of tokens. Manage this by:

- Loading tool descriptions on-demand (not all at once)
- Summarizing tool outputs before adding to history
- Setting a maximum observation length per tool call
- Pruning old reason-act-observe triples from history

### When ReAct Fails

| Symptom | Cause | Escalate To |
|---------|-------|-------------|
| Agent loops without progress | Task requires upfront planning | Plan-and-Execute |
| Quality inconsistent across runs | No self-correction mechanism | Reflexion |
| Wrong tool selected repeatedly | Too many tools, ambiguous descriptions | Tool retrieval + routing |
| Context window exceeded | Long reasoning chains | Summarization or multi-agent split |

## Plan-and-Execute

Split strategy from execution. A planner creates a complete plan upfront, then an executor runs each step. This reduces total LLM calls because the plan is generated once, not re-derived at each step.

### Two Variants

| Variant | Description | Trade-off |
|---------|-------------|-----------|
| Single-query planning | Generate full plan in one call, execute sequentially | Faster, cheaper, but brittle if steps depend on dynamic results |
| Iterative replanning | Replan after each step or on failure | More adaptive, higher cost |

### Implementation Pattern

```
plan = planner_llm.generate(
    "Create a step-by-step plan for: {task}\n"
    "Available tools: {tool_descriptions}\n"
    "Output as numbered list."
)
steps = parse_plan(plan)

results = []
for step in steps:
    result = executor_llm.generate(
        f"Execute this step: {step}\n"
        f"Previous results: {results}\n"
        f"Available tools: {tool_descriptions}"
    )
    results.append(result)

    if needs_replan(result, remaining_steps):
        remaining_steps = planner_llm.generate(
            f"Original plan: {steps}\n"
            f"Completed: {results}\n"
            f"Replan remaining steps."
        )
```

### Characteristics

| Dimension | Value |
|-----------|-------|
| LLM calls per task | 1 (plan) + N (execution steps), typically 3-4 total |
| Adaptability | Low (single-query) to Medium (iterative) |
| Cost | Lower than ReAct for structured tasks |
| Best for | Predictable multi-step tasks, efficiency-sensitive workloads |
| Weakness | Brittle when early steps produce unexpected results |

## Reflexion

Extends ReAct with self-critique. The agent executes a task, evaluates its own output, reflects on what worked or failed, and retries with learned improvements. This creates an improvement loop that raises output quality at the cost of additional LLM calls.

### Five Phases

```
1. REASON  — Analyze the current state and goal
2. ACT     — Take action based on reasoning
3. OBSERVE — Collect results and external feedback
4. REFLECT — Critique: What worked? What failed? What to change?
5. REPEAT  — Try again with reflection insights added to context
```

### Implementation Pattern

```
max_attempts = 3
memory = []

for attempt in range(max_attempts):
    result = agent.execute(task, memory=memory)
    evaluation = evaluator.grade(result, criteria)

    if evaluation.passes:
        return result

    reflection = llm.generate(
        f"Task: {task}\n"
        f"Your output: {result}\n"
        f"Evaluation: {evaluation}\n"
        f"Previous reflections: {memory}\n"
        f"What went wrong and how to improve on the next attempt?"
    )
    memory.append(reflection)
```

### Characteristics

| Dimension | Value |
|-----------|-------|
| LLM calls per task | 2-3x base pattern (execution + evaluation + reflection per attempt) |
| Quality improvement | Significant — iterative refinement catches errors |
| Cost | High — each reflection cycle adds LLM calls |
| Best for | Quality-critical tasks, code generation, complex reasoning |
| Weakness | Expensive; diminishing returns after 2-3 iterations |

### When to Use Reflexion

- Code generation where tests can validate output
- Content creation with quality rubrics
- Complex reasoning tasks where first attempts have known failure modes
- Any task where you can define an automated evaluator

## LATS (Language Agent Tree Search)

Combines Monte Carlo Tree Search with LLM agents. Instead of a single execution path, LATS explores multiple solution paths in parallel, evaluates each, and selects the best. Inspired by AlphaGo's search strategy.

### How It Works

```
1. SELECTION   — Pick the most promising node in the search tree
2. EXPANSION   — Generate multiple candidate actions from that node
3. EVALUATION  — Score each candidate using LLM self-evaluation or external signals
4. BACKPROP    — Update scores up the tree to inform future selection
5. REPEAT      — Continue until solution found or budget exhausted
```

### Characteristics

| Dimension | Value |
|-----------|-------|
| LLM calls per task | Many (explores multiple branches) |
| Quality | Highest — explores solution space systematically |
| Cost | Very high — multiple parallel evaluations |
| Best for | Complex search/exploration, math, code generation competitions |
| Weakness | Impractical for latency-sensitive or cost-sensitive production use |

### Production Viability

LATS excels in benchmarks but is rarely used in production due to cost. Consider it for:

- Offline batch processing where quality justifies cost
- Problems with verifiable solutions (math, code with test suites)
- Research and development, not user-facing real-time systems

## REWOO (Reasoning Without Observation)

Generates the full plan including all tool calls before executing any of them. Unlike ReAct, the agent does not observe intermediate results while planning. Tool outputs are collected and fed to a final solver.

### Pattern

```
1. PLANNER   — Generate plan with all tool calls specified upfront
2. WORKER    — Execute all tool calls (potentially in parallel)
3. SOLVER    — Synthesize final answer from plan + all tool results
```

### Characteristics

| Dimension | Value |
|-----------|-------|
| LLM calls | 2 (planner + solver) + tool calls |
| Parallelism | High — independent tool calls execute simultaneously |
| Cost | Low — minimal LLM calls |
| Best for | Tasks where tool calls are independent and predictable |
| Weakness | Cannot adapt tool calls based on intermediate results |

## LLMCompiler

Automatically identifies tool call dependencies and executes independent calls in parallel. A planner decomposes the task into a DAG (directed acyclic graph) of tool calls, then a scheduler executes them with maximum parallelism.

### Pattern

```
1. PLANNER    — Decompose task into tool calls with dependency annotations
2. SCHEDULER  — Build DAG, identify parallelizable calls
3. EXECUTOR   — Run independent calls in parallel, sequential where dependent
4. JOINER     — Combine results into final output
```

### When to Use

Use LLMCompiler when a task requires multiple independent data fetches (e.g., "Compare weather in NYC, London, and Tokyo" — three parallel API calls).

## Architecture Selection Decision Matrix

| Factor | ReAct | Plan-Execute | Reflexion | LATS | REWOO |
|--------|-------|-------------|-----------|------|-------|
| Dynamic adaptation | High | Low-Medium | High | High | None |
| Cost efficiency | Medium | High | Low | Very Low | High |
| Quality ceiling | Medium | Medium | High | Highest | Medium |
| Implementation complexity | Low | Medium | Medium | High | Low |
| Latency | Medium | Low | High | Very High | Low |
| Transparency | High | Medium | High | Medium | Medium |
| Production readiness | High | High | Medium | Low | Medium |

### Selection Heuristic

```
Is the task simple classification or extraction?
  -> No agent needed. Single LLM call.

Does the task require tools?
  -> Are tool calls independent and predictable?
     -> Yes: REWOO or LLMCompiler (parallel, efficient)
     -> No: Continue below

  -> Does execution need to adapt based on intermediate results?
     -> Yes: ReAct (dynamic, observable)
     -> No: Plan-and-Execute (efficient, structured)

  -> Is output quality critical enough to justify 2-3x cost?
     -> Yes: Add Reflexion layer on top of ReAct or Plan-and-Execute

  -> Does the task span multiple specialized domains?
     -> Yes: Multi-agent orchestration (see references/multi-agent.md)
```

## Hybrid Architectures

Production systems typically combine patterns. Common combinations:

| Combination | Use Case |
|-------------|----------|
| Plan-and-Execute + Reflexion | Structured tasks that need quality assurance |
| ReAct + Multi-Agent | Dynamic routing to specialized domain agents |
| REWOO + ReAct fallback | Try parallel first, fall back to adaptive if plan fails |
| Supervisor + Reflexion workers | Multi-agent with self-improving specialists |

## Performance Characteristics

Agent performance degrades over consecutive runs. Plan for this:

| Metric | Single Run | 8 Consecutive | Degradation |
|--------|-----------|---------------|-------------|
| Task completion | ~60% | ~25% | 58% drop |
| Token efficiency | Baseline | 2-3x baseline | Context accumulation |
| Latency | Baseline | 1.5-2x | History processing |

Mitigation strategies:
- Reset agent state between independent tasks
- Summarize history aggressively
- Set maximum iteration limits
- Use evaluation to detect quality degradation and trigger reset

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Starting with multi-agent | Unnecessary complexity, higher cost | Start with ReAct, escalate when evaluation shows gaps |
| No iteration limit on ReAct | Agent loops indefinitely burning tokens | Set max_iterations (typically 5-10) |
| Planning without replanning | Plan breaks on unexpected intermediate results | Add replanning on failure or significant state change |
| Reflexion without automated evaluator | Reflection is vague without concrete feedback | Define rubric or test suite before adding Reflexion |
| Using LATS for latency-sensitive tasks | Tree search is inherently slow and expensive | Reserve for offline or batch processing |
| Ignoring context window limits | Agent silently drops old history | Monitor token count, summarize proactively |
