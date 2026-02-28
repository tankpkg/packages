# Cost Optimization

Sources: Huyen (AI Engineering, ch. 9–10), Brousseau & Sharp (LLMs in Production), 2025–2026 production benchmarks (Reddit LLMDevs, Redis, Pluralsight)

Covers: cost drivers, model routing, caching strategies, token optimization, batching, cost attribution.

## Understanding LLM Cost Drivers

LLM API costs have two primary components. Understanding both is required before optimizing either.

| Component | Pricing Model | Optimization Lever |
|-----------|--------------|-------------------|
| Input tokens | Per token (prompt + context) | Compress prompts; cache prefixes |
| Output tokens | Per token (generated) | Constrain output length; stream to avoid regeneration |
| Model tier | Per-model price multiplier | Route by complexity |
| Inference infrastructure | Fixed or per-GPU-hour (self-hosted) | Batching, quantization |

**Input vs output cost**: Output tokens cost 3–5× more per token than input tokens on most providers. Controlling output length matters more than trimming prompts.

### Cost at Scale Example

A production service handling 100K requests/day with average 2K input + 500 output tokens:
- At GPT-4o pricing (~$2.50/1M input, ~$10/1M output): ~$1,000/day
- Model routing to gpt-4o-mini for 70% of requests: ~$250/day
- Adding semantic caching with 40% hit rate: ~$150/day

Systematic optimization commonly achieves 60–80% cost reduction without quality loss.

## Model Routing

Route each request to the lowest-cost model capable of handling it correctly.

### Three-Tier Routing Pattern

```
Request arrives
    → Classify complexity (fast, cheap classifier)
    → Route:
        Simple (factual lookup, classification, summarization)
            → Small model  (~$0.15/1M tokens)
        Standard (reasoning, extraction, drafting)
            → Mid model    (~$0.50–$2.50/1M tokens)
        Complex (multi-step reasoning, code, analysis)
            → Large model  (~$10–$30/1M tokens)
```

### Complexity Classification

| Signal | Tier | Rationale |
|--------|------|-----------|
| Short prompt (< 200 tokens) + factual query | Small | Low reasoning demand |
| Template-based extraction with clear schema | Small/Mid | Structured, constrained |
| Multi-step reasoning required | Large | Context-heavy |
| Code generation or debugging | Large | High precision required |
| Creative generation | Mid/Large | Quality-sensitive |
| Simple yes/no classification | Small | Binary output |

Build the classifier as a lightweight rule system first. Upgrade to an ML classifier if rule accuracy falls below 90%.

### Escalation Pattern

```
result = small_model.generate(request)
if result.confidence < threshold or result.contains_uncertainty:
    result = large_model.generate(request)
    log(escalation=true, reason=result.low_confidence)
```

Track escalation rate in production. High escalation rate signals the classifier is misrouting.

## Caching Strategies

Caching is the highest-leverage cost optimization. A 40% cache hit rate cuts costs by 40% before touching model routing or token optimization.

### Cache Type Comparison

| Type | Hit Condition | Hit Rate | Setup Cost | Use When |
|------|--------------|----------|------------|----------|
| Exact match | Identical prompt + params | Low (5–15%) | Trivial | FAQ chatbots, fixed templates |
| Semantic | Query semantically similar | Medium (20–40%) | Medium | User queries, search |
| Prompt prefix | Shared system prompt prefix | High (50–90%) | Low | Apps with large system prompts |

### Exact Match Cache

Store hash(prompt + model + params) → response. Effective for:
- Repeated identical API calls in development/testing
- High-traffic FAQ bots where users ask the same questions
- Template-rendered prompts (same template, same values)

```
cache_key = hash(model + temperature + messages + tools)
cached = redis.get(cache_key)
if cached: return cached

response = llm.generate(...)
redis.set(cache_key, response, ttl=3600)
return response
```

### Semantic Cache

Store embedding(prompt) → (response, embedding). On new request, find the stored embedding most similar to the new query. If similarity > threshold (e.g., 0.95), return cached response.

```
query_embedding = embed(user_query)
nearest = vector_db.search(query_embedding, k=1)

if nearest.similarity > 0.95:
    log(cache_hit=semantic, similarity=nearest.similarity)
    return nearest.cached_response

response = llm.generate(user_query)
vector_db.insert(query_embedding, response)
return response
```

Hit rate: 20–40% in production for conversational queries. Similarity threshold is the key tuning parameter — lower threshold increases hits but risks serving stale/wrong responses.

### Prompt Prefix Caching (Provider-Side)

Anthropic and OpenAI support server-side caching of prompt prefixes. Mark stable prefixes (system prompt, large context documents) as cacheable. The provider caches the KV state; subsequent requests using the same prefix skip recomputation.

