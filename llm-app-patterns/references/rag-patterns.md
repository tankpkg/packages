# RAG Patterns

Sources: Huyen (AI Engineering), Rothman (RAG-Driven Generative AI), Bose (Mastering Retrieval-Augmented Generation), 2024–2026 production benchmarks

Covers: RAG architecture, chunking strategies, embedding selection, retrieval algorithms, hybrid search, reranking, advanced patterns, evaluation metrics.

## RAG Architecture

RAG separates knowledge from the model. The model provides reasoning; the knowledge store provides facts. Every RAG system runs two pipelines.

### Ingest Pipeline (Offline)

```
Raw documents
    → Chunking       (split into retrievable units)
    → Embedding      (convert to dense vectors)
    → Indexing       (store in vector DB + optional keyword index)
```

Build the ingest pipeline first. Retrieval quality is a ceiling on generation quality — no prompt engineering compensates for poor retrieval.

### Query Pipeline (Online)

```
User query
    → Query embedding
    → Retrieval      (vector search + optional keyword search)
    → Reranking      (score and trim candidates to top-k)
    → Context assembly
    → LLM generation
    → Response
```

Instrument each stage independently. Retrieval failures and generation failures have different fixes.

## Chunking Strategy Selection

How documents are split determines what the retriever can find. Splitting at the wrong boundary corrupts the embedding and breaks retrieval.

### Strategy Comparison

| Strategy | Best For | Chunk Size | Overlap | Trade-off |
|----------|----------|------------|---------|-----------|
| Recursive character | Default, mixed text | 400–512 tokens | 10–15% | Simple, occasionally splits sentences |
| Page-level | PDFs, slide decks | Full page | None | Highest consistency, large context |
| Sentence-based | News, short-form | 1–3 sentences | 1 sentence | Good coherence, many small chunks |
| Semantic | Dense technical docs | Variable | None | Better coherence, slower, LLM cost |
| Hierarchical (parent-child) | Long-form documents | Small retrieve / large send | None | Best context; more index complexity |
| Contextual | Reference material | 400–512 tokens | 10% | Best retrieval quality, expensive |

### Selection Rules

- Default to recursive character splitting at 400–512 tokens with 10–15% overlap for most systems.
- Use page-level chunking for PDFs — lowest variance, most consistent retrieval.
- Use hierarchical chunking when full context matters but precise retrieval is still needed: index small chunks, but send the surrounding parent chunk to the LLM.
- Use contextual chunking (prepend a document-level summary to each chunk before embedding) for the highest retrieval accuracy. Anthropic research shows ~49% reduction in retrieval failures. Costs one LLM call per chunk at ingest time.
- Overlap at 10–20% of chunk size prevents losing information at boundaries.

### Hierarchical Pattern (Pseudocode)

```
# Ingest
for each document:
    parent_chunks = split(document, size=1024)
    for each parent_chunk:
        child_chunks = split(parent_chunk, size=256)
        store(parent_chunk, id=parent_id)
        for each child_chunk:
            embed(child_chunk)
            index(vector, metadata={parent_id})

# Retrieval
child_results = vector_search(query_embedding, k=20)
parent_chunks = [fetch(r.parent_id) for r in child_results]
send parent_chunks to LLM (not children)
```

## Embedding Selection

### Model Comparison

| Model | Dimensions | Cost/1M tokens | Best For |
|-------|-----------|----------------|----------|
| OpenAI text-embedding-3-small | 1536 | ~$0.02 | Default production choice |
| OpenAI text-embedding-3-large | 3072 | ~$0.13 | Accuracy-critical domains |
| Cohere Embed v4 | 1024 | ~$0.10 | Multilingual, multimodal |
| BGE-M3 (local) | 1024 | Compute only | Privacy-constrained, high volume |
| all-MiniLM-L6-v2 (local) | 384 | Compute only | Low-resource, acceptable quality |

### Dense vs Sparse vs Hybrid

| Type | Mechanism | Strengths | Weaknesses |
|------|-----------|-----------|------------|
| Dense (vector) | Semantic similarity | Handles synonyms, paraphrases | Misses exact rare terms |
| Sparse (BM25/TF-IDF) | Keyword frequency | Exact term match, domain jargon | No semantic understanding |
| Hybrid | Weighted combination | Best of both | More pipeline complexity |

Use hybrid retrieval in production. Sparse search catches exact product names, IDs, and technical terms that dense search misses.

## Retrieval Algorithms

### Vector Search

Sufficient when queries are natural-language questions and documents are semantically rich. Fetch more candidates than needed (k=20) so the reranker has room to work.

```
query_vector = embed(user_query)
candidates = vector_db.search(query_vector, k=20, threshold=0.65)
```

### Hybrid Search with RRF

Combine vector and keyword results using Reciprocal Rank Fusion.

