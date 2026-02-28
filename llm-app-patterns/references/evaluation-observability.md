# Evaluation and Observability

Sources: Huyen (AI Engineering, ch. 3–4, 10), Brousseau & Sharp (LLMs in Production), Pydantic Evals documentation analysis, RAGAS framework documentation analysis, 2025–2026 production patterns

Covers: evaluation methodology, LLM-as-judge, RAG evaluation, golden datasets, production monitoring, tracing, feedback loops.

## Why Evaluation Is the Hard Part

LLM applications fail in ways traditional software does not:
- Correct code produces wrong answers
- The same prompt produces different outputs at different times
- Quality degrades when prompts are updated upstream
- Failures are semantic, not syntactic — no stack trace

Without evaluation infrastructure, you are shipping blind. Every prompt change is a regression risk you cannot detect.

## Evaluation Methodology

### Three-Layer Framework

| Layer | Approach | When to Use |
|-------|----------|-------------|
| Functional correctness | Deterministic code checks | Schema validation, format compliance |
| Similarity metrics | BLEU, ROUGE, semantic similarity | Translation, summarization with reference |
| Semantic quality | LLM-as-judge | Open-ended tasks; when correctness is subjective |

Apply layers cheapest-first. Run schema validation before LLM-as-judge. A response that fails schema validation does not need an expensive semantic quality check.

### Evaluation Granularity

Evaluate at three levels:

```
System level:    End-to-end quality (does the app do its job?)
Component level: Each pipeline stage (retrieval, generation, routing)
Prompt level:    Each template variant (A/B test prompt changes)
```

Only system-level evaluation reveals emergent failures. Only component-level evaluation reveals where to fix them.

## Human vs Automated Evaluation

| Approach | Scalability | Accuracy | Use For |
|----------|-------------|----------|---------|
| Human annotation | Low (expensive) | High (ground truth) | Calibrating judges; golden dataset creation |
| Rule-based automated | High | Medium (brittle to edge cases) | Schema, format, length checks |
| LLM-as-judge | High | Medium-High | Semantic quality, open-ended tasks |
| Specialized model | High | High for specific task | Code correctness, factual accuracy |

Use human evaluation to create the golden dataset. Use automated evaluation for ongoing regression testing.

## LLM-as-Judge

Use a strong LLM to evaluate another LLM's output. Effective for tasks where correctness is context-dependent or subjective.

### Judge Prompt Pattern

```
System: You are an evaluator assessing response quality.
        Score the response on the criterion below.
        Return JSON: {"score": 1-5, "reasoning": "one sentence"}
        Do not let response length influence your score.

User:
    Criterion: Faithfulness — does the response contain only
               information present in the provided context?

    Context: {retrieved_chunks}
    Question: {user_query}
    Response: {llm_response}

    Score 1-5 where:
    1 = Contains significant hallucinations
    3 = Mostly faithful, minor unsubstantiated claims
    5 = Fully grounded in the provided context
```

### Judge Configuration Rules

| Rule | Rationale |
|------|-----------|
| Request reasoning alongside score | Enables debugging failed cases |
| Evaluate one criterion per call | Multi-criterion prompts produce inconsistent scores |
| Use stronger model than the one being evaluated | Judge must exceed the model's capability |
| Align judge with human labels before deploying | Misaligned judge produces misleading metrics |
| Randomize response position in comparative eval | Position bias: models favor first/last response |

### Judge Alignment Process

Before using LLM-as-judge in production:

```
1. Collect 100 labeled examples (human annotated)
2. Run judge on the same examples
3. Compute judge–human agreement (Cohen's kappa or accuracy)
4. Identify disagreement patterns (where does judge fail?)
5. Refine judge prompt to address disagreements
6. Repeat until agreement > 0.7 (substantial) or 0.8 (strong)
```

Target 80%+ agreement between judge and human labels before trusting the judge for regression testing.

## RAG-Specific Evaluation

Evaluate RAG in two stages: retrieval quality and generation quality. A perfect generator cannot compensate for poor retrieval.

### Retrieval Metrics

| Metric | Definition | Compute Without Golden Labels? |
|--------|------------|-------------------------------|
| Context Relevance | Fraction of retrieved chunks relevant to the query | Yes — LLM judge per chunk |
| Context Recall | Fraction of needed information that was retrieved | No — requires golden context |
| Context Precision | Fraction of retrieved chunks that were actually used in the answer | Partial |

### Generation Metrics

| Metric | Definition | Compute Without Golden Labels? |
|--------|------------|-------------------------------|
| Faithfulness | Answer uses only retrieved context (no hallucination) | Yes — LLM checks each claim |
| Answer Relevance | Answer addresses the actual question asked | Yes — LLM judge |
| Answer Correctness | Answer matches known-correct answer | No — requires golden answer |

**Minimal viable eval set**: Start with faithfulness + answer relevance. Both use LLM-as-judge and require no pre-labeled data. Add answer correctness when building a curated golden set.

### Faithfulness Check Pattern

```
for each claim in llm_response:
    prompt = "Is this claim supported by the provided context?
              Context: {retrieved_chunks}
              Claim: {claim}
              Answer: yes / no / partially"
    result = judge.evaluate(prompt)

faithfulness_score = count(yes) / total_claims
```

