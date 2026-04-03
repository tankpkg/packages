# Retrieval Patterns

Sources: LangChain Retrievers documentation, LlamaIndex Query Engines documentation, Gao et al. (HyDE, 2023), Ma et al. (Query Decomposition, 2023), Pinecone hybrid search documentation, 2024-2026 RAG production research

Covers: hybrid search (BM25 + vector), metadata filtering, HyDE, multi-query retrieval, query decomposition, step-back prompting, and contextual compression.

## Single-Vector Retrieval (Baseline)

The simplest retrieval pattern: embed the query, find the k nearest chunks by cosine similarity.

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PGVector(
    connection_string=DATABASE_URL,
    embedding_function=embeddings,
    collection_name="documents"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
docs = retriever.invoke("How do I configure authentication?")
```

### Limitations of Single-Vector Search

| Problem | Example | Why It Fails |
|---------|---------|-------------|
| Keyword mismatch | Query: "SSL certificate" vs chunk: "TLS cert" | Embeddings may not bridge all synonyms |
| Acronym/jargon | Query: "K8s" vs chunk: "Kubernetes" | Domain abbreviations poorly embedded |
| Exact identifier lookup | Query: "error code E-4021" | Semantic search ignores exact strings |
| Negation | Query: "not related to pricing" | Embeddings struggle with negation |
| Multi-faceted queries | "Compare auth methods for mobile and web" | Single vector collapses multiple intents |

When single-vector fails on these patterns, add hybrid search or query expansion.

## Hybrid Search (BM25 + Vector)

Combine lexical (keyword) search with semantic (vector) search. BM25 excels at exact matches and rare terms; vectors excel at semantic similarity. Together they cover each other's blind spots.

### Architecture

```
Query: "configure K8s ingress TLS"
         |                    |
    [BM25 Search]      [Vector Search]
    exact "K8s"        semantic "configure
    exact "TLS"        ingress TLS"
         |                    |
    Top-50 by BM25     Top-50 by cosine
         \                  /
          [Reciprocal Rank Fusion]
                  |
            Top-10 merged results
```

### Reciprocal Rank Fusion (RRF)

RRF merges ranked lists without requiring score normalization. Each document's score is the sum of reciprocal ranks across all lists:

```
RRF_score(d) = SUM( 1 / (k + rank_i(d)) ) for each ranker i
```

Where `k` is a constant (typically 60) that controls how much top ranks dominate.

```python
def reciprocal_rank_fusion(ranked_lists: list[list], k: int = 60) -> list:
    scores = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### LangChain EnsembleRetriever

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

bm25_retriever = BM25Retriever.from_documents(documents, k=50)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 50})

ensemble = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6]  # Tune based on query mix
)
results = ensemble.invoke("configure K8s ingress TLS")
```

### Weight Tuning

| Query Profile | BM25 Weight | Vector Weight | Rationale |
|--------------|-------------|---------------|-----------|
| Technical docs with jargon | 0.5 | 0.5 | Equal — jargon needs exact match |
| Natural language Q&A | 0.3 | 0.7 | Semantic similarity dominant |
| Code search | 0.6 | 0.4 | Function names, identifiers are exact |
| Multilingual | 0.2 | 0.8 | Vector models handle cross-language |

## Metadata Filtering

Apply structured filters before or during vector search to narrow the search space. Pre-filtering reduces computation; post-filtering may miss results if top-k is too small.

### Common Filter Patterns

```python
# Temporal filtering — only recent documents
results = vectorstore.similarity_search(
    query, k=10,
    filter={"created_at": {"$gte": "2025-01-01"}}
)

# Source filtering — specific document type
results = vectorstore.similarity_search(
    query, k=10,
    filter={"doc_type": {"$eq": "api-reference"}}
)

# Tenant isolation — mandatory in multi-tenant
results = vectorstore.similarity_search(
    query, k=10,
    filter={"tenant_id": {"$eq": current_tenant_id}}
)

# Compound filters
results = vectorstore.similarity_search(
    query, k=10,
    filter={
        "$and": [
            {"doc_type": {"$eq": "technical"}},
            {"language": {"$eq": "en"}},
            {"status": {"$eq": "published"}}
        ]
    }
)
```

### Pre-Filter vs Post-Filter

| Strategy | Behavior | Trade-off |
|----------|----------|-----------|
| Pre-filter | Filter first, then vector search within subset | Fast if filter is selective; may hurt recall if subset too small |
| Post-filter | Vector search first, then filter results | Better recall, but wastes compute on filtered-out results |
| Hybrid | Database-level optimization (Qdrant, Weaviate) | Best of both; database decides strategy |

Qdrant and Weaviate implement adaptive pre/post filtering. pgvector requires manual implementation (typically post-filter with higher initial k).

## HyDE (Hypothetical Document Embeddings)

Generate a hypothetical answer to the query, embed that answer, and use the answer embedding for retrieval. The hypothesis is closer in embedding space to real answers than the raw question.

### How HyDE Works

```
User query: "What are the rate limits for the API?"
    |
