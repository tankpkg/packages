# Tracing and Spans

Sources: Langfuse documentation, LangSmith documentation, Arize Phoenix documentation, Helicone docs, OpenTelemetry concepts, production LLM tracing practices

Covers: trace design, span boundaries, generations, metadata, prompt/model/version capture, correlation IDs, and practical debugging patterns for LLM systems.

## Trace the Full User Outcome, Not Just the Model Call

LLM observability becomes useful when one trace can explain why a user saw a result — including retrieval, prompt version, model choice, tool calls, and post-processing.

| Good trace scope | Bad trace scope |
|------------------|-----------------|
| user request → retrieval → generation → response | only raw model latency |
| prompt version + metadata + outcome | one disconnected completion log |

## Basic Span Structure

| Span type | Example |
|----------|---------|
| parent request span | one user or API request |
| retrieval span | vector search / DB lookup |
| generation span | model call |
| tool span | external tool or function execution |
| post-processing span | ranking, formatting, safety checks |

Good spans mirror the actual decision path of the system.

## Metadata You Should Always Capture

| Field | Why |
|------|-----|
| prompt version | compare changes over time |
| model/provider | quality/cost/latency analysis |
| token counts | budget and regression tracking |
| latency | user experience and bottlenecks |
| user/session/request ID | traceability |

## Correlation IDs

Use correlation IDs across app logs, traces, and downstream services so LLM debugging is connected to the wider system.

## Span Boundary Heuristics

1. create a span when work has a distinct latency or quality effect
2. avoid spans so tiny they create noise without decision value
3. separate retrieval, generation, and post-processing when they can fail independently

## Common Tracing Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| only tracing model call | misses root cause | trace pipeline end-to-end |
| no prompt version in spans | impossible regression attribution | capture prompt ID/version |
| huge unstructured metadata blobs | noisy dashboards | keep typed, intentional fields |

## Debugging Questions

1. Was the failure in retrieval, prompt, model, tool, or formatting?
2. Which prompt version and model produced the output?
3. Did cost or latency spike alongside quality drift?

## Parent/Child Trace Shape

| Parent span | Child spans |
|------------|-------------|
| user request | retrieval, rerank, generation, tool calls, formatter |
| batch eval run | per-example generation spans |
| agent workflow | planner, tool, retriever, final answer spans |

Parent spans should answer “what happened overall,” while child spans explain where time and quality moved.

## Metadata Design Rules

| Rule | Why |
|-----|-----|
| prefer typed fields over giant JSON blobs | easier filtering and dashboards |
| capture both model and provider | routing analysis |
| include prompt registry ID + version | rollback and regression attribution |
| tag feature or route name | cost/quality hotspot analysis |

## Prompt Capture Questions

1. Are you storing the exact prompt text or only a version reference?
2. Can you safely reconstruct the full rendered prompt later?
3. Are sensitive user inputs redacted where needed?

Prompt capture is essential, but so is data hygiene.

## Tool Call Tracing

| Concern | Recommendation |
|--------|----------------|
| tool input/output size | sample or summarize when huge |
| success/failure status | explicit field |
| retry count | capture for reliability analysis |

Tool spans should explain whether the agent failed because of reasoning, retrieval, or infrastructure.

## Retrieval Span Design

| Field | Why |
|------|-----|
| retriever type | compare strategies |
| top-k | retrieval tuning |
| latency | bottleneck detection |
| document IDs/chunk refs | reproducibility |

For RAG systems, retrieval spans are usually the difference between guesswork and root-cause clarity.

## Span Granularity Trade-offs

| Too coarse | Too fine |
|-----------|----------|
| root cause hidden | dashboards become noisy |
| one big generation span only | dozens of meaningless micro-spans |

Aim for spans that map to real decisions or latencies a human would care about.

## Correlation Across Systems

LLM traces should connect to your broader system observability.

| System | Correlation field |
|-------|-------------------|
| app request logs | request ID |
| background jobs | job/task ID |
| user analytics | session/user IDs where appropriate |
| provider invoices/cost exports | model/provider call metadata |

## Privacy and Redaction Notes

