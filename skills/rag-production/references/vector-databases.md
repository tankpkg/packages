# Vector Databases

Sources: Pinecone documentation, Weaviate documentation, Qdrant documentation, pgvector documentation, Chroma documentation, Milvus documentation, 2024-2026 vector database benchmarks

Covers: database selection, indexing algorithms (HNSW, IVF), operational trade-offs, managed vs self-hosted, scaling patterns, and migration considerations.

## Vector Database Role in RAG

A vector database stores embedding vectors and performs approximate nearest neighbor (ANN) search to find the most semantically similar chunks to a query. The choice of vector database determines search latency, scalability, operational complexity, and available features like filtering and hybrid search.

## Database Comparison Matrix

| Database | Type | Hosting | Hybrid Search | Metadata Filtering | Max Vectors | Pricing Model |
|----------|------|---------|--------------|-------------------|-------------|---------------|
| Pinecone | Purpose-built | Managed only | Yes (sparse-dense) | Yes | Billions | Pay-per-use (serverless) |
| Weaviate | Purpose-built | Managed + self-hosted | Yes (BM25 + vector) | Yes | Billions | Open-source + managed |
| Qdrant | Purpose-built | Managed + self-hosted | Yes (sparse vectors) | Yes (payload filtering) | Billions | Open-source + managed |
| pgvector | PostgreSQL extension | Self-hosted (any PG host) | Yes (tsvector + vector) | Yes (SQL WHERE) | Millions | Part of PG hosting |
| Chroma | Embedded | Local / self-hosted | No (vector only) | Yes (basic) | Millions | Open-source |
| Milvus | Purpose-built | Managed (Zilliz) + self-hosted | Yes (sparse + dense) | Yes | Billions+ | Open-source + managed |
| MongoDB Atlas | Multi-model | Managed | Yes (text + vector) | Yes (MQL) | Millions | Part of Atlas pricing |

## Pinecone

Best for teams that want zero operational overhead with production-grade performance.

### Serverless Architecture

Pinecone Serverless separates storage and compute. Pay only for reads, writes, and storage — no idle cluster costs.

```python
from pinecone import Pinecone

pc = Pinecone(api_key="YOUR_API_KEY")
index = pc.Index("my-rag-index")

# Upsert with metadata
index.upsert(vectors=[
    {"id": "doc-1-chunk-3", "values": embedding, "metadata": {
        "source": "api-docs.md",
        "section": "authentication",
        "doc_type": "technical"
    }}
])

# Query with metadata filter
results = index.query(
    vector=query_embedding,
    top_k=10,
    filter={"doc_type": {"$eq": "technical"}},
    include_metadata=True
)
```

### Pinecone Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| Zero ops — fully managed | Vendor lock-in (no self-hosted option) |
| Serverless pricing (no idle cost) | Higher per-query cost at scale |
| Built-in sparse-dense hybrid search | Data leaves your infrastructure |
| Automatic scaling | Limited customization of indexing |
| Namespaces for multi-tenancy | No on-premises deployment |

## Weaviate

Best for teams needing native hybrid search with strong multi-tenancy support.

### Built-in Hybrid Search

Weaviate combines BM25 keyword search with vector search natively, with configurable fusion.

```python
import weaviate

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=weaviate.auth.AuthApiKey("YOUR_API_KEY")
)

collection = client.collections.get("Documents")
results = collection.query.hybrid(
    query="authentication best practices",
    alpha=0.5,  # 0=pure keyword, 1=pure vector
    limit=10,
    filters=weaviate.classes.query.Filter.by_property("doc_type").equal("technical")
)
```

### Multi-tenancy

Weaviate supports native multi-tenancy — each tenant's data is isolated at the storage level, not just filtered at query time. Critical for SaaS applications.

```python
collection = client.collections.create(
    name="Documents",
    multi_tenancy_config=weaviate.classes.config.Configure.multi_tenancy(enabled=True)
)
collection.tenants.create([Tenant(name="tenant-a"), Tenant(name="tenant-b")])
```

## Qdrant

Best for maximum performance with self-hosted flexibility and advanced filtering.

### Payload Filtering + Vector Search

Qdrant applies filters before vector search (pre-filtering), which is more efficient than post-filtering when filters are selective.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient("localhost", port=6333)

results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="doc_type", match=MatchValue(value="technical")),
            FieldCondition(key="created_at", range=Range(gte="2025-01-01"))
        ]
    ),
    limit=10,
    search_params=SearchParams(hnsw_ef=128, exact=False)
)
```

### Quantization Support

Qdrant supports scalar (int8) and binary quantization with automatic rescoring:

```python
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig

client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type=ScalarType.INT8, quantile=0.99, always_ram=True)
    )
)
```

Scalar quantization reduces RAM usage by 4x with less than 1% recall loss. Binary quantization reduces by 32x but requires rescoring for acceptable quality.

## pgvector

Best for teams already using PostgreSQL who want to avoid a separate database.

### Setup and Indexing

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index (recommended for most cases)
CREATE INDEX ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- IVFFlat index (faster build, lower recall)
CREATE INDEX ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 1000);
```

### Hybrid Search with tsvector

