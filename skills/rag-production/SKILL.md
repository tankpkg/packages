---
name: "@tank/rag-production"
description: |
  Production RAG (Retrieval-Augmented Generation) pipeline architecture for any
  language or framework. Covers chunking strategies (fixed, recursive, semantic,
  document-aware, parent-child), embedding models (OpenAI, Cohere, open-source,
  dimensionality reduction, Matryoshka), vector databases (Pinecone, Weaviate,
  Qdrant, pgvector, Chroma, Milvus), retrieval patterns (hybrid search, BM25 +
  vector, metadata filtering, reranking with Cohere/cross-encoders, reciprocal
  rank fusion), advanced retrieval (HyDE, multi-query, query decomposition,
  contextual compression), agentic RAG (tool-use retrieval, self-RAG, CRAG),
  graph RAG (Microsoft GraphRAG, RAPTOR), context assembly (prompt construction,
  citation, lost-in-the-middle mitigation), evaluation (RAGAS, faithfulness,
  context precision/recall, DeepEval), and production operations (caching,
  streaming, cost optimization, multimodal RAG).

  Synthesizes LangChain documentation, LlamaIndex documentation, Vercel AI SDK,
  RAGAS framework, pgvector documentation, Pinecone/Weaviate/Qdrant docs, and
  2024-2026 RAG research (HyDE, RAPTOR, GraphRAG, ColBERT).

  Trigger phrases: "RAG", "retrieval augmented generation", "RAG pipeline",
  "vector database", "embedding model", "chunking strategy", "hybrid search",
  "reranking", "agentic RAG", "RAG evaluation", "RAGAS", "pgvector",
  "Pinecone", "Weaviate", "Qdrant", "Chroma", "RAG production",
  "RAG best practices", "graph RAG", "RAPTOR", "HyDE",
  "context window RAG", "RAG implementation", "semantic search",
  "document retrieval", "knowledge base", "RAG architecture"
---

# RAG Production

## Core Philosophy

1. **Retrieval quality trumps generation quality** — A perfect LLM cannot compensate for irrelevant context. Invest 80% of effort in the retrieval pipeline (chunking, indexing, search, reranking) before tuning prompts.
2. **Start naive, measure, then optimize** — Begin with recursive character splitting + single vector search. Add hybrid search, reranking, and query expansion only when metrics prove the baseline insufficient.
3. **Chunk for retrieval, not for storage** — Chunk boundaries determine what the model sees. Optimize chunk size and overlap for answer completeness, not disk efficiency.
4. **Evaluate continuously with RAGAS** — Track faithfulness, context precision, context recall, and answer relevance on every pipeline change. Gut-feel evaluation hides regression.
5. **Cache aggressively, embed once** — Embedding computation and reranking are the dominant costs. Cache embeddings at ingestion, cache retrieval results per query hash, batch embed during off-peak.

## Quick-Start: Common Problems

### "How do I build a basic RAG pipeline?"

1. Load documents with appropriate loaders (PDF, markdown, HTML)
2. Split into chunks: recursive character splitter, 512-1024 tokens, 10-20% overlap
3. Embed chunks with `text-embedding-3-small` (cost-effective) or `text-embedding-3-large` (quality)
4. Store in vector database (pgvector for existing Postgres, Pinecone for managed)
5. Retrieve top-k (k=5-10) by cosine similarity on query embedding
6. Construct prompt: system instructions + retrieved context + user query
7. Generate with LLM, include source citations
-> See `references/chunking-strategies.md` and `references/embedding-models.md`

### "Retrieval returns irrelevant results"

1. Check chunk size — too large buries signal, too small loses context
2. Add hybrid search: combine BM25 full-text + vector similarity with RRF
3. Add a reranker (Cohere Rerank or cross-encoder) as second-stage filter
4. Try HyDE: generate a hypothetical answer, embed that instead of the raw query
5. Verify embedding model matches your domain (multilingual, code, etc.)
-> See `references/retrieval-patterns.md` and `references/reranking.md`

### "RAG is too expensive in production"

1. Use `text-embedding-3-small` with reduced dimensions (512d via Matryoshka)
2. Cache embeddings — never re-embed unchanged documents
3. Cache retrieval results by query hash (TTL: 5-60 minutes)
4. Use tiered retrieval: cheap vector search first, expensive reranker only on top-50
5. Batch embedding calls during ingestion, not per-request
-> See `references/production-operations.md`

### "How do I evaluate my RAG pipeline?"

1. Generate a test set: 50-100 question-answer pairs from your corpus
2. Run RAGAS metrics: faithfulness, context precision, context recall, answer relevance
3. Baseline first, then measure each pipeline change independently
4. Set quality gates: faithfulness > 0.85, context precision > 0.75
-> See `references/evaluation.md`

## Decision Trees

### Vector Database Selection

| Signal | Recommendation |
|--------|---------------|
| Already using PostgreSQL | pgvector (simplest ops, hybrid via tsvector) |
| Managed, zero-ops required | Pinecone Serverless |
| Need native hybrid search + multi-tenancy | Weaviate |
| Maximum performance, self-hosted | Qdrant |
| Local dev / prototyping | Chroma |
| Enterprise, massive scale | Milvus or MongoDB Atlas Vector Search |

### Chunking Strategy

| Content Type | Strategy |
|-------------|----------|
| Prose documents (articles, reports) | Recursive character, 512-1024 tokens, 10% overlap |
| Markdown / structured docs | Markdown header splitter (preserve hierarchy) |
| Code repositories | Language-aware splitter (function/class boundaries) |
| Legal / regulatory | Semantic chunking (sentence-transformer boundaries) |
| FAQ / Q&A pairs | Keep each Q&A as a single chunk |
| Tables / structured data | Keep table intact, embed with surrounding context |

### Retrieval Strategy

| Signal | Approach |
|--------|---------|
| Baseline / starting point | Single vector search, top-k=5 |
| Keyword-heavy queries fail | Add BM25 hybrid search + RRF |
| Top-k results contain noise | Add reranker (Cohere Rerank or cross-encoder) |
| Short/ambiguous queries | HyDE or multi-query expansion |
| Complex multi-part questions | Query decomposition → parallel retrieval → merge |
| Agent needs selective retrieval | Agentic RAG with tool-use |

## Reference Index

| File | Contents |
|------|----------|
| `references/chunking-strategies.md` | Fixed, recursive, semantic, document-aware, parent-child, and hierarchical chunking with size/overlap guidance |
| `references/embedding-models.md` | OpenAI, Cohere, open-source models, dimensionality reduction, Matryoshka, quantization, benchmarks |
| `references/vector-databases.md` | pgvector, Pinecone, Weaviate, Qdrant, Chroma, Milvus comparison with indexing (HNSW, IVF), ops trade-offs |
| `references/retrieval-patterns.md` | Hybrid search (BM25 + vector), metadata filtering, HyDE, multi-query, query decomposition, contextual compression |
| `references/reranking.md` | Cohere Rerank, cross-encoders, ColBERT, reciprocal rank fusion, MMR diversity, scoring pipelines |
| `references/context-assembly.md` | Prompt construction, citation/attribution, lost-in-the-middle, context window budgeting, source deduplication |
| `references/evaluation.md` | RAGAS metrics (faithfulness, precision, recall), DeepEval, test set generation, quality gates, regression testing |
| `references/advanced-rag.md` | Agentic RAG, self-RAG, CRAG, graph RAG (GraphRAG, RAPTOR), multimodal RAG, late chunking |
| `references/production-operations.md` | Caching (embedding, retrieval, LLM), streaming, cost optimization, monitoring, ingestion pipelines, scaling |
