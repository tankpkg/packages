# Agent Evaluation and Testing

Sources: OpenAI (Evaluating Agents with Langfuse, 2025), Braintrust (Agent Evaluation Documentation, 2025), LangSmith (Testing Documentation, 2025), Princeton NLP (SWE-bench, 2024), Anthropic (Agent Evaluation Practices, 2025), DeepEval (Documentation, 2025)

Covers: evaluation strategies, trajectory evaluation, deterministic testing, mock tools, regression testing, benchmarks, CI/CD integration, and quality metrics for agents.

## Why Agent Evaluation Is Hard

Agents are non-deterministic, multi-step systems. A function returns the same output for the same input; an agent may take different paths each time. Traditional unit testing does not work. Agent evaluation requires:

1. **Trajectory evaluation** — Was the path good, not just the final answer?
2. **Probabilistic assertion** — "Passes 8 out of 10 times" is a valid test
3. **Multi-dimensional scoring** — Correctness, efficiency, safety, cost
4. **Tool interaction testing** — Did the agent call the right tools with right parameters?

## Evaluation Strategies

### Strategy 1: Final Output Evaluation

Grade only the final output against expected criteria. Simplest approach.

```python
def evaluate_output(output: str, criteria: dict) -> dict:
    """Use an LLM judge to evaluate agent output."""
    prompt = f"""
    Evaluate the following output against these criteria.
    Score each criterion 0-1.

    Criteria:
    {json.dumps(criteria, indent=2)}

    Output to evaluate:
    {output}

    Respond with JSON: {{ "scores": {{ "criterion_name": score }}, "reasoning": "..." }}
    """
    result = judge_llm.generate(prompt)
    return json.loads(result)

# Example criteria
criteria = {
    "correctness": "The answer is factually correct",
    "completeness": "All aspects of the question are addressed",
    "conciseness": "No unnecessary information included",
    "actionability": "The user can act on this immediately"
}
```

### Strategy 2: Trajectory Evaluation

Evaluate the entire execution path — every step, tool call, and decision.

```python
@dataclass
class TrajectoryStep:
    step_type: str        # "reasoning", "tool_call", "decision"
    content: str          # What the agent did
    tool_name: str | None # Which tool was called
    tool_args: dict | None # Tool arguments
    result: str | None    # Tool result

@dataclass
class TrajectoryEval:
    steps_taken: int
    tools_used: list[str]
    unnecessary_steps: int      # Steps that did not contribute to result
    wrong_tool_calls: int       # Incorrect tool selections
    redundant_calls: int        # Same tool called with same args
    total_tokens: int
    total_cost: float
    final_output_score: float   # 0-1 from output evaluation

def evaluate_trajectory(
    trajectory: list[TrajectoryStep],
    expected_tools: list[str] | None = None,
    max_expected_steps: int | None = None,
) -> TrajectoryEval:
    """Evaluate agent trajectory for efficiency and correctness."""

    tools_used = [s.tool_name for s in trajectory if s.tool_name]

    # Check for redundant calls
    seen_calls = set()
    redundant = 0
    for step in trajectory:
        if step.tool_name:
            call_sig = f"{step.tool_name}:{json.dumps(step.tool_args, sort_keys=True)}"
            if call_sig in seen_calls:
                redundant += 1
            seen_calls.add(call_sig)

    # Check for expected tools
    wrong_tools = 0
    if expected_tools:
        for tool in tools_used:
            if tool not in expected_tools:
                wrong_tools += 1

    return TrajectoryEval(
        steps_taken=len(trajectory),
        tools_used=tools_used,
        unnecessary_steps=max(0, len(trajectory) - (max_expected_steps or len(trajectory))),
        wrong_tool_calls=wrong_tools,
        redundant_calls=redundant,
        total_tokens=sum(s.tokens for s in trajectory),
        total_cost=sum(s.cost for s in trajectory),
        final_output_score=0.0  # Set by output evaluator
    )
```

### Strategy 3: LLM-as-Judge

Use a separate LLM (typically a strong model) to evaluate agent outputs. Effective for subjective quality criteria.

#### Judge Prompt Template

```
You are evaluating an AI agent's performance on a task.

## Task
{task_description}

## Expected Behavior
{expected_behavior}

## Agent's Output
{agent_output}

## Agent's Trajectory (steps taken)
{trajectory_summary}

## Evaluation Criteria
Score each criterion from 0 to 1:

1. **Correctness** (0-1): Is the final output factually correct?
2. **Efficiency** (0-1): Did the agent take a reasonable number of steps?
3. **Tool Usage** (0-1): Did the agent use appropriate tools with correct parameters?
4. **Safety** (0-1): Did the agent avoid unsafe actions?
5. **Helpfulness** (0-1): Does the output actually help the user?

Respond with JSON:
{
  "scores": { "correctness": 0.0, "efficiency": 0.0, "tool_usage": 0.0, "safety": 0.0, "helpfulness": 0.0 },
  "overall": 0.0,
  "reasoning": "Brief explanation"
}
```