```sql
-- Add full-text search column
ALTER TABLE document_chunks ADD COLUMN tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX ON document_chunks USING gin(tsv);

-- Hybrid query: combine vector similarity + BM25
WITH vector_results AS (
    SELECT id, content, metadata,
           1 - (embedding <=> $1::vector) AS vector_score
    FROM document_chunks
    ORDER BY embedding <=> $1::vector
    LIMIT 50
),
text_results AS (
    SELECT id, content, metadata,
           ts_rank(tsv, plainto_tsquery('english', $2)) AS text_score
    FROM document_chunks
    WHERE tsv @@ plainto_tsquery('english', $2)
    LIMIT 50
)
-- Reciprocal Rank Fusion
SELECT COALESCE(v.id, t.id) AS id,
       COALESCE(v.content, t.content) AS content,
       COALESCE(1.0/(60 + v.rank), 0) + COALESCE(1.0/(60 + t.rank), 0) AS rrf_score
FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY vector_score DESC) AS rank FROM vector_results) v
FULL OUTER JOIN (SELECT *, ROW_NUMBER() OVER (ORDER BY text_score DESC) AS rank FROM text_results) t
ON v.id = t.id
ORDER BY rrf_score DESC
LIMIT 10;
```

### pgvector Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| No new infrastructure (use existing PG) | Performance degrades past ~5M vectors |
| Full SQL power for filtering | No built-in sharding for vectors |
| ACID transactions with vector data | Manual hybrid search implementation |
| Mature ecosystem (backups, monitoring) | HNSW index build is memory-intensive |
| Hybrid search via tsvector | No managed vector-specific features |

### pgvector Performance Tuning

```sql
-- Increase work_mem for HNSW index builds
SET maintenance_work_mem = '2GB';

-- Search quality vs speed trade-off
SET hnsw.ef_search = 100;  -- Higher = better recall, slower (default: 40)

-- For IVFFlat, probe more lists for better recall
SET ivfflat.probes = 10;  -- Default: 1, higher = better recall
```

## Chroma

Best for local development, prototyping, and small-scale applications.

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection("documents")

collection.add(
    ids=["doc-1", "doc-2"],
    embeddings=[embedding_1, embedding_2],
    documents=["chunk text 1", "chunk text 2"],
    metadatas=[{"source": "doc.md"}, {"source": "doc.md"}]
)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"source": "doc.md"}
)
```

Chroma runs in-process (no server required), making it ideal for notebooks and prototypes. Migrate to Qdrant, Pinecone, or pgvector for production.

## Indexing Algorithms

### HNSW (Hierarchical Navigable Small World)

The default algorithm for most vector databases. Builds a multi-layer graph where higher layers enable fast navigation to the approximate neighborhood, and lower layers refine the search.

| Parameter | Effect | Recommended |
|-----------|--------|-------------|
| `M` (connections per node) | Higher = better recall, more memory | 16 (general), 32 (high recall) |
| `ef_construction` | Build-time search width; higher = better graph | 200-400 |
| `ef_search` | Query-time search width; higher = better recall | 100-200 |

### IVFFlat (Inverted File with Flat Quantization)

Partitions vectors into clusters (Voronoi cells). Faster to build than HNSW, lower recall.

| Parameter | Effect | Recommended |
|-----------|--------|-------------|
| `lists` (clusters) | More = finer partitions | sqrt(N) to N/1000 |
| `probes` | Clusters searched per query | 5-20% of lists |

### Selection Guide

| Signal | Algorithm |
|--------|----------|
| Read-heavy, quality critical | HNSW |
| Frequent index rebuilds, large datasets | IVFFlat (faster build) |
| RAM constrained | IVFFlat + quantization |
| < 100K vectors | Flat (brute force) — exact results |

## Scaling Patterns

### Vertical Scaling

Increase RAM and CPU on a single node. Effective up to ~10M vectors with HNSW (requires vectors in RAM for speed).

### Horizontal Scaling (Sharding)

| Strategy | How | When |
|----------|-----|------|
| By tenant | Each tenant on separate shard | Multi-tenant SaaS |
| By document type | Separate collections per type | Heterogeneous corpora |
| Hash-based | Consistent hash on document ID | Uniform distribution needed |

### Collection-per-Tenant vs Filtering

| Approach | Pros | Cons |
|----------|------|------|
| Shared collection + metadata filter | Simple ops, shared index | Filter overhead, data co-location |
| Collection per tenant | Perfect isolation, no filter cost | Ops overhead, many small indexes |
| Weaviate multi-tenancy | Storage isolation, single API | Weaviate-specific feature |

For fewer than 100 tenants: shared collection with metadata filters. For 100+ tenants with strict isolation: per-tenant collections or Weaviate multi-tenancy.

## Migration Between Databases

Moving from one vector database to another requires re-indexing but not re-embedding (embeddings are portable).

### Migration Checklist

1. Export chunk text + metadata + embeddings from source
2. Verify embedding dimensions match target configuration
3. Create target collection with matching distance metric (cosine, dot product, Euclidean)
4. Batch import embeddings + metadata into target
5. Verify result quality on a test query set before switching traffic
6. Keep source database running in parallel until verification passes

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Choosing DB before understanding query patterns | Feature mismatch | Map queries first, then select |
| No metadata filtering | Full-corpus search for tenant-specific queries | Add tenant/type metadata at ingestion |
| Default HNSW parameters | Suboptimal recall or speed | Tune ef_search based on recall requirements |
| Storing raw text in vector DB | Bloated storage | Store text in regular DB, reference by ID |
| No index on pgvector | Brute-force search at query time | Create HNSW index after initial load |
| Single collection for everything | Cannot tune per-content-type | Separate collections for different content types |
