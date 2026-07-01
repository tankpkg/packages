# Advanced RAG

Sources: Asai et al. (Self-RAG, 2023), Yan et al. (CRAG, 2024), Microsoft Research (GraphRAG, 2024), Sarthi et al. (RAPTOR, 2024), LlamaIndex Agentic RAG documentation, LangGraph documentation, 2024-2026 advanced RAG research

Covers: agentic RAG, self-RAG, corrective RAG (CRAG), graph RAG (Microsoft GraphRAG), RAPTOR, multimodal RAG, late chunking, and query routing.

## Agentic RAG

Standard RAG retrieves on every query. Agentic RAG uses an LLM agent that decides when, what, and how to retrieve — treating retrieval as a tool the agent can invoke selectively.

### Why Agentic RAG

| Standard RAG | Agentic RAG |
|-------------|-------------|
| Always retrieves | Retrieves only when needed |
| Single retrieval pass | Multiple retrieval passes possible |
| Fixed retrieval strategy | Adapts strategy to query type |
| Retrieves then generates | Can interleave retrieval and reasoning |
| Cannot combine data sources | Can query multiple indexes, APIs, databases |

### Tool-Use Pattern

```python
from langchain.agents import create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool

# Define retrieval as a tool
docs_tool = create_retriever_tool(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    name="search_documentation",
    description="Search the technical documentation. Use this when the user asks about API features, configuration, or troubleshooting."
)

api_tool = create_retriever_tool(
    retriever=api_vectorstore.as_retriever(search_kwargs={"k": 5}),
    name="search_api_reference",
    description="Search the API reference. Use for endpoint details, parameters, response schemas."
)

# Agent decides which tool to use (or none)
agent = create_tool_calling_agent(
    llm=ChatOpenAI(model="gpt-4o"),
    tools=[docs_tool, api_tool],
    prompt=agent_prompt
)
```

### LangGraph Agentic RAG

```python
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    question: str
    context: list[str]
    answer: str
    retrieval_needed: bool

def should_retrieve(state: AgentState) -> str:
    """Agent decides if retrieval is needed."""
    response = llm.invoke(
        f"Does this question require looking up documentation? "
        f"Question: {state['question']} Answer YES or NO."
    )
    return "retrieve" if "YES" in response.content else "generate"

def retrieve(state: AgentState) -> AgentState:
    docs = retriever.invoke(state["question"])
    return {"context": [d.page_content for d in docs]}

def generate(state: AgentState) -> AgentState:
    answer = llm.invoke(build_prompt(state["question"], state["context"]))
    return {"answer": answer.content}

def grade_answer(state: AgentState) -> str:
    """Check if answer is grounded in context."""
    score = faithfulness_check(state["answer"], state["context"])
    return "accept" if score > 0.8 else "retry_retrieve"

graph = StateGraph(AgentState)
graph.add_node("decide", should_retrieve)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("grade", grade_answer)
graph.add_edge("decide", "retrieve")  # conditional
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "grade")
graph.add_conditional_edges("grade", {"accept": END, "retry_retrieve": "retrieve"})
```

### When to Use Agentic RAG

| Signal | Standard RAG | Agentic RAG |
|--------|-------------|-------------|
| Uniform query types | Sufficient | Overkill |
| Mix of retrievable and general queries | Retrieves unnecessarily | Agent skips retrieval for general knowledge |
| Multiple data sources | Awkward merging | Agent selects appropriate source |
| Multi-step reasoning | Single-pass retrieval | Iterative retrieve-reason cycles |
| Cost-sensitive at scale | Lower cost per query | Higher (LLM routing overhead) |

## Self-RAG

Self-RAG (Asai et al., 2023) trains the LLM to generate special reflection tokens that control retrieval and evaluate its own output. The model decides mid-generation whether to retrieve, then self-evaluates whether retrieved passages are relevant and whether its generation is grounded.

### Reflection Tokens

| Token | Purpose | Values |
|-------|---------|--------|
| `[Retrieve]` | Should I retrieve? | `yes`, `no`, `continue` |
| `[IsRel]` | Is retrieved passage relevant? | `relevant`, `irrelevant` |
| `[IsSup]` | Is generation supported by passage? | `fully supported`, `partially supported`, `no support` |
| `[IsUse]` | Is generation useful to the query? | `5` (best) to `1` (worst) |

### Self-RAG Flow

```
1. Model begins generating
2. Model outputs [Retrieve=yes] — triggers retrieval
3. Retriever returns passages
4. Model evaluates [IsRel=relevant] for each passage
5. Model generates answer with relevant passages
6. Model self-evaluates [IsSup=fully supported]
7. If not supported → retry with different passages
```

### Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| Model controls its own retrieval | Requires fine-tuned model (not plug-and-play) |
| Built-in hallucination detection | Training data with reflection tokens needed |
| Adaptive retrieval (only when needed) | Higher latency from self-evaluation |

## Corrective RAG (CRAG)

CRAG (Yan et al., 2024) adds a retrieval evaluator that grades retrieved documents before generation. If retrieval quality is insufficient, CRAG triggers corrective actions.

### CRAG Pipeline

```
Query → Retriever → Retrieved Docs
                         |
                 [Retrieval Evaluator]
                    /     |      \
              Correct  Ambiguous  Incorrect
                |         |          |
            Use as-is  Refine    Web search
                |      knowledge    fallback
                |      stripping      |
                \        |          /
                 [Knowledge Refinement]
                         |
                    [Generation]
```

### Implementation Pattern

```python
def crag_pipeline(query: str) -> str:
    docs = retriever.invoke(query)
    
    # Grade retrieval quality
    grade = evaluate_retrieval(query, docs)
    
    if grade == "correct":
        # High confidence — use retrieved docs directly
        context = docs
    elif grade == "ambiguous":
        # Medium confidence — extract only relevant sentences
        context = [extract_relevant_sentences(doc, query) for doc in docs]
    else:
        # Low confidence — fallback to web search
        web_results = web_search(query)
        context = web_results + docs  # Combine both
    
    return generate(query, context)
```

## Microsoft GraphRAG

GraphRAG builds a knowledge graph from documents, then uses graph structure for retrieval. Excels at queries requiring synthesis across multiple documents or understanding entity relationships.

### Pipeline

```
Documents → [Entity Extraction] → Entities + Relationships
    → [Community Detection (Leiden)] → Hierarchical communities
    → [Community Summarization] → Summary per community at each level
    → [Indexing] → Graph + vector index of summaries
```

### Query Modes

| Mode | How It Works | Best For |
|------|-------------|----------|
| Local Search | Embed query → find similar entities → traverse neighbors → synthesize | Specific entity questions |
| Global Search | Map query to community summaries → reduce across levels | Thematic / synthesis questions |
| DRIFT Search | Start global → progressively drill into local communities | Exploratory questions |

### GraphRAG vs Standard RAG

| Query Type | Standard RAG | GraphRAG |
|-----------|-------------|----------|
| "What is X?" | Good | Equivalent |
| "What are the main themes?" | Poor (no global view) | Strong (community summaries) |
| "How are X and Y related?" | Poor (single-chunk retrieval) | Strong (graph traversal) |
| "What depends on X?" | Cannot traverse | Strong (relationship traversal) |

### Cost Considerations

GraphRAG indexing requires LLM calls for entity extraction and community summarization:

| Corpus Size | Indexing Cost (GPT-4o-mini) | Indexing Cost (GPT-4o) |
|-------------|---------------------------|----------------------|
| 10K tokens | ~$0.50 | ~$5 |
| 100K tokens | ~$5 | ~$50 |
| 1M tokens | ~$50 | ~$500 |

Use GPT-4o-mini for entity extraction and GPT-4o only for final community summarization to reduce costs 5-10x.

### LlamaIndex PropertyGraphIndex

```python
from llama_index.core import PropertyGraphIndex

index = PropertyGraphIndex.from_documents(
    documents,
    llm=ChatOpenAI(model="gpt-4o-mini"),
    embed_model=OpenAIEmbeddings(model="text-embedding-3-small"),
    show_progress=True
)

# Query with graph-aware retrieval
query_engine = index.as_query_engine(
    include_text=True,
    response_mode="tree_summarize",
    similarity_top_k=5
)
response = query_engine.query("How are authentication and rate limiting related?")
```

## RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)

RAPTOR recursively clusters and summarizes chunks into a tree structure. Leaf nodes are original chunks; higher nodes are progressively more abstract summaries. At query time, retrieve from multiple tree levels simultaneously.

### RAPTOR Tree Structure

```
Level 3: [Global summary of entire corpus]
Level 2: [Topic cluster summary A] [Topic cluster summary B]
Level 1: [Section summary 1] [Section summary 2] [Section summary 3]
Level 0: [chunk] [chunk] [chunk] [chunk] [chunk] [chunk] [chunk]
```

### When RAPTOR Beats Flat RAG

| Scenario | Flat RAG | RAPTOR |
|----------|---------|--------|
| Detail + overview needed | Must retrieve many chunks | Retrieves from appropriate level |
| Long document understanding | Chunks lose global context | Tree preserves hierarchy |
| "Summarize the main points" | Struggles without all chunks | Higher-level nodes already summarize |
| Specific fact lookup | Works well | Works well (leaf level) |

