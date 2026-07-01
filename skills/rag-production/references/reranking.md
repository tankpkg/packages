# Reranking

Sources: Cohere Rerank documentation, sentence-transformers cross-encoder documentation, Khattab & Zaharia (ColBERT, 2020), Cormack et al. (Reciprocal Rank Fusion, 2009), LangChain Reranker documentation, 2024-2026 RAG reranking benchmarks

Covers: reranking architecture, Cohere Rerank, cross-encoders, ColBERT, reciprocal rank fusion, MMR diversity, scoring pipeline design, and latency/cost trade-offs.

## Why Reranking Matters

First-stage retrieval (vector search or BM25) trades accuracy for speed using approximate algorithms. Reranking applies a more expensive but more accurate model to re-score and reorder a small candidate set. Production systems consistently see 10-25% improvement in retrieval precision after adding a reranker.

### Two-Stage Architecture

```
Query
  |
[Stage 1: Fast Retrieval] — ANN search, return top-50 to top-100
  |                          Latency: 10-50ms
  |                          Accuracy: Good (approximate)
  |
[Stage 2: Reranking] — Cross-encoder or API reranker scores each candidate
  |                     Latency: 50-200ms for 50 candidates
  |                     Accuracy: Excellent (full query-document attention)
  |
Top-5 to top-10 reranked results → LLM context
```

## Cohere Rerank

Managed reranking API. Send query + candidate documents, receive relevance scores.

```python
import cohere

co = cohere.Client(api_key="YOUR_API_KEY")

results = co.rerank(
    model="rerank-v3.5",
    query="What are the API rate limits?",
    documents=[
        "The API allows 100 requests per minute for free tier...",
        "Rate limiting helps prevent abuse and ensures fair usage...",
        "Premium accounts get 1000 requests per minute...",
        "The authentication endpoint uses OAuth 2.0..."
    ],
    top_n=3,
    return_documents=True
)

for result in results.results:
    print(f"Score: {result.relevance_score:.4f} — {result.document.text[:80]}")
```

### Cohere Rerank Models

| Model | Quality | Latency (50 docs) | Cost | Best For |
|-------|---------|-------------------|------|----------|
| rerank-v3.5 | Highest | ~150ms | $2/1K searches | Production, quality-critical |
| rerank-v3.0 | High | ~120ms | $2/1K searches | General purpose |
| rerank-english-v2.0 | Good | ~100ms | $1/1K searches | English-only, cost-sensitive |
| rerank-multilingual-v3.0 | High | ~150ms | $2/1K searches | Multi-language corpora |

### LangChain Integration

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

reranker = CohereRerank(model="rerank-v3.5", top_n=5)
retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 50})
)
docs = retriever.invoke("What are the API rate limits?")
```

## Cross-Encoder Reranking

Cross-encoders process query and document together through a transformer, computing full attention between all tokens. More accurate than bi-encoders (which embed query and document independently) because they see both texts simultaneously.

### sentence-transformers Cross-Encoder

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Score query-document pairs
pairs = [
    ["What are the API rate limits?", "The API allows 100 requests per minute..."],
    ["What are the API rate limits?", "Authentication uses OAuth 2.0..."],
    ["What are the API rate limits?", "Premium accounts get 1000 RPM..."]
]
scores = model.predict(pairs)
# scores: [0.92, 0.03, 0.87] — authentication doc correctly scored lowest
```

### Cross-Encoder Model Comparison

| Model | Parameters | Quality (NDCG@10) | Speed (50 pairs) | Best For |
|-------|-----------|-------------------|-------------------|----------|
| ms-marco-MiniLM-L-6-v2 | 22M | 0.39 | ~20ms (GPU) | Fast, low-resource |
| ms-marco-MiniLM-L-12-v2 | 33M | 0.41 | ~35ms (GPU) | Balanced |
| bge-reranker-v2-m3 | 568M | 0.46 | ~200ms (GPU) | Multilingual, high quality |
| bge-reranker-v2-gemma | 2B | 0.48 | ~500ms (GPU) | Maximum quality |

### Self-Hosted vs API Trade-offs

| Factor | Cohere Rerank (API) | Cross-Encoder (Self-hosted) |
|--------|--------------------|-----------------------------|
| Setup | API key only | GPU server + model deployment |
| Latency | Network RTT + compute | Compute only (lower if co-located) |
| Cost at scale | Per-search pricing | Fixed GPU cost (amortized) |
| Quality | Top-tier | Depends on model choice |
| Data privacy | Data sent to Cohere | Data stays in your infra |
| Maintenance | Zero | Model updates, GPU management |

At fewer than 100K queries/day, Cohere Rerank is simpler and comparable cost. Above that, self-hosted cross-encoders become more economical.

## ColBERT (Contextualized Late Interaction)