## Golden Datasets

### Construction

A golden dataset is a curated set of (input, expected_output) pairs used for regression testing.

```
Golden dataset structure:
{
    "id":           unique identifier,
    "input":        {user_query, context, conversation_history},
    "expected":     {answer, key_points, must_include, must_exclude},
    "difficulty":   "easy" | "medium" | "hard",
    "category":     "factual" | "reasoning" | "multi-hop" | "refusal",
    "source":       "user_feedback" | "expert_annotation" | "adversarial"
}
```

### Dataset Sources (Priority Order)

| Source | Quality | Volume | Process |
|--------|---------|--------|---------|
| Failed production cases | High | Low | Review user complaints → curate |
| Expert annotation | Highest | Low | Expensive; use for calibration |
| User feedback (thumbs down) | High | Medium | Convert ratings → labeled cases |
| AI-generated + human reviewed | Medium | High | Generate diverse, review all |
| Adversarial (red team) | High | Low | Test boundary/refusal behavior |

### Target Dataset Size

| Purpose | Minimum | Target |
|---------|---------|--------|
| Initial quality baseline | 50 | 200 |
| Regression testing | 100 | 500 |
| Fine-tuning evaluation | 500 | 2000+ |

Prioritize quality over quantity. Fifty well-labeled examples beat 500 poorly labeled ones.

## Production Monitoring

Monitoring catches regressions that evaluation misses. Evaluation runs before deployment; monitoring runs after.

### What to Monitor

| Signal | Metric | Alert Threshold |
|--------|--------|----------------|
| Response quality | Average judge score | Drop > 5% from baseline |
| Latency | P50, P95, P99 per pipeline stage | P99 > 2× P50 |
| Error rate | Failed requests / total | > 1% |
| Cost | Tokens per request, $ per request | > 20% increase |
| Cache hit rate | Hits / total | Drop > 10% |
| Retrieval quality | Context relevance score | Drop > 10% |

### Trace Structure

Log one trace per request. Each trace spans the full pipeline.

```
Trace:
    trace_id:        UUID
    user_id:         anonymized
    timestamp:       ISO 8601
    total_latency_ms: end-to-end time

    Spans:
        - name: "retrieval"
          latency_ms: 80
          retrieved_chunks: 5
          context_relevance: 0.82
        - name: "generation"
          latency_ms: 1200
          model: "claude-3-5-sonnet"
          input_tokens: 2400
          output_tokens: 350
          cost_usd: 0.0094
        - name: "judge_evaluation"
          latency_ms: 450
          faithfulness: 0.95
          answer_relevance: 0.88
```

Store traces in a searchable backend (LangSmith, Langfuse, Honeycomb, or custom). Sample 100% in development; 10–20% in high-volume production.

## User Feedback Loops

Structured user feedback is the highest-quality signal. Convert every negative signal into an evaluation case.

### Feedback Signal Types

| Signal | Quality | Collection Method |
|--------|---------|------------------|
| Thumbs down / explicit reject | High | Explicit UI action |
| Edited response | High | Detect post-generation edits |
| Retry / regenerate | Medium | Detected from session behavior |
| Session abandonment | Low | Inferred from session end |
| Explicit rating (1–5) | Highest | Rare; adds UI friction |

### Feedback → Test Case Pipeline

```
User submits thumbs down
    → Log: {session_id, message_id, user_id, timestamp}
    → Async job: retrieve trace for message_id
    → Queue for human review
    → Human labels: {is_failure: bool, failure_category, correct_response}
    → If is_failure: add to golden_dataset
```

Even 10 labeled failures per week compound quickly. 50 weeks = 500 test cases without a formal annotation project.

## Evaluation Pipeline Design

### Pre-Deployment (Offline)

```
Pull latest golden dataset
→ Run candidate model/prompt against all examples
→ Compute metrics (faithfulness, answer relevance, correctness)
→ Compare to baseline (previous passing version)
→ Gate: merge only if no metric degrades > 5%
```

### Post-Deployment (Online)

```
Production traffic (sampled 10%)
→ LLM judge evaluates each sampled response
→ Aggregate into daily metric report
→ Alert if rolling 7-day average drops below threshold
→ Failed cases queued for golden dataset review
```

### Evaluation Cadence

| Event | Evaluation Action |
|-------|-------------------|
| Prompt change | Full offline eval against golden dataset |
| Model version change | Full offline eval + 24h online monitoring |
| Weekly | Review online metrics; review failed cases |
| Monthly | Add new cases to golden dataset; re-baseline |

## Observability Stack Options

| Tool | Type | Best For |
|------|------|----------|
| LangSmith | Managed (LangChain) | LangChain-based apps; trace visualization |
| Langfuse | Open source / managed | Multi-framework; cost tracking; self-hostable |
| Phoenix (Arize) | Open source | Model debugging; embedding visualization |
| Weights & Biases (Weave) | Managed | Teams already using W&B |
| Custom (OpenTelemetry) | DIY | Full control; no vendor lock-in |

Instrument with OpenTelemetry-compatible spans regardless of backend. Swap backends without code changes.