## Multimodal RAG

Extend RAG beyond text to handle images, tables, charts, and diagrams in documents.

### Architecture Options

| Approach | Description | Pros | Cons |
|----------|------------|------|------|
| Text extraction only | OCR all visual content to text | Simple, cheap | Loses visual information |
| VLM description | Use vision model to describe images | Rich descriptions | Expensive per image |
| Multimodal embeddings | Embed images and text together (CLIP) | Fast retrieval | Less granular |
| Dual representation | Text chunks + image descriptions separately | Best coverage | Complex pipeline |

### Production Multimodal Pipeline

```python
def ingest_document(doc_path: str):
    # Extract text, images, and tables separately
    text_chunks = extract_and_chunk_text(doc_path)
    images = extract_images(doc_path)
    tables = extract_tables(doc_path)
    
    # Generate descriptions for images
    for img in images:
        description = vision_model.describe(
            img, prompt="Describe this image in detail, including any text, "
                       "data, or relationships shown."
        )
        img.text_description = description
    
    # Convert tables to both JSON and prose
    for table in tables:
        table.json_repr = table.to_json()
        table.prose_repr = llm.invoke(
            f"Convert this table to a paragraph: {table.to_markdown()}"
        )
    
    # Embed all content types
    all_chunks = text_chunks + [img.text_description for img in images] + \
                 [t.prose_repr for t in tables]
    embed_and_store(all_chunks)
```

### Key Multimodal Guidelines

- Cache VLM descriptions at ingestion time — images do not change, descriptions are expensive
- Keep tables as single chunks — never split a table across chunk boundaries
- Pair figures with their captions — a caption provides essential context for retrieval
- Use dual retrieval: text-based search for descriptions, image similarity for visual queries

## Late Chunking

Late chunking (Jina AI, 2024) embeds the full document through a long-context model first, then chunks the embedding sequence. Each chunk's embedding retains awareness of the full document context, unlike traditional chunk-then-embed approaches.

### Traditional vs Late Chunking

| Step | Traditional | Late Chunking |
|------|-----------|--------------|
| 1 | Chunk document | Embed full document (long-context model) |
| 2 | Embed each chunk independently | Chunk the embedding sequence |
| 3 | Each chunk embedding knows only its own text | Each chunk embedding knows full document context |

### Trade-offs

| Advantage | Disadvantage |
|-----------|-------------|
| Chunks have document-level context | Requires long-context embedding model |
| Better for pronouns/references across chunks | Not supported by all models |
| Improved retrieval for context-dependent text | Higher ingestion latency |

## Query Routing

Route queries to different retrieval strategies based on query classification.

```python
def route_query(query: str) -> str:
    classification = llm.invoke(
        f"Classify this query into one category: "
        f"FACTUAL, COMPARISON, SYNTHESIS, CODE, UNANSWERABLE. "
        f"Query: {query}"
    )
    
    routing = {
        "FACTUAL": lambda q: vector_search(q, k=3),
        "COMPARISON": lambda q: decompose_and_retrieve(q),
        "SYNTHESIS": lambda q: multi_query_retrieve(q),
        "CODE": lambda q: code_index_search(q, k=5),
        "UNANSWERABLE": lambda q: graceful_decline(q)
    }
    
    return routing.get(classification.strip(), vector_search)(query)
```

### Routing Decision Matrix

| Query Type | Retrieval Strategy | Example |
|-----------|-------------------|---------|
| Factual | Single vector search, k=3-5 | "What is the rate limit?" |
| Comparison | Query decomposition + parallel retrieval | "Compare plan A vs plan B" |
| Synthesis | Multi-query + RAPTOR higher levels | "Summarize the main features" |
| Relationship | GraphRAG local search | "How are auth and billing related?" |
| Code | Code-specific index + language-aware chunks | "Show me the auth middleware" |
| Ambiguous | HyDE + multi-query expansion | "How does it work?" |
| Conversational | Query rewriting + context carry-forward | Follow-up questions |

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Using agentic RAG for simple Q&A | Unnecessary latency and cost | Start with standard RAG, upgrade when needed |
| GraphRAG on small corpora (<100 docs) | Overhead exceeds benefit | Use standard RAG; GraphRAG shines at 1000+ docs |
| No fallback when advanced retrieval fails | Silent failures | Implement tiered fallback (see production-operations.md) |
| Multimodal without caching VLM descriptions | Re-describing images per query | Cache descriptions at ingestion |
| Routing without measuring | Cannot justify complexity | A/B test routing vs uniform strategy |