ColBERT computes token-level embeddings for both query and document, then performs late interaction (MaxSim) between token embeddings. Faster than full cross-encoders while maintaining most of the quality advantage.

### How ColBERT Scores

```
Query tokens:  [q1, q2, q3, q4]     (each a vector)
Document tokens: [d1, d2, d3, d4, d5]  (each a vector)

Score = SUM over qi of MAX over dj of cosine(qi, dj)
```

Each query token finds its best-matching document token. This enables pre-computing document token embeddings (offline) while query tokens are computed at query time.

### ColBERT Advantages

| Over Bi-Encoders | Over Cross-Encoders |
|------------------|---------------------|
| Token-level matching captures nuance | Document embeddings pre-computed (faster) |
| Better on exact term matching | Scales to large candidate sets |
| Higher NDCG scores | 10-100x faster inference |

### RAGatouille (ColBERTv2 for RAG)

```python
from ragatouille import RAGPretrainedModel

rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

# Index documents
rag.index(
    collection=[doc.page_content for doc in documents],
    document_ids=[doc.metadata["id"] for doc in documents],
    index_name="my_rag_index"
)

# Search with ColBERT
results = rag.search(query="API rate limits", k=10)
```

## Maximal Marginal Relevance (MMR)

MMR balances relevance with diversity. Without MMR, top-k results may all be semantically similar (near-duplicates), wasting context window tokens on redundant information.

### MMR Formula

```
MMR(d) = lambda * Sim(d, query) - (1 - lambda) * max(Sim(d, d_selected))
```

- `lambda = 1.0`: Pure relevance (no diversity)
- `lambda = 0.5`: Balance relevance and diversity
- `lambda = 0.0`: Maximum diversity (ignore relevance)

### LangChain MMR Search

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 20,       # Fetch 20, select 5 with MMR
        "lambda_mult": 0.7   # Favor relevance, some diversity
    }
)
```

### When to Use MMR

| Signal | Use MMR? |
|--------|---------|
| Retrieved chunks are near-duplicates | Yes — diversity reduces redundancy |
| Broad topic query ("tell me about X") | Yes — covers more aspects |
| Specific factual query ("what is the price of X") | No — relevance is king |
| Parent-child chunking already in use | Less needed — parent chunks already provide context |

## Scoring Pipeline Design

Combine multiple signals into a single ranking score.

### Production Pipeline Example

```python
def score_and_rank(query: str, candidates: list, top_n: int = 5) -> list:
    # Stage 1: Vector similarity scores (already from retrieval)
    # Stage 2: BM25 scores (if hybrid search)
    # Stage 3: Cross-encoder reranking
    rerank_scores = cross_encoder.predict(
        [[query, doc.content] for doc in candidates]
    )
    
    # Stage 4: Metadata boost
    for i, doc in enumerate(candidates):
        recency_boost = compute_recency_boost(doc.metadata.get("created_at"))
        authority_boost = compute_authority_boost(doc.metadata.get("source"))
        candidates[i].final_score = (
            0.7 * rerank_scores[i] +
            0.2 * recency_boost +
            0.1 * authority_boost
        )
    
    # Stage 5: MMR for diversity
    selected = mmr_select(candidates, query_embedding, k=top_n, lambda_mult=0.7)
    return selected
```

### Score Component Weights

| Component | Weight Range | Purpose |
|-----------|-------------|---------|
| Reranker score | 0.6-0.8 | Primary relevance signal |
| Recency boost | 0.05-0.2 | Prefer newer documents |
| Authority boost | 0.05-0.15 | Prefer authoritative sources |
| User feedback signal | 0.05-0.1 | Learn from click/rating data |

## Latency and Cost Budget

| Component | Latency | Cost per Query | Notes |
|-----------|---------|---------------|-------|
| Vector search (top-50) | 10-50ms | ~$0.00001 | Negligible |
| BM25 search (top-50) | 5-20ms | ~$0.00001 | Negligible |
| RRF merge | <1ms | None | In-memory computation |
| Cohere Rerank (50 docs) | 100-200ms | $0.002 | Dominant cost |
| Cross-encoder (50 pairs) | 20-200ms | GPU amortized | Depends on model size |
| MMR selection | <5ms | None | In-memory |
| Total pipeline | 150-400ms | $0.002-0.005 | Acceptable for interactive |

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Reranking top-5 instead of top-50 | Reranker has no room to improve order | Retrieve top-50+, rerank to top-5 |
| Skipping reranking entirely | 10-25% precision left on the table | Add reranker as the highest-impact single improvement |
| Same model for embedding and reranking | Redundant signal, no quality gain | Use bi-encoder for retrieval, cross-encoder for reranking |
| Reranking in the hot path without caching | Latency on every request | Cache rerank results by query hash |
| Not measuring reranker impact | Cannot justify cost | A/B test with and without reranking |
| Using reranker on already-excellent results | Cost without benefit | Only add when baseline metrics are insufficient |
