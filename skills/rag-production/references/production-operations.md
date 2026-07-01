# Production Operations

Sources: LangChain production deployment documentation, Pinecone operational guides, OpenAI rate limiting documentation, Vercel AI SDK streaming documentation, 2024-2026 RAG production engineering research

Covers: caching architecture, streaming responses, cost optimization, monitoring, ingestion pipelines, scaling patterns, and operational runbooks.

## Caching Architecture

Caching is the highest-impact cost optimization for RAG. A well-designed cache reduces embedding costs by 70-90%, retrieval costs by 50-80%, and generation costs by 20-40%.

### Four Cache Layers

```
Query → [Layer 1: Response Cache] → cached answer (fastest, least safe)
     → [Layer 2: Retrieval Cache]  → cached chunk IDs (fast, moderately safe)
     → [Layer 3: Rerank Cache]     → cached reranked results (medium)
     → [Layer 4: Embedding Cache]  → cached vectors (safest, most stable)
```

### Layer Details

| Layer | Cache Key | TTL | Hit Rate | Correctness Risk |
|-------|-----------|-----|----------|-----------------|
| Embedding (document) | content_hash | 30 days | 95%+ | Very low (content-addressed) |
| Embedding (query) | normalized_query + model_id | 1-24 hours | 40-60% | Low |
| Retrieval | query_hash + filter_hash + index_version | 5-60 min | 30-50% | Medium (stale docs) |
| Rerank | query_hash + candidate_set_hash | 1-4 hours | 20-40% | Low |
| Full response | query_hash + context_hash + prompt_version | 5-15 min | 10-30% | High (use cautiously) |

### Embedding Cache Implementation

```python
import hashlib
import redis
import json

redis_client = redis.Redis(host="localhost", port=6379, db=0)

def get_or_compute_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    cache_key = f"emb:{model}:{hashlib.sha256(text.encode()).hexdigest()}"
    
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    embedding = openai_client.embeddings.create(model=model, input=text).data[0].embedding
    redis_client.setex(cache_key, 86400 * 30, json.dumps(embedding))  # 30-day TTL
    return embedding
```

### Cache Invalidation

TTL-only caching ships stale answers. Use multi-pronged invalidation:

| Trigger | Action |
|---------|--------|
| Document updated | Invalidate embedding + retrieval cache for affected doc IDs |
| Prompt template changed | Invalidate all response caches (new prompt version key) |
| Index rebuilt | Invalidate retrieval + rerank caches (new index version key) |
| Model changed | Invalidate all caches for old model |

```python
def invalidate_on_doc_update(doc_id: str):
    # Invalidate embedding cache for this document's chunks
    for chunk_hash in get_chunk_hashes(doc_id):
        redis_client.delete(f"emb:*:{chunk_hash}")
    
    # Invalidate all retrieval caches (broad, but safe)
    pattern = f"retrieval:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
```

## Streaming Responses

Stream generated text to the user while it is being produced. Reduces perceived latency from seconds to milliseconds for first token.

### Vercel AI SDK Streaming

```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(request: Request) {
  const { messages } = await request.json();
  
  // Retrieve context
  const context = await retrieveRelevantChunks(messages[messages.length - 1].content);
  
  const result = streamText({
    model: openai('gpt-4o'),
    system: `Answer based on the following context:\n${context}`,
    messages,
  });
  
  return result.toDataStreamResponse();
}
```

### LangChain Streaming

```python
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

llm = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Stream with retrieval
async for chunk in rag_chain.astream({"question": "What are the rate limits?"}):
    yield chunk
```

### Streaming Architecture

```
User Query
     |
[Retrieval] ← 100-500ms (not streamable, must complete first)
     |
[Context Assembly] ← <10ms
     |
[LLM Generation] ← Streamable: first token in 200-500ms
     |
[Token-by-token streaming to client]
```

Show a loading indicator during retrieval, then stream generation tokens.

## Cost Optimization

### Cost Breakdown for Typical RAG Query

| Component | Cost per Query | Percentage |
|-----------|---------------|------------|
| Query embedding | $0.000013 | <1% |
| Vector search | $0.00001 | <1% |
| BM25 search | ~$0 | <1% |
| Reranking (50 docs, Cohere) | $0.002 | 15-25% |
| LLM generation (4K input + 500 output) | $0.006-0.03 | 60-80% |
| **Total per query** | **$0.008-0.032** | 100% |

### Cost Reduction Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| Reduce embedding dimensions (Matryoshka) | 50-80% of storage | Set `dimensions=512` in OpenAI API |
| Batch embeddings at ingestion | 30-40% of embedding cost | Batch 100-500 texts per API call |
| Cache query embeddings | 40-60% of query embedding cost | Redis with 1-hour TTL |
| Cache retrieval results | 30-50% of retrieval cost | Redis with 5-60 min TTL |
| Use GPT-4o-mini for simple queries | 90% of generation cost | Route by query complexity |
| Self-hosted cross-encoder vs Cohere | 50-80% of reranking at scale | GPU amortization above 100K queries/day |
| Response caching (careful) | 90% for repeated queries | Short TTL, cache FAQs only |

### Model Routing

```python
def select_model(query: str, context_tokens: int) -> str:
    complexity = classify_query_complexity(query)
    
    if complexity == "simple" and context_tokens < 2000:
        return "gpt-4o-mini"   # $0.15/1M input
    elif complexity == "complex" or context_tokens > 8000:
        return "gpt-4o"        # $2.50/1M input
    else:
        return "gpt-4o-mini"   # Default to cheaper
```

Intelligent routing reduces LLM costs 50-70% while maintaining quality on complex queries.

## Ingestion Pipeline

### Architecture

