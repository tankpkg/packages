---
name: "@tank/llm-observability"
description: |
  Production LLM observability, evaluation, and prompt operations. Covers
  tracing and span design (Langfuse, LangSmith, Phoenix, Helicone), prompt
  versioning, dataset-driven evaluation, RAG evaluation, latency and cost
  monitoring, user feedback capture, regression detection, experiment design,
  dashboards, and practical production debugging for LLM systems.

  Synthesizes Langfuse documentation, LangSmith documentation, Arize Phoenix,
  Braintrust, DeepEval, RAGAS, OpenTelemetry-for-LLMs patterns, and production
  evaluation practices from 2024-2026.

  Trigger phrases: "llm observability", "langfuse", "langsmith",
  "llm evaluation", "prompt testing", "prompt versioning", "ragas",
  "deepeval", "llm monitoring", "ai evaluation", "trace llm calls",
  "llm cost tracking", "llm latency", "prompt regression", "llm dashboard"
---

# LLM Observability

## Core Philosophy

1. **Trace what matters, not everything blindly** — Good observability starts with meaningful spans, metadata, and outcomes, not a pile of noisy logs.
2. **Evaluation is part of the product loop** — Prompts, retrieval, latency, and cost should be measured as continuously as code regressions.
3. **Prompt changes need versioning and evidence** — Never ship prompt edits without a way to compare behavior, cost, and failure rate.
4. **Human feedback and automated scores complement each other** — Neither alone is enough for trustworthy LLM systems.
5. **Cost, latency, and quality trade off together** — A “better” prompt or model is not better if it wrecks budgets or user response time.

## Quick-Start: Common Problems

### "We can’t debug bad LLM outputs"

1. Trace request → retrieval → prompt → model → post-processing
2. Capture prompt version, model, latency, token usage, and user/session context
3. Log enough artifacts to reproduce failures safely
-> See `references/tracing-and-spans.md`

### "How do we evaluate prompt changes safely?"

| Need | Approach |
|------|----------|
| quick regression check | saved eval dataset + side-by-side scores |
| RAG quality check | retrieval + answer metrics |
| production rollout | prompt versioning + experiment comparison |
-> See `references/evaluation-and-regressions.md`

### "Costs are climbing fast"

1. Track tokens, latency, and model choice per route/use case
2. Compare prompt versions and model routing costs
3. Set budget alerts and route-level cost review
-> See `references/cost-latency-and-ops.md`

## Decision Trees

### Observability Platform Choice

| Signal | Recommendation |
|--------|----------------|
| prompt/version + tracing focus | Langfuse |
| LangChain-heavy stack and experiments | LangSmith |
| open-source tracing/eval focus | Phoenix |
| lightweight gateway-style monitoring | Helicone |

### Evaluation Strategy

| Signal | Use |
|--------|-----|
| deterministic task with clear labels | dataset + exact/assertive metrics |
| subjective generation quality | rubric or model-graded evals |
| RAG system | retrieval metrics + answer quality metrics |

## Reference Index

| File | Contents |
|------|----------|
| `references/tracing-and-spans.md` | Trace design, spans, generations, metadata, correlation IDs, prompt/model/version capture |
| `references/evaluation-and-regressions.md` | datasets, prompt experiments, regression gates, RAGAS/DeepEval-style thinking, score interpretation |
| `references/prompt-versioning-and-feedback.md` | prompt registries, version promotion, human feedback capture, annotation workflows |
| `references/cost-latency-and-ops.md` | token/cost tracking, latency budgets, routing decisions, production dashboards, alerts |
| `references/platform-selection.md` | Langfuse, LangSmith, Phoenix, Helicone, Braintrust trade-offs and deployment patterns |