[LLM generates hypothetical answer]
    |
"The API enforces rate limits of 100 requests per minute
 for free tier and 1000 for paid tier. Exceeding limits
 returns HTTP 429 with a Retry-After header."
    |
[Embed hypothetical answer]
    |
[Search with hypothesis embedding — closer to real docs]
```

### LangChain Implementation

```python
from langchain.chains import HypotheticalDocumentEmbedder
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
base_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

hyde_embeddings = HypotheticalDocumentEmbedder.from_llm(
    llm=llm,
    base_embeddings=base_embeddings,
    prompt_key="web_search"  # or custom prompt
)

# Use as drop-in replacement for embeddings in retriever
vectorstore = PGVector(embedding_function=hyde_embeddings, ...)
```

### When HyDE Helps vs Hurts

| Scenario | HyDE Impact | Reason |
|----------|-------------|--------|
| Short, vague queries | Helps significantly | Hypothesis adds specificity |
| Well-formed specific queries | Marginal or no improvement | Query already close to answer |
| Factual lookups ("What is X?") | Helps | Hypothesis is in same semantic space |
| Queries about absence ("Why doesn't X work?") | Can hurt | Hypothesis may be incorrect, misleading retrieval |
| High-stakes / low-tolerance | Risky | Incorrect hypothesis pollutes retrieval |

HyDE adds one LLM call per query. Use it selectively for short or ambiguous queries, not as a blanket strategy.

## Multi-Query Retrieval

Generate multiple rephrased versions of the query, retrieve for each, and merge results. Covers different angles of the same question.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm
)
# Generates 3 query variants, retrieves for each, deduplicates
docs = retriever.invoke("How do I handle authentication in microservices?")
```

### Generated Query Variants Example

```
Original: "How do I handle authentication in microservices?"
Variant 1: "What are the best practices for microservice authentication?"
Variant 2: "How to implement auth between services in a distributed system?"
Variant 3: "Service-to-service authentication patterns and token management"
```

Multi-query retrieval improves recall by 15-30% on ambiguous queries at the cost of 3-5x more retrieval calls per query.

## Query Decomposition

Break complex multi-part questions into sub-questions, retrieve independently for each, then synthesize.

```python
from langchain.chains.query_constructor.base import AttributeInfo

# Complex query
query = "Compare the authentication and authorization features of AWS Cognito vs Auth0"

# Decomposed sub-queries
sub_queries = [
    "AWS Cognito authentication features and capabilities",
    "Auth0 authentication features and capabilities",
    "AWS Cognito authorization and access control features",
    "Auth0 authorization and role-based access control"
]

# Retrieve for each sub-query, then merge context
all_docs = []
for sub_q in sub_queries:
    docs = retriever.invoke(sub_q)
    all_docs.extend(docs)

# Deduplicate and send to LLM with original query
```

### When to Decompose

| Query Type | Decompose? | Rationale |
|-----------|-----------|-----------|
| Single-entity factual | No | Direct retrieval sufficient |
| Comparison ("X vs Y") | Yes | Need docs about both X and Y |
| Multi-step ("How to X then Y") | Yes | Each step may be in different docs |
| Temporal ("How has X changed") | Yes | Need docs from different time periods |
| Conditional ("If X then what about Y") | Sometimes | Depends on complexity |

## Contextual Compression

After retrieval, compress chunks to extract only the query-relevant portions. Reduces noise in the context window.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI

compressor = LLMChainExtractor.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0)
)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)
# Returns compressed versions of top-10 chunks
docs = compression_retriever.invoke("What are the API rate limits?")
```

### Compression Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| Reduces irrelevant content in context | Adds LLM call per chunk (cost + latency) |
| Fits more relevant info in context window | May accidentally remove important context |
| Improves faithfulness scores | Not suitable for latency-sensitive paths |

Use contextual compression for complex queries where retrieved chunks contain substantial irrelevant material. Skip it for simple factual lookups where chunks are already focused.

## Retrieval Strategy Selection

| Query Complexity | Strategy Stack | Latency | Cost |
|-----------------|---------------|---------|------|
| Simple factual | Vector search, k=5 | ~50ms | Low |
| Keyword-heavy technical | Hybrid (BM25 + vector + RRF) | ~100ms | Low |
| Ambiguous / short | HyDE + vector search | ~500ms | Medium (1 LLM call) |
| Broad topic | Multi-query + dedup | ~300ms | Medium (3-5 retrievals) |
| Complex comparison | Decompose + parallel retrieve | ~600ms | Medium-High |
| Maximum precision | Hybrid + reranker + compression | ~800ms | High |

Start with the simplest strategy that meets quality requirements. Add complexity only when metrics justify it.