```
[Source Documents]
     |
[Document Loaders] → PDF, Markdown, HTML, DOCX, CSV
     |
[Preprocessing] → Clean, normalize, extract metadata
     |
[Chunking] → Strategy per document type
     |
[Embedding] → Batch embed with caching
     |
[Vector Store] → Upsert with metadata
     |
[Verification] → Spot-check retrieval quality
```

### Incremental Ingestion

Only process new or changed documents:

```python
def incremental_ingest(documents: list):
    for doc in documents:
        content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
        
        existing = db.query("SELECT hash FROM documents WHERE source = %s", [doc.source])
        if existing and existing.hash == content_hash:
            continue  # Document unchanged, skip
        
        if existing:
            # Document changed — delete old chunks, re-process
            vectorstore.delete(filter={"source": doc.source})
        
        chunks = chunk_document(doc)
        embeddings = batch_embed([c.content for c in chunks])
        vectorstore.upsert(chunks, embeddings)
        
        db.upsert("documents", {"source": doc.source, "hash": content_hash})
```

### Ingestion Rate Limiting

OpenAI rate limits for embeddings:

| Tier | RPM | TPM | Batch Recommendation |
|------|-----|-----|---------------------|
| Tier 1 | 500 | 1M | 100 texts/batch, 5 batches/sec |
| Tier 2 | 5,000 | 5M | 500 texts/batch, 10 batches/sec |
| Tier 3+ | 10,000 | 10M+ | 500 texts/batch, 20 batches/sec |

```python
import asyncio
from openai import AsyncOpenAI

async def rate_limited_embed(texts, batch_size=100, delay=0.2):
    client = AsyncOpenAI()
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = await client.embeddings.create(
            model="text-embedding-3-small", input=batch
        )
        all_embeddings.extend([d.embedding for d in response.data])
        await asyncio.sleep(delay)
    return all_embeddings
```

## Monitoring and Observability

### Key Dashboards

| Dashboard | Metrics | Alert On |
|-----------|---------|----------|
| Retrieval Health | Latency P50/P95/P99, empty result rate, cache hit rate | P95 > 500ms, empty > 10% |
| Generation Quality | Faithfulness (sampled), relevance (sampled), user feedback | Faithfulness < 0.75 |
| Cost Tracking | Daily embedding cost, generation cost, reranking cost | Cost > 1.5x baseline |
| Ingestion Pipeline | Documents processed, chunks created, errors | Error rate > 5% |

### Logging Pattern

```python
import structlog

logger = structlog.get_logger()

def rag_query(query: str, user_id: str) -> str:
    start = time.time()
    
    # Log retrieval
    chunks = retrieve(query)
    retrieval_ms = (time.time() - start) * 1000
    logger.info("retrieval_complete",
        query_hash=hash(query), chunk_count=len(chunks),
        latency_ms=retrieval_ms, cache_hit=was_cache_hit)
    
    # Log generation
    response = generate(query, chunks)
    total_ms = (time.time() - start) * 1000
    logger.info("generation_complete",
        query_hash=hash(query), total_ms=total_ms,
        input_tokens=count_tokens(chunks), output_tokens=count_tokens(response),
        model=selected_model)
    
    return response
```

## Scaling Patterns

### Horizontal Scaling

| Component | Scaling Strategy |
|-----------|-----------------|
| Embedding service | Stateless — add replicas behind load balancer |
| Vector database | Shard by tenant or hash (database-specific) |
| Reranking service | Stateless — add GPU replicas |
| LLM gateway | Use provider's built-in scaling (OpenAI, Anthropic) |
| Cache (Redis) | Redis Cluster or ElastiCache |

### Load Testing

Test the full pipeline end-to-end, not individual components:

```python
import locust

class RAGUser(locust.HttpUser):
    wait_time = locust.between(1, 3)
    
    @locust.task
    def query_rag(self):
        self.client.post("/api/rag", json={
            "question": random.choice(test_questions),
            "top_k": 5
        })
```

Target: P95 end-to-end latency under 3 seconds for interactive applications.

## Fallback Strategy

```python
def rag_with_fallback(query: str) -> dict:
    # Tier 1: Full pipeline (hybrid + rerank)
    try:
        chunks = hybrid_search_and_rerank(query, top_k=5)
        if max_score(chunks) > 0.7:
            return {"answer": generate(query, chunks), "confidence": "high"}
    except TimeoutError:
        pass
    
    # Tier 2: Vector-only (skip reranker)
    try:
        chunks = vector_search(query, top_k=10)
        if max_score(chunks) > 0.5:
            return {"answer": generate(query, chunks[:5]), "confidence": "medium"}
    except Exception:
        pass
    
    # Tier 3: Keyword fallback
    chunks = bm25_search(query, top_k=5)
    if chunks:
        return {"answer": generate(query, chunks), "confidence": "low"}
    
    # Tier 4: Graceful degradation
    return {
        "answer": "I don't have enough information to answer confidently. "
                  "Please try rephrasing or contact support.",
        "confidence": "none"
    }
```

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| No caching at any layer | Paying full price for every query | Add embedding and retrieval cache first |
| Caching responses without invalidation | Serving stale/wrong answers | Version-key caches, invalidate on doc update |
| No ingestion deduplication | Re-embedding unchanged docs | Content-hash check before processing |
| Synchronous embedding in hot path | Slow responses | Embed at ingestion, cache query embeddings |
| No fallback strategy | Hard failures on retrieval issues | Implement tiered fallback |
| No cost monitoring | Budget surprise at month end | Track daily cost per component |
| No load testing | Unknown breaking point | Load test full pipeline before launch |
| Logging queries with PII | Privacy violation | Hash or redact PII in logs |
