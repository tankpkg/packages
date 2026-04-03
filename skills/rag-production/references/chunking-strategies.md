# Chunking Strategies

Sources: LangChain Text Splitters documentation, LlamaIndex Node Parsers documentation, Pinecone chunking research (2024), Greg Kamradt (semantic chunking), Unstructured.io documentation, 2024-2026 RAG production research

Covers: fixed-size, recursive character, semantic, document-aware, parent-child, and hierarchical chunking with practical size/overlap guidance and selection framework.

## Why Chunking Matters

Chunking determines what the retriever can find. A chunk is the atomic unit of retrieval — the LLM sees exactly what chunks the retriever returns. Poor chunk boundaries cause two failures: (1) relevant information split across chunks that never surface together, and (2) irrelevant filler diluting signal within oversized chunks.

## Fixed-Size Chunking

Split text every N characters or tokens regardless of content boundaries.

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separator="\n\n"
)
chunks = splitter.split_text(document)
```

| Advantage | Disadvantage |
|-----------|-------------|
| Simple, predictable chunk count | Cuts sentences mid-thought |
| Fast processing | Ignores document structure |
| Consistent embedding dimensions | Poor for structured content |

Use fixed-size only for unstructured homogeneous text where speed matters more than precision — bulk log files, raw transcripts.

## Recursive Character Splitting

Split by a hierarchy of separators, trying the largest boundary first. LangChain's default and the most common production choice.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_documents(documents)
```

The splitter first tries double-newline (paragraph breaks), then single newline, then sentence boundaries, then word boundaries, then character-level. This preserves the largest natural boundary possible within the size constraint.

### Separator Hierarchy

| Priority | Separator | Preserves |
|----------|-----------|-----------|
| 1 | `\n\n` | Paragraph boundaries |
| 2 | `\n` | Line boundaries |
| 3 | `. ` | Sentence boundaries |
| 4 | ` ` | Word boundaries |
| 5 | `""` | Character-level (last resort) |

### Language-Specific Separators

LangChain provides language-aware separator lists:

```python
from langchain.text_splitter import Language

splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1000,
    chunk_overlap=100
)
```

Supported: Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, Markdown, HTML, LaTeX, and more. These split at function/class boundaries instead of arbitrary character positions.

## Semantic Chunking

Split based on embedding similarity between consecutive sentences. When the semantic similarity drops below a threshold, insert a chunk boundary.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

chunker = SemanticChunker(
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95
)
chunks = chunker.split_text(document)
```

### Breakpoint Methods

| Method | How It Works | Best For |
|--------|-------------|----------|
| `percentile` | Break at distances above the Nth percentile | General purpose (use 90-95) |
| `standard_deviation` | Break at distances > N standard deviations above mean | Consistent-length docs |
| `interquartile` | Break at distances > 1.5x IQR above Q3 | Outlier-resistant |
| `gradient` | Break at steepest changes in distance | Topic-shift detection |

### Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| Chunks are topically coherent | Requires embedding every sentence (cost) |
| No mid-thought splits | Variable chunk sizes (harder to predict token usage) |
| Adapts to content structure | Slower ingestion pipeline |
| No manual separator tuning | Threshold tuning required per domain |

Use semantic chunking for high-value corpora where retrieval precision justifies the extra embedding cost — legal documents, research papers, policy manuals.

## Document-Aware Chunking

Leverage document structure (headers, sections, lists) as natural chunk boundaries.

### Markdown Header Splitting

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False
)
chunks = splitter.split_text(markdown_doc)
# Each chunk includes header hierarchy as metadata
```

### HTML Header Splitting

```python
from langchain.text_splitter import HTMLHeaderTextSplitter

headers = [("h1", "Header 1"), ("h2", "Header 2"), ("h3", "Header 3")]
splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers)
chunks = splitter.split_text(html_doc)
```

### Benefits of Document-Aware Splitting

- Preserves section hierarchy as metadata (filter by section during retrieval)
- Maintains table integrity (keeps tables within a single chunk)
- Respects code block boundaries (never splits mid-function)
- Enables hierarchical retrieval (search section titles, then drill into content)

## Parent-Child (Hierarchical) Chunking

Store small chunks for precise retrieval but return the larger parent chunk to the LLM for full context. This solves the precision-vs-context dilemma.

### Architecture

```
Document
  └── Parent Chunk (2000 tokens) — stored for context
        ├── Child Chunk (200 tokens) — embedded for retrieval
        ├── Child Chunk (200 tokens) — embedded for retrieval
        └── Child Chunk (200 tokens) — embedded for retrieval
```

### LlamaIndex Implementation

