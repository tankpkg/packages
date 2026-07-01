---
name: "@tank/ai-agent-patterns"
description: |
  Design and build AI agents for production. Covers agent architecture
  selection (ReAct, Plan-and-Execute, Reflexion, LATS), tool calling
  patterns (structured output, parallel calls, error recovery), multi-agent
  orchestration (supervisor, hierarchical teams, swarm), memory systems
  (sliding window, semantic, episodic, working memory), human-in-the-loop
  (approval gates, interrupts, review cycles), guardrails and safety,
  cost optimization (model routing, caching, token budgets), observability
  (LangFuse, LangSmith, tracing), evaluation and testing, and production
  deployment patterns. Framework-specific guidance for LangGraph (TypeScript
  and Python), CrewAI, Mastra, OpenAI Agents SDK, and Anthropic tool use.

  Synthesizes Yao et al. (ReAct, 2022), Shinn et al. (Reflexion, 2023),
  Anthropic (Building Effective Agents, 2024), OpenAI (Agents Best Practices,
  2025), LangGraph documentation, CrewAI documentation, Mastra documentation,
  and production agent architecture research (2024-2026).

  Trigger phrases: "AI agent", "build AI agent", "agent architecture",
  "ReAct pattern", "plan and execute", "Reflexion", "LangGraph",
  "CrewAI", "Mastra", "multi-agent", "agent orchestration",
  "agent memory", "tool calling", "human in the loop",
  "agent patterns", "agent observability", "agent evaluation",
  "model routing", "agent guardrails", "structured output",
  "agent cost optimization", "agent deployment", "agentic workflow"
---

# AI Agent Patterns

## Core Philosophy

1. **Start simple, add complexity only when measured** — Begin with a single ReAct loop. Add planning, reflection, or multi-agent orchestration only when evaluation shows the simpler pattern failing. Anthropic's #1 finding: the most successful agent builders resist unnecessary complexity.
2. **Tools over prompts** — Invest more time in tool definitions than prompt engineering. Well-specified tools with clear schemas, examples, and error messages outperform clever prompts. The tool is the agent's interface to the world.
3. **Architecture determines cost, reliability, and scaling** — A ReAct agent makes 5-7 LLM calls per task; Plan-and-Execute often cuts this to 3-4. Wrong architecture choice compounds across thousands of requests. Choose based on workload, not hype.
4. **Memory is not one thing** — Agents need multiple memory systems: sliding window for conversation, working memory for current task state, semantic memory for long-term knowledge, episodic memory for past experiences. Each serves a different retrieval need.
5. **Evaluate before shipping** — Agent performance drops 58% between single execution and eight consecutive runs. Without evaluation infrastructure, model upgrades take weeks instead of days. Build evals first.

## Quick-Start: Common Problems

### "Which agent architecture should I use?"

| Workload | Architecture |
|----------|-------------|
| Tool-heavy, single domain, dynamic | ReAct |
| Structured multi-step, predictable | Plan-and-Execute |
| Quality-critical, self-improvement needed | Reflexion |
| Complex search/exploration space | LATS |
| Multiple specialized domains | Multi-agent (supervisor) |
| Simple classification/extraction | Single LLM call (no agent needed) |

-> See `references/architectures.md`

### "How do I add tools to my agent?"

1. Define tools with JSON Schema — name, description, parameters, required fields
2. Include 2-3 examples in the tool description showing expected input/output
3. Handle errors explicitly — return structured error messages, not exceptions
4. Use `tool_choice` to force tool use when the task always requires a specific tool
-> See `references/tool-calling.md`

### "My agent is too expensive"

1. Route simple tasks to fast/cheap models, complex tasks to capable models
2. Enable prompt caching (Anthropic: automatic, OpenAI: structured prefix)
3. Set token budgets per agent step — fail fast instead of burning tokens
4. Cache tool results for deterministic operations
-> See `references/cost-and-observability.md`

### "I need multiple agents working together"

1. Start with supervisor pattern — one router, specialized workers
2. Use sequential chains when each agent builds on previous output
3. Use parallel dispatch when agents analyze independent factors
4. Avoid full mesh communication — it scales quadratically
-> See `references/multi-agent.md`

### "My agent needs to remember across sessions"

1. Start with sliding window + smart summarization (baseline)
2. Add semantic memory (vector store) for cross-session knowledge
3. Add episodic memory for learning from past experiences
4. Run consolidation between sessions to merge duplicates and decay unused memories
-> See `references/memory-systems.md`

## Decision Trees

### Architecture Selection

| Signal | Use |
|--------|-----|
| Dynamic tool use, single domain | ReAct |
| Predictable steps, efficiency matters | Plan-and-Execute |
| Quality improvement through self-critique | Reflexion (2-3x token cost) |
| Need to explore multiple solution paths | LATS |
| Task decomposable into independent subtasks | Multi-agent parallel |
| Need domain specialists with routing | Multi-agent supervisor |
| Deterministic extraction or classification | No agent — single LLM call |

### Framework Selection

| Requirement | Framework |
|-------------|-----------|
| Maximum control, state graphs, TypeScript or Python | LangGraph |
| Role-based crews, rapid prototyping, Python | CrewAI |
| TypeScript-native, workflow engine, integrations | Mastra |
| OpenAI models, hosted infrastructure | OpenAI Agents SDK |
| Vendor-agnostic, enterprise | Semantic Kernel |

### Memory System Selection

| Need | Pattern |
|------|---------|
| Conversation continuity | Sliding window + summarization |
| Current task tracking | Working memory (structured scratchpad) |
| Cross-session knowledge | Semantic memory (vector store) |
| Learning from past tasks | Episodic memory |
| All of the above | Unified memory manager |

## Reference Index

| File | Contents |
|------|----------|
| `references/architectures.md` | ReAct, Plan-and-Execute, Reflexion, LATS, REWOO, architecture selection, trade-offs, implementation patterns |
| `references/tool-calling.md` | Tool schemas, structured output, parallel calls, error handling, MCP, tool selection patterns across providers |
| `references/multi-agent.md` | Supervisor, hierarchical teams, sequential chains, parallel dispatch, swarm, CrewAI crews, debate patterns |
| `references/memory-systems.md` | Sliding window, semantic memory, episodic memory, working memory, consolidation, unified manager, persistence |
| `references/human-in-the-loop.md` | Approval gates, interrupts, review cycles, escalation, confidence thresholds, LangGraph interrupts |
| `references/frameworks.md` | LangGraph (TS/Python), CrewAI, Mastra, OpenAI Agents SDK, Semantic Kernel, framework comparison and migration |
| `references/cost-and-observability.md` | Model routing, prompt caching, token budgets, LangFuse, LangSmith, tracing, latency monitoring, cost tracking |
| `references/evaluation-and-testing.md` | Trajectory evaluation, deterministic testing, mock tools, regression testing, benchmarks, CI/CD for agents |
| `references/guardrails-and-safety.md` | Input validation, output filtering, PII detection, hallucination mitigation, content policies, rate limiting |