| Concern | Recommendation |
|--------|----------------|
| sensitive user data in prompts | redact or hash where possible |
| full document/chunk capture | store references when safer |
| tool outputs with secrets | sanitize before tracing |

Observability that leaks user or secret data is not a win.

## Common Trace Smells

| Smell | Why it matters |
|------|----------------|
| no feature tagging | cannot attribute costs or failures |
| prompt text stored but no version | weak release debugging |
| retrieval spans without doc IDs | poor reproducibility |
| missing user/session correlation | hard support triage |

## Span Review Checklist

1. Can one trace explain a bad user result?
2. Can you identify the exact prompt/model version involved?
3. Can you tell whether retrieval, model, or tools were to blame?
4. Can you connect this trace to broader system logs?

## Platform-Neutral Tracing Concepts

| Concept | Langfuse/LangSmith/etc. equivalent |
|--------|-------------------------------------|
| request trace | trace/run/session |
| generation span | generation/llm call |
| tool span | tool/run step |
| feedback/score | score/annotation/evaluation |

This shared conceptual model makes migration and comparison easier.

## Final Trace Discipline Notes

Tracing exists to answer questions quickly under pressure. If a trace cannot explain a bad user outcome, it is likely too shallow or too noisy.

## Input / Output Capture Questions

1. What exact prompt or prompt template rendered?
2. Which retrieved documents or tool outputs shaped the answer?
3. Which parts of the input/output should be redacted or summarized for safety?

Capturing everything blindly is not observability maturity. It is sometimes just liability.

## Trace Retention Questions

| Question | Why |
|---------|-----|
| how long should traces be stored? | cost and privacy |
| which traces need long retention? | incident and compliance needs |
| can payloads be summarized after triage value drops? | storage control |

## Multi-Step Agent Trace Model

| Step type | Example metadata |
|----------|------------------|
| planner step | intent, chosen tool path |
| retrieval step | source IDs, top-k, latency |
| tool step | tool name, success/failure, retries |
| final answer step | model, prompt version, output quality score |

Agentic systems especially need traces that expose intermediate decisions, not just the final completion.

## Trace Review Heuristics

| Heuristic | Why |
|----------|-----|
| every expensive span should justify itself | cost discipline |
| every low-quality output should map to a trace | debugging practicality |
| every production prompt should appear in traces by version | rollback clarity |

## Common Instrumentation Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| tracing the model call but not retrieval | root cause blindness |
| no structured metadata for feature or tenant | poor operational slicing |
| storing giant raw payloads where references would suffice | storage/privacy problems |

## Review Questions for New LLM Features

1. If this fails, what trace would explain it?
2. Which metadata field would tell you whether the prompt or model changed?
3. Would support or QA be able to use the trace without reading code?

## Trace Ownership Questions

| Question | Why |
|---------|-----|
| who defines span taxonomy? | consistency |
| who adds new feature metadata fields? | prevents drift |
| who decides retention and redaction? | privacy and cost |

## Observability Maturity Levels

| Level | Description |
|------|-------------|
| basic | one generation log with tokens and latency |
| intermediate | end-to-end traces with prompt version + retrieval |
| mature | traces linked to evals, feedback, cost dashboards, and release decisions |

## Final Tracing Questions

1. Could you explain yesterday’s worst output from trace data alone?
2. Could you compare two prompt versions using trace slices?
3. Could you isolate whether latency is retrieval-, tool-, or model-driven?

## Trace Taxonomy Smells

| Smell | Why it matters |
|------|----------------|
| every team invents its own span names | dashboards fragment |
| no version metadata on generation spans | regressions hard to attribute |
| no retrieval/tool separation | root cause guesswork |

## Tracing Review Questions

1. Can this trace explain a bad answer end to end?
2. Would an operator know which prompt/model/retrieval path changed?
3. Is the trace schema stable enough to support dashboards and regression analysis over time?

## Release Readiness Checklist

- [ ] traces cover the whole LLM decision path
- [ ] prompt version, model, tokens, and latency are captured
- [ ] correlation IDs connect LLM traces with system logs
- [ ] spans are meaningful enough to debug user-visible failures
