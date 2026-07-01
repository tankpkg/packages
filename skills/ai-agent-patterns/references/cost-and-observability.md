# Cost Optimization and Observability

Sources: LangFuse (Documentation, 2025), LangSmith (Documentation, 2025), Braintrust (Documentation, 2025), Anthropic (Prompt Caching, 2024), OpenAI (Token Management, 2025), production agent architecture research (2025-2026)

Covers: model routing, prompt caching, token budgets, batch processing, tracing, metrics, observability platforms, cost tracking, latency monitoring, and production monitoring patterns.

## Cost Optimization

Agents are expensive. A single ReAct agent with 5-7 LLM calls per task costs $0.05-0.30 per interaction. At 10,000 daily requests, that is $500-3,000/month on LLM calls alone. Multi-agent systems multiply this. Cost optimization is a production requirement, not a nice-to-have.

### Strategy 1: Model Routing

Route tasks to the cheapest model that can handle them. Use expensive models only when quality justifies the cost.

#### Routing Table

| Task Complexity | Model Tier | Examples | Cost per 1K tokens |
|----------------|------------|---------|-------------------|
| Simple extraction, classification | Fast/cheap | GPT-4o-mini, Haiku, Gemini Flash | $0.0001-0.001 |
| Standard reasoning, tool calling | Mid-tier | GPT-4o, Sonnet, Gemini Pro | $0.003-0.015 |
| Complex reasoning, creative tasks | Premium | o1, Opus, GPT-4.5 | $0.015-0.060 |

#### Routing Implementation

```typescript
interface ModelRouter {
  route(task: TaskMetadata): ModelConfig;
}

function routeByComplexity(task: TaskMetadata): ModelConfig {
  // Classifier determines task complexity (cheap model call)
  const complexity = classifyComplexity(task);

  switch (complexity) {
    case "simple":
      return { model: "gpt-4o-mini", maxTokens: 500 };
    case "standard":
      return { model: "gpt-4o", maxTokens: 2000 };
    case "complex":
      return { model: "claude-sonnet-4-20250514", maxTokens: 4000 };
    case "expert":
      return { model: "claude-opus-4-20250514", maxTokens: 8000 };
  }
}
```

#### Complexity Classification

Classify task complexity using a cheap model or heuristics:

| Signal | Complexity | Reasoning |
|--------|-----------|-----------|
| Short input, single question | Simple | Classification or extraction |
| Requires tool calling | Standard | Needs reasoning + action loop |
| Multi-step reasoning | Standard-Complex | Plan + execute + synthesize |
| Creative, nuanced, or ambiguous | Complex | Needs stronger model for quality |
| Domain expert knowledge needed | Expert | Premium model for accuracy |

### Strategy 2: Prompt Caching

Cache the static prefix of prompts (system prompt, tool definitions, few-shot examples) so repeated calls pay for the prefix only once.

#### Provider Support

| Provider | Mechanism | Cache Duration | Savings |
|----------|-----------|---------------|---------|
| Anthropic | Automatic (cache_control breakpoints) | 5 minutes | 90% on cached prefix tokens |
| OpenAI | Automatic (matching prefix) | ~5-10 minutes | 50% on cached prefix tokens |
| Google Gemini | Explicit cached content API | Configurable | Up to 75% |

#### Anthropic Cache Control

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,  # Static, cached across calls
            "cache_control": {"type": "ephemeral"}
        }
    ],
    tools=tools,  # Tool definitions also cached
    messages=messages  # Dynamic per-request
)
```

#### Maximizing Cache Hits

```
1. Place static content FIRST in the prompt:
   System prompt → Tool definitions → Few-shot examples → Dynamic content

2. Keep the static prefix identical across requests:
   - Do not randomize example order
   - Do not include timestamps in system prompt
   - Do not embed dynamic data in tool descriptions

3. Batch related requests within the cache window (5 min):
   - Process similar queries together
   - Route to same model instance when possible
```

### Strategy 3: Token Budgets

Set maximum token spend per agent step and per total task. Fail fast when budget is exceeded rather than burning tokens on a likely-failing task.

```typescript
interface TokenBudget {
  maxInputPerStep: number;     // Max input tokens per LLM call
  maxOutputPerStep: number;    // Max output tokens per LLM call
  maxTotalInput: number;       // Total input budget for entire task
  maxTotalOutput: number;      // Total output budget for entire task
  maxSteps: number;            // Maximum agent iterations
}

const DEFAULT_BUDGET: TokenBudget = {
  maxInputPerStep: 8000,
  maxOutputPerStep: 2000,
  maxTotalInput: 50000,
  maxTotalOutput: 15000,
  maxSteps: 10,
};

