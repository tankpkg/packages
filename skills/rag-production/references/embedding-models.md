# Embedding Models

Sources: OpenAI Embeddings documentation, Cohere Embed v3 documentation, MTEB Leaderboard (Hugging Face), Nomic AI documentation, sentence-transformers documentation, 2024-2026 embedding benchmarks

Covers: model selection, dimensionality reduction, Matryoshka embeddings, quantization, cost analysis, and production embedding patterns.

## How Embeddings Work in RAG

An embedding model converts text into a fixed-length numerical vector that captures semantic meaning. Texts with similar meaning produce vectors that are close together in high-dimensional space, measured by cosine similarity. In RAG, both document chunks and user queries are embedded with the same model, and retrieval finds the closest chunk vectors to the query vector.

## Model Comparison

### Commercial Models

| Model | Provider | Dimensions | Max Tokens | MTEB Score | Price (per 1M tokens) | Notes |
|-------|----------|-----------|------------|------------|----------------------|-------|
| text-embedding-3-small | OpenAI | 1536 (reducible) | 8191 | 62.3 | $0.02 | Best cost/performance ratio |
| text-embedding-3-large | OpenAI | 3072 (reducible) | 8191 | 64.6 | $0.13 | Highest quality commercial |
| text-embedding-ada-002 | OpenAI | 1536 (fixed) | 8191 | 61.0 | $0.10 | Legacy — migrate to v3 |
| embed-v3 (english) | Cohere | 1024 | 512 | 64.5 | $0.10 | Native compression types |
| embed-v3 (multilingual) | Cohere | 1024 | 512 | 63.0 | $0.10 | 100+ languages |
| Voyage-3 | Voyage AI | 1024 | 32000 | 67.0 | $0.06 | Long-context specialist |

### Open-Source Models

| Model | Dimensions | Max Tokens | MTEB Score | Size | Notes |
|-------|-----------|------------|------------|------|-------|
| nomic-embed-text-v1.5 | 768 | 8192 | 62.3 | 137M | Matryoshka, long context |
| BGE-large-en-v1.5 | 1024 | 512 | 63.9 | 335M | Strong general purpose |
| all-MiniLM-L6-v2 | 384 | 256 | 56.3 | 22M | Fastest, smallest |
| GTE-large | 1024 | 512 | 63.1 | 335M | Alibaba, strong multilingual |
| E5-mistral-7b-instruct | 4096 | 32768 | 66.6 | 7B | Best open-source quality |
| mxbai-embed-large-v1 | 1024 | 512 | 64.7 | 335M | Top compact model |

## Dimensionality Reduction (Matryoshka Embeddings)

OpenAI's text-embedding-3 models support Matryoshka Representation Learning — embeddings are constructed so that truncating to fewer dimensions preserves most of the semantic information.

### How It Works

The model is trained so that the first N dimensions carry the most important information. Truncating from 3072 to 256 dimensions loses some nuance but retains core semantic similarity.

```python
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="The quick brown fox jumps over the lazy dog",
    dimensions=256  # Reduce from default 1536
)
embedding = response.data[0].embedding  # len = 256
```

### Dimension vs Performance Trade-off

| Model | Full Dims | 512d | 256d | Storage Savings |
|-------|-----------|------|------|----------------|
| text-embedding-3-small | 1536 (62.3 MTEB) | 61.6 | 60.4 | 67-83% |
| text-embedding-3-large | 3072 (64.6 MTEB) | 63.4 | 62.8 | 83-92% |

For most RAG applications, 512 dimensions of `text-embedding-3-large` outperforms full 1536 dimensions of `text-embedding-3-small` while using 67% less storage.

### When to Reduce Dimensions

| Signal | Recommendation |
|--------|---------------|
| Storage or memory constrained | Reduce to 512 or 256 |
| Millions of vectors, cost-sensitive | Reduce to 512 |
| Maximum retrieval quality needed | Keep full dimensions |
| Latency-critical (search speed) | Reduce — fewer dimensions = faster distance calculation |
| Prototype / development | Reduce to 256 (cheapest) |

## Quantization

Quantization converts float32 vectors to lower-precision representations, reducing storage and improving search speed.

### Types