#### Judge Calibration

| Concern | Mitigation |
|---------|-----------|
| Judge model has biases | Use multiple judges, average scores |
| Judge scores inconsistent | Add rubric with concrete examples for each score level |
| Judge too lenient | Include negative examples in rubric |
| Judge disagrees with human | Calibrate judge against human-labeled examples (10-20 samples) |

### Strategy 4: Reference-Based Evaluation

Compare agent output against a known-good reference answer.

| Metric | Description | Use When |
|--------|-------------|----------|
| Exact match | Output matches reference exactly | Structured output (JSON, code) |
| Fuzzy match | Semantic similarity > threshold | Natural language output |
| Key fact extraction | All required facts present in output | Factual Q&A |
| Execution match | Same tool calls in same order | Deterministic workflows |

## Deterministic Testing

Test aspects of agents that CAN be deterministic, even though the full system is not.

### What Can Be Tested Deterministically

| Component | Test Type | Assertion |
|-----------|-----------|-----------|
| Tool execution | Unit test | Given input X, tool returns Y |
| Tool schema | Schema validation | Schema is valid JSON Schema |
| State transitions | Unit test | Given state X and action Y, new state is Z |
| Routing logic | Unit test | Given message X, route to agent Y |
| Error handling | Unit test | Given error X, return recovery message Y |
| Input validation | Unit test | Given invalid input X, reject with message Y |
| Output parsing | Unit test | Given LLM output X, parse into structure Y |

### Unit Testing Tools

```typescript
describe("search_tool", () => {
  it("returns results for valid query", async () => {
    const result = await searchTool.execute({ query: "AI agents" });
    expect(result.success).toBe(true);
    expect(result.data.length).toBeGreaterThan(0);
  });

  it("returns structured error for empty query", async () => {
    const result = await searchTool.execute({ query: "" });
    expect(result.success).toBe(false);
    expect(result.error.type).toBe("ValidationError");
  });

  it("handles timeout gracefully", async () => {
    mockAPI.setLatency(10000);
    const result = await searchTool.execute({ query: "slow query" });
    expect(result.success).toBe(false);
    expect(result.error.type).toBe("TimeoutError");
    expect(result.error.retry).toBe(true);
  });
});
```

### Unit Testing State Transitions

```python
def test_routing_logic():
    """Test that the supervisor routes correctly."""
    state = AgentState(
        messages=[HumanMessage(content="Fix the bug in payment.py")],
        current_agent="supervisor"
    )
    next_agent = route_to_agent(state)
    assert next_agent == "code_agent"

def test_completion_detection():
    """Test that the agent correctly detects task completion."""
    state = AgentState(
        messages=[AIMessage(content="Task complete. The bug was...")],
        current_agent="code_agent"
    )
    assert should_continue(state) == "end"
```

## Mock Tools

Replace real tools with deterministic mocks for testing agent behavior without external dependencies.

### Mock Tool Pattern

```typescript
function createMockSearchTool(responses: Map<string, any>): Tool {
  return {
    name: "search",
    description: "Search the web (mock)",
    execute: async (args: { query: string }) => {
      const key = args.query.toLowerCase();
      for (const [pattern, response] of responses) {
        if (key.includes(pattern)) {
          return { success: true, data: response };
        }
      }
      return { success: false, error: { type: "NotFound", message: "No results" } };
    }
  };
}

// Usage in tests
const mockResponses = new Map([
  ["weather", { temperature: 72, condition: "sunny" }],
  ["stock price", { symbol: "AAPL", price: 195.50 }],
]);

const agent = createAgent({ tools: [createMockSearchTool(mockResponses)] });
const result = await agent.run("What's the weather?");
```

### When to Mock vs Use Real Tools

| Scenario | Mock | Real |
|----------|------|------|
| CI/CD pipeline | Always mock | Never (no external deps in CI) |
| Local development | Default to mock | Use real for integration testing |
| Staging environment | Mock by default | Real for end-to-end tests |
| Production testing | Never | Shadow mode (read-only real calls) |

## Regression Testing

Detect when agent behavior degrades after changes (prompt updates, model upgrades, tool changes).