function checkBudget(usage: TokenUsage, budget: TokenBudget): boolean {
  if (usage.totalInput > budget.maxTotalInput) return false;
  if (usage.totalOutput > budget.maxTotalOutput) return false;
  if (usage.steps > budget.maxSteps) return false;
  return true;
}
```

### Strategy 4: Output Caching

Cache tool results for deterministic operations. Do not re-call tools that return the same result for the same input.

| Tool Type | Cacheable? | TTL |
|-----------|-----------|-----|
| Database query (same params) | Yes | 1-5 minutes |
| Web search | Yes | 5-30 minutes |
| File read (unchanged file) | Yes | Until file modified |
| API call (idempotent GET) | Yes | Varies by API |
| Write/mutation operations | No | Never cache |
| Real-time data (stock prices) | No | Never cache |

### Strategy 5: Batch Processing

Group similar requests and process them in a single LLM call or batch API call.

```
# Instead of 10 separate classification calls:
response = llm.generate(
    "Classify each of the following items:\n"
    "1. {item_1}\n2. {item_2}\n...\n10. {item_10}\n"
    "Return JSON array of classifications."
)
# 1 call instead of 10 — ~10x cost reduction
```

### Cost Monitoring Dashboard Metrics

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Cost per task (avg) | < $0.05 | > $0.15 |
| Cost per task (p95) | < $0.20 | > $0.50 |
| Daily spend | Budget-dependent | > 120% of daily budget |
| Cache hit rate | > 60% | < 40% |
| Failed tasks (wasted spend) | < 5% | > 15% |
| Tokens per task (avg) | < 10K | > 30K |

## Observability

### Why Agent Observability Matters

Agents are non-deterministic multi-step systems. Without observability:
- Cannot debug failures (which step failed and why?)
- Cannot optimize cost (which calls are expensive?)
- Cannot measure quality (are outputs getting better or worse?)
- Model upgrades take weeks instead of days

### Observability Platform Comparison

| Platform | Type | Strengths | Pricing |
|----------|------|-----------|---------|
| LangFuse | Open-source | Self-hostable, LangChain integration, cost tracking | Free (self-hosted), paid cloud |
| LangSmith | Commercial | Deep LangChain integration, playground, datasets | Free tier, paid plans |
| Braintrust | Commercial | Evaluation-focused, experiment tracking, CI/CD | Free tier, paid plans |
| Helicone | Open-source | Simple proxy model, request logging | Free (self-hosted), paid cloud |
| Custom OpenTelemetry | DIY | Full control, fits existing infra | Engineering cost |

### Tracing

Traces capture the complete execution path of an agent — every LLM call, tool invocation, and state transition — as a hierarchical tree.

#### Trace Structure

```
Trace: "Research and summarize AI trends"
├── Span: Agent Loop (iteration 1)
│   ├── Span: LLM Call (reasoning)
│   │   ├── Input: 4,200 tokens
│   │   ├── Output: 350 tokens
│   │   ├── Model: gpt-4o
│   │   ├── Latency: 1.2s
│   │   └── Cost: $0.014
│   └── Span: Tool Call (web_search)
│       ├── Input: {"query": "AI trends 2026"}
│       ├── Output: [5 results]
│       └── Latency: 0.8s
├── Span: Agent Loop (iteration 2)
│   ├── Span: LLM Call (synthesis)
│   └── Span: Tool Call (format_output)
└── Metadata:
    ├── Total cost: $0.032
    ├── Total latency: 4.5s
    ├── Steps: 2
    └── Tokens: 8,400 input / 1,200 output
```

#### LangFuse Integration

```python
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse = Langfuse()

@observe()
def agent_step(query: str):
    """Decorated function creates a trace span automatically."""
    response = llm.generate(query)
    return response

@observe()
def run_agent(task: str):
    """Parent span groups all child spans into one trace."""
    plan = agent_step(f"Plan: {task}")
    result = agent_step(f"Execute: {plan}")
    return result
```

### Key Metrics to Track

| Category | Metric | Why It Matters |
|----------|--------|---------------|
| Cost | Total cost per trace | Budget management |
| Cost | Cost per step (mean, p50, p95) | Identify expensive steps |
| Cost | Cache hit rate | Cache effectiveness |
| Performance | Total latency (end-to-end) | User experience |
| Performance | LLM latency per call | Model speed |
| Performance | Tool call latency | External dependency health |
| Quality | Task completion rate | Agent effectiveness |
| Quality | Error rate by step | Find failing components |
| Quality | Human override rate | Confidence calibration |
| Reliability | Retry count per trace | Error handling effectiveness |
| Reliability | Timeout rate | Infrastructure issues |

### Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Error rate > 10% (5 min window) | High | Page on-call |
| p95 latency > 30s | Medium | Investigate, check external deps |
| Daily cost > 150% of budget | High | Throttle or pause non-critical agents |
| Cache hit rate < 30% | Low | Review caching configuration |
| Completion rate < 80% | Medium | Review recent changes, check evals |

### Structured Logging

Log structured data at each agent step for post-hoc analysis:

```typescript
interface AgentStepLog {
  traceId: string;
  stepIndex: number;
  timestamp: string;
  type: "llm_call" | "tool_call" | "decision" | "error";
  model?: string;
  inputTokens?: number;
  outputTokens?: number;
  cost?: number;
  latency: number;
  success: boolean;
  error?: string;
  metadata: Record<string, any>;
}
```

### A/B Testing Agents

Compare agent variants in production using trace data:

```
1. Deploy two agent variants (A: current, B: candidate)
2. Route traffic 90/10 (A/B)
3. Compare metrics: cost, latency, completion rate, quality score
4. Promote B if it outperforms on all critical metrics
5. Roll back if quality degrades
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No cost tracking | Budget overrun discovered in billing | Track cost per trace from day one |
| Using premium model for everything | 10x higher cost than necessary | Implement model routing by complexity |
| No prompt caching | Paying full price for identical prefixes | Enable caching, structure prompts for cache hits |
| Logging only final output | Cannot debug intermediate failures | Trace every LLM call and tool invocation |
| No token budget | Single runaway agent burns entire daily budget | Set per-task and per-step token limits |
| Alerting on averages only | Misses p95/p99 spikes | Alert on percentiles, not just means |
| No evaluation alongside observability | Can see what happened but not if it was correct | Connect traces to quality evaluations |