| Type | Precision | Storage per Dim | Speed Gain | Quality Loss |
|------|-----------|----------------|-----------|-------------|
| float32 (default) | 32 bits | 4 bytes | Baseline | None |
| float16 | 16 bits | 2 bytes | ~1.5x | Negligible |
| int8 (scalar) | 8 bits | 1 byte | ~3x | Minimal (1-2% recall drop) |
| binary | 1 bit | 0.125 bytes | ~30x | Moderate (use as first-pass filter) |

### Binary Quantization + Rescoring

Use binary quantization as a fast first-pass filter, then rescore the top candidates with full-precision vectors:

```python
# Qdrant binary quantization example
from qdrant_client import QdrantClient
from qdrant_client.models import BinaryQuantization, ScalarQuantization

client = QdrantClient("localhost", port=6333)
client.create_collection(
    collection_name="documents",
    vectors_config={"size": 1536, "distance": "Cosine"},
    quantization_config=BinaryQuantization(
        binary=BinaryQuantizationConfig(always_ram=True),
    ),
)
# Search with rescoring
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=10,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(rescore=True, oversampling=3.0)
    )
)
```

### Cohere Embedding Types

Cohere embed-v3 natively supports compression at embedding time:

```python
import cohere
co = cohere.Client()

response = co.embed(
    texts=["document chunk text here"],
    model="embed-english-v3.0",
    input_type="search_document",
    embedding_types=["float", "int8", "uint8", "binary"]
)
# Choose type based on storage/quality needs
```

## Input Type Specification

Some models perform better when told whether the input is a document or a query.

| Model | Document Prefix/Type | Query Prefix/Type |
|-------|---------------------|------------------|
| Cohere embed-v3 | `input_type="search_document"` | `input_type="search_query"` |
| nomic-embed-text | `search_document: ` prefix | `search_query: ` prefix |
| BGE models | No prefix for documents | `Represent this sentence: ` prefix |
| E5 models | `passage: ` prefix | `query: ` prefix |
| OpenAI text-embedding-3 | No prefix needed | No prefix needed |

Mismatching input types (querying with document type) degrades retrieval quality by 5-15%.

## Batch Embedding for Ingestion

Embed documents in batches during ingestion to reduce API calls and cost.

```python
from openai import OpenAI
client = OpenAI()

def batch_embed(texts, model="text-embedding-3-small", batch_size=100):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(model=model, input=batch)
        all_embeddings.extend([d.embedding for d in response.data])
    return all_embeddings
```

### Cost Estimation

| Model | 10K docs (512 tokens each) | 100K docs | 1M docs |
|-------|---------------------------|-----------|---------|
| text-embedding-3-small | $0.10 | $1.02 | $10.24 |
| text-embedding-3-large | $0.67 | $6.66 | $66.56 |
| Cohere embed-v3 | $0.51 | $5.12 | $51.20 |
| nomic-embed (self-hosted) | GPU cost only | GPU cost only | GPU cost only |

## Embedding Model Selection Framework

| Scenario | Recommended Model | Dimensions | Rationale |
|----------|------------------|-----------|-----------|
| General-purpose English RAG | text-embedding-3-small | 512-1536 | Best cost/performance |
| Maximum quality, English | text-embedding-3-large | 1024-3072 | Highest MTEB commercial |
| Multilingual RAG | Cohere embed-v3-multilingual | 1024 | 100+ languages |
| Long documents (>4K tokens) | Voyage-3 or nomic-embed | 1024/768 | 32K/8K context windows |
| Air-gapped / on-premises | nomic-embed-text-v1.5 | 768 | Open-source, self-hosted |
| Minimum cost prototype | all-MiniLM-L6-v2 | 384 | Free, 22MB, runs on CPU |
| Code-specific retrieval | Voyage-code-2 | 1536 | Trained on code corpora |

## Distance Metrics

Vector databases support multiple distance metrics. The choice depends on the embedding model and use case.

| Metric | Formula | Range | When to Use |
|--------|---------|-------|-------------|
| Cosine Similarity | dot(a,b) / (norm(a) * norm(b)) | -1 to 1 | Default for most embeddings (OpenAI, Cohere) |
| Dot Product | dot(a,b) | Unbounded | Pre-normalized vectors (same as cosine, faster) |
| Euclidean (L2) | sqrt(sum((a-b)^2)) | 0 to inf | When magnitude matters |

Most embedding models produce normalized vectors, making cosine similarity and dot product equivalent. Verify normalization before choosing dot product for speed:

```python
import numpy as np

embedding = get_embedding("sample text")
norm = np.linalg.norm(embedding)
print(f"Norm: {norm:.4f}")  # Should be ~1.0 for normalized vectors
# If 1.0: cosine == dot product, use dot product (faster)
# If not 1.0: must use cosine similarity
```

### Matching Metric to Database

| Database | Configure As |
|----------|-------------|
| Pinecone | `metric="cosine"` at index creation |
| Qdrant | `distance=Distance.COSINE` in collection config |
| pgvector | `vector_cosine_ops` for HNSW/IVFFlat index |
| Weaviate | `distanceMetric: "cosine"` in schema |
| Chroma | Cosine by default |

Changing the distance metric after index creation requires rebuilding the entire index. Choose correctly at the start.

## Embedding Normalization and Preprocessing

### Text Preprocessing Before Embedding

Clean text before embedding to improve vector quality:

```python
def preprocess_for_embedding(text: str) -> str:
    # Remove excessive whitespace
    text = " ".join(text.split())
    # Remove special characters that add noise
    text = text.replace("\x00", "").replace("\ufeff", "")
    # Truncate to model max tokens (with safety margin)
    if len(text) > 30000:  # Approximate character limit
        text = text[:30000]
    return text.strip()
```

### Embedding Warm-Up for Self-Hosted Models

Self-hosted models (sentence-transformers, nomic) have cold-start latency. Warm up the model before serving:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5")

# Warm-up: run a dummy encode to load model into GPU memory
_ = model.encode(["warm up"], show_progress_bar=False)

# Now ready for production queries with consistent latency
```

## Migrating Embedding Models

Switching embedding models requires re-embedding the entire corpus because vectors from different models occupy different vector spaces and are not comparable.

### Migration Checklist

1. Compute cost estimate: (corpus_tokens / 1M) * price_per_1M_tokens
2. Provision storage for new index (can run alongside old)
3. Batch re-embed all documents with new model
4. Create new vector database collection/index
5. Run evaluation on test set with new embeddings
6. Compare RAGAS metrics (old vs new pipeline)
7. If quality improves or matches: switch traffic
8. Keep old index available for rollback (7-14 days)
9. Delete old index after confirmation

### Cost of Migration

| Corpus Size | text-embedding-3-small | text-embedding-3-large |
|-------------|----------------------|----------------------|
| 100K chunks (512 tokens) | $1.02 | $6.66 |
| 1M chunks | $10.24 | $66.56 |
| 10M chunks | $102.40 | $665.60 |

Factor migration cost into embedding model decisions — cheaper models reduce the cost of future re-embedding.

## Self-Hosting Considerations

### When to Self-Host

| Signal | Self-Host | Use API |
|--------|----------|---------|
| Data cannot leave your infrastructure | Yes | No |
| >1M queries/day | Yes (cost break-even) | Expensive |
| Air-gapped environment | Yes (only option) | Impossible |
| Prototype / low volume | No (ops overhead) | Yes |
| Need latest model immediately | No (deployment lag) | Yes |

### Self-Hosted Performance Targets

| Model | Hardware | Throughput | Latency |
|-------|----------|------------|---------|
| all-MiniLM-L6-v2 | CPU (4 cores) | ~500 texts/sec | ~2ms |
| nomic-embed-text-v1.5 | GPU (T4) | ~200 texts/sec | ~5ms |
| BGE-large-en-v1.5 | GPU (T4) | ~100 texts/sec | ~10ms |
| E5-mistral-7b-instruct | GPU (A100) | ~20 texts/sec | ~50ms |

Use text-embedding-inference (TEI) from Hugging Face for optimized self-hosted serving with batching, quantization, and OpenAI-compatible API.

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Different models for indexing vs querying | Vectors in different spaces — zero relevance | Use the same model for both |
| Embedding full documents (no chunking) | Truncation at max tokens, diluted semantics | Chunk first, then embed |
| Not specifying input_type | 5-15% quality loss on asymmetric models | Use correct document/query types |
| Re-embedding unchanged documents | Wasted API cost | Hash content, skip unchanged |
| Ignoring max token limits | Silent truncation | Verify chunk size < model max tokens |
| Using ada-002 in new projects | Lower quality, higher cost than v3 | Migrate to text-embedding-3-small |
| Float32 at scale without considering quantization | 4x storage overhead | Use int8 or binary + rescore |