```
messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": large_system_prompt, "cache_control": {"type": "ephemeral"}}]
    },
    {"role": "user", "content": user_message}
]
```

Cost reduction: 60–90% on input tokens for the cached prefix. Effective when:
- System prompt is > 1000 tokens
- Large reference documents are included in every request
- Multi-turn conversations reuse conversation history

## Token Optimization

Reducing token count reduces both cost and latency (fewer tokens = faster generation).

### System Prompt Compression

| Technique | Token Reduction | Risk |
|-----------|----------------|------|
| Remove redundant instructions | 10–30% | Low |
| Eliminate examples that aren't improving quality | 20–40% | Medium |
| Replace prose with structured lists | 5–15% | Low |
| Compress few-shot examples to minimal form | 30–50% | Medium |

Measure quality impact of each compression. A/B test before deploying.

### Context Window Management

For multi-turn conversations, context grows unboundedly. Options:

| Strategy | Approach | Trade-off |
|----------|----------|-----------|
| Fixed window | Keep last N turns | Loses early context |
| Summary compression | Summarize old turns with LLM | Extra cost; lossy |
| Selective retention | Keep turns with key facts; discard small talk | Requires relevance scoring |
| Message importance scoring | Weight turns by recency + user importance signals | Complex |

```
# Simple sliding window
context = conversation_history[-10:]  # keep last 10 turns

# Summary compression
if len(conversation_history) > 20:
    summary = llm.summarize(conversation_history[:-10])
    context = [summary_message(summary)] + conversation_history[-10:]
```

### Output Token Control

| Method | Effect |
|--------|--------|
| `max_tokens` parameter | Hard cap on output length |
| Explicit length instruction in prompt | Soft guidance ("respond in 2–3 sentences") |
| Structured output (constrained fields) | Output length bounded by schema |
| Few-shot examples with target length | Model learns expected response length |

Set max_tokens to 20% above expected output length. Setting it too tight causes truncation.

## Batching

For async workloads (data pipelines, background processing), batching reduces per-request overhead.

| Batch Strategy | When | Benefit |
|----------------|------|---------|
| Request batching (multiple users) | High throughput, latency-tolerant | Higher GPU utilization |
| Document batching (one user) | Processing many docs | Amortized overhead |
| Embedding batching | Large-scale indexing | 10–50× throughput vs one-by-one |

```
# Embed in batches, not one document at a time
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    embeddings = embed_batch(batch)  # single API call for 100 docs
    store(embeddings)
```

Provider rate limits affect batch size — stay within tokens-per-minute limits.

## Cost Attribution

Without attribution, you cannot optimize. You need to know which features, users, or request types drive cost.

### Attribution Dimensions

| Dimension | Instrumentation |
|-----------|----------------|
| Feature | Tag requests with `feature_id` |
| User/tenant | Tag requests with `tenant_id` |
| Model | Log which model served each request |
| Request type | Tag with `prompt_template_id` |
| Cache outcome | Log `cache_hit` = true/false/type |

### Metrics to Track

| Metric | Why |
|--------|-----|
| Tokens per request (input + output) | Identify token-heavy features |
| Cost per request | Unit economics |
| Cache hit rate by type | Measure caching effectiveness |
| Escalation rate | Measure routing classifier accuracy |
| Cost by feature | Identify cost drivers |
| Monthly cost trend | Detect regressions before bill arrives |

### Cost Budget Alerts

Set spend alerts at 50%, 75%, and 90% of monthly budget. A single feature bug (infinite retry loop, missing cache key) can generate 10–100× normal spend in hours.

## Optimization Sequence

Apply in order — each builds on the previous:

```
1. Prompt prefix caching       → 60–90% reduction on cached prefixes
2. Model routing               → 20–60% reduction on routed traffic  
3. Semantic caching            → 20–40% reduction on repeated queries
4. Token compression           → 10–30% reduction across all requests
5. Output length control       → 10–20% reduction on verbose outputs
6. Batching (async only)       → Throughput gain, not direct cost reduction
```

Do not start with batching or token compression. Start with caching and routing — both have the highest leverage and lowest quality risk.

## Cost Optimization Checklist

- [ ] Cost attribution in place (by feature, user, model)
- [ ] Spend alerts configured at 50/75/90% of monthly budget
- [ ] Model routing implemented with complexity classifier
- [ ] Escalation rate tracked; < 15% considered healthy
- [ ] Prompt prefix caching enabled for system prompts > 1000 tokens
- [ ] Semantic cache deployed for user-facing query endpoints
- [ ] Cache hit rate tracked separately by cache type
- [ ] Max_tokens set on all requests (prevents runaway output)
- [ ] Context window managed for multi-turn conversations
- [ ] Baseline cost per feature established before optimization