```
vector_results = vector_search(query_vector, k=20)
bm25_results  = bm25_search(query_text, k=20)

# RRF formula: score(doc) = Σ 1/(k + rank) where k=60
combined = reciprocal_rank_fusion([vector_results, bm25_results], k=60)
top_results = combined[:30]  # pass to reranker
```

RRF is robust to score scale differences between retrieval methods. The constant k=60 is a well-established default from the original RRF paper (Cormack et al.).

### Metadata Filtering

Apply metadata filters before vector search to reduce search space and prevent cross-tenant data exposure.

```
candidates = vector_db.search(
    query_vector,
    filter={tenant_id: current_user.tenant, doc_type: "policy"},
    k=10,
)
```

High-selectivity filters (user ID, tenant) dramatically reduce search space. Low-selectivity filters (date > 2023) provide minimal benefit.

### HyDE (Hypothetical Document Embedding)

For queries where the question and answer share few surface-level terms, generate a hypothetical answer and retrieve documents similar to that answer rather than to the question.

```
hypothetical = llm.generate("Write a short answer to: " + user_query)
candidates = vector_db.search(embed(hypothetical), k=10)
```

Use when direct query embedding returns poor results on factual lookup queries.

### Multi-Query Retrieval

Generate 3–5 query paraphrases, retrieve for each independently, deduplicate by content hash.

```
variants = llm.generate("Rephrase this query 4 ways: " + user_query)
all_results = flatten([vector_search(q, k=5) for q in variants])
final_results = deduplicate(all_results)
```

Improves recall for ambiguous queries. Cost: 3–5× more embedding calls.

## Post-Retrieval: Reranking

Retrieve a large candidate pool with fast approximate search (k=20–50), then apply a slower accurate scorer to produce the final context (k=3–5).

### Reranker Comparison

| Method | Latency | Accuracy | Cost | Use When |
|--------|---------|----------|------|----------|
| Cross-encoder (local) | ~50ms | Good | Compute only | Privacy, high volume |
| Cohere Rerank API | ~100ms | Excellent | ~$1/1K requests | Production default |
| LLM listwise rerank | ~500ms | Excellent | LLM API cost | Highest accuracy critical |
| MMR (diversity) | <10ms | Moderate | Free | Diverse results needed |

### MMR (Max Marginal Relevance)

Prevents returning 5 near-identical chunks. Balances relevance with diversity.

```
# MMR: iteratively pick the candidate that maximizes
# λ × similarity(candidate, query) − (1−λ) × max_similarity(candidate, selected)
selected = mmr_select(candidates, query_vector, k=5, lambda=0.5)
```

`lambda=0`: maximum diversity. `lambda=1`: maximum relevance (same as plain similarity search).

## Advanced Patterns

### Self-RAG

The model decides whether to retrieve and whether the retrieved content is relevant. Reduces over-retrieval costs for simple queries.

```
Step 1: Does this question require external knowledge?
    YES → retrieve → assess: is retrieved content relevant?
        YES → incorporate
        NO  → re-retrieve with refined query
    NO  → answer from model knowledge directly
```

### Agentic RAG

Treat retrieval as a tool call. The agent iterates — retrieve, assess completeness, retrieve again if needed — before generating a final answer.

Best for: multi-hop questions that require combining facts from multiple documents. Cost: multiple LLM calls per query versus one in standard RAG.

### GraphRAG

Build a knowledge graph from documents. Queries traverse entity relationships rather than pure vector similarity.

Use for questions requiring multi-hop reasoning across entities, or summarization across an entire document collection. Higher quality at significantly higher cost and complexity.

## RAG Evaluation Metrics

Evaluate both retrieval quality and generation quality independently.

### Retrieval Metrics

| Metric | What It Measures | Requires Golden Labels? |
|--------|-----------------|------------------------|
| Context Relevance | Fraction of retrieved chunks relevant to the query | No (LLM judge) |
| Context Recall | Fraction of needed information that was retrieved | Yes |
| Context Precision | Fraction of retrieved chunks that were actually used | Partial |

### Generation Metrics

| Metric | What It Measures | Requires Golden Labels? |
|--------|-----------------|------------------------|
| Faithfulness | Answer uses only retrieved context; no hallucination | No (LLM judge) |
| Answer Relevance | Answer addresses the actual question | No (LLM judge) |
| Answer Correctness | Answer matches known-correct answer | Yes |

Implement faithfulness and answer relevance first — both use LLM-as-judge and require no golden dataset. Add answer correctness when building a curated test set.

## RAG vs Fine-Tuning Decision

| Signal | Prefer RAG | Prefer Fine-Tuning |
|--------|------------|-------------------|
| Knowledge updates frequently | ✓ | |
| Privacy or compliance required | ✓ | |
| Explainability needed | ✓ | |
| Knowledge is stable and bounded | | ✓ |
| Style/format adaptation needed | | ✓ |
| Latency critical (< 200ms) | | ✓ |

The two are not mutually exclusive. Fine-tune for style and task format; use RAG for factual knowledge.