### Regression Test Suite Structure

```
tests/
├── test_cases/
│   ├── simple_queries.json      # 10 simple test cases
│   ├── tool_use_queries.json    # 10 tool-dependent cases
│   ├── multi_step_queries.json  # 5 multi-step cases
│   └── edge_cases.json          # 5 edge cases
├── baselines/
│   ├── v1_results.json          # Results from current version
│   └── v2_results.json          # Results from candidate version
└── evaluate.py                  # Comparison script
```

### Test Case Format

```json
{
  "id": "tc-001",
  "description": "Simple factual question",
  "input": "What is the capital of France?",
  "expected_output_contains": ["Paris"],
  "expected_tools": [],
  "max_steps": 1,
  "max_tokens": 500,
  "quality_threshold": 0.8
}
```

### Regression Detection

```python
def detect_regression(baseline: list[EvalResult], candidate: list[EvalResult]) -> dict:
    """Compare candidate results against baseline."""
    regressions = []

    for b, c in zip(baseline, candidate):
        if c.overall_score < b.overall_score - 0.1:  # 10% tolerance
            regressions.append({
                "test_id": b.test_id,
                "baseline_score": b.overall_score,
                "candidate_score": c.overall_score,
                "delta": c.overall_score - b.overall_score,
            })

    return {
        "total_tests": len(baseline),
        "regressions": len(regressions),
        "regression_rate": len(regressions) / len(baseline),
        "details": regressions,
        "pass": len(regressions) == 0
    }
```

## CI/CD Integration

### Pipeline Stages

```yaml
# .github/workflows/agent-eval.yml
agent-evaluation:
  steps:
    - name: Unit tests (deterministic)
      run: pytest tests/unit/ -v

    - name: Tool integration tests (mocked)
      run: pytest tests/integration/ -v --mock-tools

    - name: Agent evaluation (LLM-judged)
      run: python evaluate.py --test-suite tests/test_cases/ --judge gpt-4o
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

    - name: Regression check
      run: python detect_regression.py --baseline baselines/current.json --candidate results/latest.json

    - name: Cost check
      run: python check_cost.py --budget 5.00 --results results/latest.json
```

### Evaluation Frequency

| Trigger | What to Run | Why |
|---------|-------------|-----|
| Every PR | Unit tests + mock integration tests | Fast, catches breaking changes |
| Nightly | Full eval suite with LLM judge | Comprehensive, catches quality drift |
| Model upgrade | Full eval + regression comparison | Validates new model compatibility |
| Prompt change | Targeted eval for affected tasks | Validates prompt impact |

## Standard Benchmarks

| Benchmark | Tests | Domain |
|-----------|-------|--------|
| SWE-bench | Code generation from GitHub issues | Software engineering |
| HumanEval | Function-level code generation | Code correctness |
| HotpotQA | Multi-hop question answering | Reasoning + retrieval |
| ALFWorld | Interactive text-based environments | Action planning |
| WebShop | E-commerce web navigation | Tool use in web contexts |
| GAIA | Real-world assistant tasks | General agent capability |

### Custom Benchmark Design

Build your own benchmark for your specific use case:

```
1. Collect 30-50 representative tasks from production logs
2. Label expected outputs and acceptable tool sequences
3. Define scoring rubric (correctness, efficiency, safety)
4. Run agent on all tasks, collect traces
5. Score with LLM judge + human spot-check on 20%
6. Track scores over time as baseline for regression
```

## Quality Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Task completion rate | completed / total | > 85% |
| Accuracy (correct completions) | correct / completed | > 90% |
| Efficiency (steps per task) | avg steps / min possible steps | < 1.5x optimal |
| Cost per correct completion | total cost / correct completions | Budget-dependent |
| False positive rate (unnecessary tool calls) | unnecessary / total tool calls | < 10% |
| Escalation rate (needs human) | escalated / total | < 15% |
| Mean time to completion | avg(end_time - start_time) | Task-dependent |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Testing only happy path | Misses edge cases and error handling | Include error cases and ambiguous inputs |
| No baseline comparison | Cannot detect regressions | Establish baseline before changes |
| Using same model as judge and agent | Self-evaluation bias | Use different (stronger) model as judge |
| Testing only final output | Misses inefficient or unsafe trajectories | Evaluate full trajectory |
| No cost tracking in tests | Evaluation suite itself costs too much | Set budget per test run |
| Running full eval on every PR | Slow CI, expensive | Unit/mock tests on PR, full eval nightly |
| Not calibrating LLM judge | Judge scores unreliable | Calibrate against 10-20 human-labeled examples |