```python
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import IndexNode

# Create small child nodes for embedding
child_parser = SentenceSplitter(chunk_size=200, chunk_overlap=20)
# Create larger parent nodes for context
parent_parser = SentenceSplitter(chunk_size=2000, chunk_overlap=200)

parent_nodes = parent_parser.get_nodes_from_documents(documents)
for parent in parent_nodes:
    children = child_parser.get_nodes_from_documents([parent])
    for child in children:
        child.relationships[NodeRelationship.PARENT] = parent.node_id
```

### When to Use Parent-Child

| Signal | Use Parent-Child |
|--------|-----------------|
| Answers require surrounding context | Yes — retrieve child, return parent |
| Documents have clear hierarchical structure | Yes — sections as parents, paragraphs as children |
| Chunk size trade-off is painful | Yes — small for precision, large for context |
| Simple Q&A over short documents | No — overhead not justified |

## Chunk Size and Overlap Guidelines

### Size Selection

| Chunk Size | Best For | Trade-off |
|------------|----------|-----------|
| 128-256 tokens | Precise factual retrieval (dates, names, numbers) | May lose surrounding context |
| 512 tokens | General purpose — balanced precision and context | Default recommendation |
| 1024 tokens | Documents where answers span multiple paragraphs | More noise per chunk |
| 2048+ tokens | Legal/regulatory where full clause context required | Embedding models may truncate |

### Overlap

- **10-20% of chunk size** is standard (50-100 tokens for 512-token chunks)
- Overlap ensures concepts at boundaries appear in at least one chunk
- Excessive overlap (>25%) wastes storage and adds redundant retrieval results
- Zero overlap risks losing boundary information

### Matching Chunk Size to Embedding Model

| Embedding Model | Max Tokens | Recommended Chunk Size |
|----------------|------------|----------------------|
| OpenAI text-embedding-3-small | 8191 | 512-1024 |
| OpenAI text-embedding-3-large | 8191 | 512-1024 |
| Cohere embed-v3 | 512 | 256-512 |
| sentence-transformers (all-MiniLM) | 256 | 128-256 |
| nomic-embed-text | 8192 | 512-1024 |
| BGE-large-en-v1.5 | 512 | 256-512 |

Exceeding the model's max token limit causes silent truncation — embeddings only represent the first N tokens.

## Metadata Enrichment

Attach metadata to every chunk during ingestion. Metadata enables filtered retrieval (search only within a date range, document type, or section).

### Essential Metadata Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `source` | Origin document path or URL | `docs/api-v2.md` |
| `section_title` | Nearest header | `Authentication` |
| `page_number` | For PDF pagination | `42` |
| `doc_type` | Classification | `api-docs`, `tutorial`, `changelog` |
| `created_at` | Temporal filtering | `2025-01-15` |
| `chunk_index` | Position within document | `7` (of 23) |
| `parent_id` | Link to parent chunk | `doc-123-section-2` |

### Metadata at Ingestion

```python
for i, chunk in enumerate(chunks):
    chunk.metadata.update({
        "source": document.metadata["source"],
        "chunk_index": i,
        "total_chunks": len(chunks),
        "doc_type": classify_document(document),
        "ingested_at": datetime.utcnow().isoformat()
    })
```

## Chunking Strategy Selection Framework

| Content Type | Recommended Strategy | Chunk Size | Overlap |
|-------------|---------------------|------------|---------|
| Blog posts, articles | Recursive character | 512 | 50 |
| API documentation | Markdown header + recursive | 512-1024 | 50-100 |
| Legal contracts | Semantic chunking | 1024 | 100 |
| Source code | Language-aware recursive | 1000 | 100 |
| FAQ pages | Keep each Q&A as one chunk | Variable | 0 |
| Research papers | Section-aware + semantic | 512-1024 | 50-100 |
| Chat/conversation logs | Fixed-size with timestamp metadata | 256-512 | 50 |
| Product catalogs | One chunk per product | Variable | 0 |
| Mixed-format (tables + text) | Document-aware, keep tables intact | Variable | 50 |

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| One-size-fits-all chunk size | Poor retrieval across content types | Profile content, use different strategies per type |
| No overlap | Boundary information lost | 10-20% overlap standard |
| Chunking tables row-by-row | Table context destroyed | Keep tables as single chunks |
| Ignoring code blocks | Functions split mid-body | Language-aware splitter |
| No metadata | Cannot filter by source/date | Enrich at ingestion time |
| Chunks too large (>2048) | Noise drowns signal | Prefer 512-1024 for general use |
| Re-chunking on every query | Wasted computation | Chunk once at ingestion, store permanently |
