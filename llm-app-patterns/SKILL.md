---
name: llm-app-patterns
description: |
  Build production-grade LLM-powered applications — RAG systems, tool-using
  agents, structured output extraction, streaming responses, and cost
  optimization. Covers the full engineering stack for apps built on top of
  foundation models, not model training. Synthesizes Huyen (AI Engineering),
  Brousseau & Sharp (LLMs in Production), Bouchard & Peters (Building LLMs for
  Production), Lanham (AI Agents in Action), Arsanjani & Bustos (Agentic
  Architectural Patterns), Rothman (RAG-Driven Generative AI).

  Trigger phrases: "RAG", "retrieval-augmented generation", "vector search",
  "chunking strategy", "embedding", "reranking", "hybrid search", "tool use",
  "function calling", "tool calling", "agent", "agentic", "multi-agent",
  "orchestrator", "structured output", "JSON mode", "Instructor", "Pydantic",
  "streaming", "server-sent events", "SSE", "token streaming", "LLM cost",
  "model routing", "semantic cache", "prompt caching", "LLM evaluation",
  "LLM-as-judge", "RAGAS", "hallucination", "faithfulness", "golden dataset",
  "LLM in production", "LLMOps", "build with LLMs", "LLM application"
---

# LLM App Patterns

## Core Philosophy

1. **Retrieval quality is a ceiling on generation quality** — No prompt engineering
   compensates for bad RAG. Fix retrieval before tuning prompts.
2. **Workflows beat agents for predictability** — Use agents only when the execution
   path is genuinely unknown at design time. Everything else should be code.
3. **Measure before optimizing** — Add cost attribution and eval metrics first.
   Optimization without measurement is guessing.
4. **Schema failures cascade** — Unstructured LLM output is a reliability tax.
   Constrain output at the token level; don't parse free text.
5. **Stream by default** — Token streaming is the lowest-effort UX improvement
   for any LLM interface. Users read while the model generates.

## Quick-Start: Common Problems

### "My RAG system gives wrong answers"

1. Measure faithfulness first — are answers grounded in retrieved context?
   -> See `references/evaluation-observability.md` (Faithfulness Check Pattern)
2. Check retrieval quality — are the right chunks being retrieved?
   -> See `references/rag-patterns.md` (RAG Evaluation Metrics)
3. Fix the pipeline stage that is failing; do not tune prompts to mask retrieval failures.

### "I need structured data from LLM output"

1. Choose the right method (native structured outputs vs Instructor vs JSON mode).
   -> See `references/structured-output.md` (Method Comparison)
2. Design schemas for LLMs — use enums, Field descriptions, explicit bounds.
   -> See `references/structured-output.md` (Schema Design for LLMs)
3. Add retry logic with error context; LLMs correct mistakes when shown them.

### "The app feels slow"

1. Enable token streaming immediately — reduces perceived latency to time-to-first-token.
   -> See `references/streaming.md` (Server Implementation Pattern)
2. Check proxy buffering — nginx/Cloudflare often buffer SSE by default.
   -> See `references/streaming.md` (Proxy Buffering table)
3. For actual latency: profile per pipeline stage; retrieval and reranking are often the bottleneck.

### "LLM API costs are too high"

1. Implement prompt prefix caching first (60–90% reduction on large system prompts).
   -> See `references/cost-optimization.md` (Prompt Prefix Caching)
2. Add model routing — route simple requests to small models.
   -> See `references/cost-optimization.md` (Three-Tier Routing Pattern)
3. Add semantic caching for user-facing query endpoints.
   -> See `references/cost-optimization.md` (Semantic Cache)

### "My agent loops, hallucinates tools, or gets stuck"

1. Implement loop detection — break on repeated (tool, args) pairs.
   -> See `references/tool-use-agents.md` (Loop Detection)
2. Set max_steps — always cap the ReAct loop.
   -> See `references/tool-use-agents.md` (Max Steps Guard)
3. Improve tool descriptions — models select tools by description, not name.
   -> See `references/tool-use-agents.md` (Tool Design Principles)

## Decision Trees

### RAG vs Fine-Tuning vs Prompting

| Goal | Use |
|------|-----|
| Answer questions from private documents | RAG |
| Knowledge changes frequently | RAG |
| Style or tone adaptation | Fine-tuning |
| Specialized task format | Fine-tuning |
| Task is well-served by base model | Prompt engineering |
| Latency critical (< 200ms) | Fine-tuning or prompt-only |

### Agent vs Workflow

| Signal | Use |
|--------|-----|
| Execution path is known at design time | Workflow (code) |
| Actions are irreversible | Workflow + explicit human gates |
| Task is exploratory, path unknown | Agent (ReAct) |
| Multiple specialized subtasks | Multi-agent orchestration |
| Quality over speed | Generator-Critic pattern |

### Structured Output Method

| Need | Method |
|------|--------|
| Prototyping, flexible schema | JSON mode |
| Single provider, guaranteed schema | Native structured outputs |
| Multi-provider, retry, type safety | Instructor + Pydantic |
| Streaming + incremental rendering | Instructor Partial |

### Streaming Transport

| Need | Use |
|------|-----|
| Token delivery, no user interruption | SSE (Server-Sent Events) |
| Bidirectional (user sends mid-stream) | WebSocket |
| Short responses (< 50 tokens) | Regular HTTP (no streaming) |
| Serverless (Vercel, Cloudflare) | Edge runtime + SSE |

## Evaluation Minimum Viable Setup

Before shipping any LLM feature to production:

1. Run faithfulness and answer relevance on 50 examples (no golden labels needed).
   -> `references/evaluation-observability.md`
2. Add traces: log input, output, latency, token count per request.
3. Set up one judge metric as a regression gate in CI.
4. Collect failed cases from user feedback → build golden dataset over time.

## Reference Files

| File | Contents |
|------|----------|
| `references/rag-patterns.md` | RAG architecture, chunking strategy selection, embedding models, hybrid search, reranking, HyDE, multi-query, GraphRAG, RAGAS evaluation metrics |
| `references/tool-use-agents.md` | Tool design, function calling loop, parallel execution, error recovery, agent spectrum, multi-agent patterns, planning strategies, failure modes |
| `references/structured-output.md` | JSON mode vs structured outputs vs Instructor, Pydantic schema design, retry logic, partial parsing, validation pipelines |
| `references/streaming.md` | SSE transport, server implementation, client consumption (EventSource + fetch), tool call streaming, backpressure, error handling, UX patterns |
| `references/cost-optimization.md` | Cost drivers, model routing, exact/semantic/prefix caching, token compression, context management, batching, cost attribution |
| `references/evaluation-observability.md` | Eval methodology, LLM-as-judge, judge alignment, RAG metrics, golden datasets, production monitoring, tracing, feedback loops |
