# Context Assembly

Sources: Liu et al. (Lost in the Middle, 2023), LangChain prompt engineering documentation, Anthropic prompt design documentation, OpenAI best practices, 2024-2026 RAG production research

Covers: prompt construction for RAG, citation and attribution, lost-in-the-middle mitigation, context window budgeting, source deduplication, and faithfulness-preserving patterns.

## The Role of Context Assembly

Context assembly is the bridge between retrieval and generation. After retrieval returns ranked chunks, context assembly decides how to format, order, and present those chunks to the LLM. Poor context assembly wastes good retrieval — the model may ignore relevant chunks, hallucinate despite having the answer, or produce responses without verifiable citations.

## Prompt Construction

### Standard RAG Prompt Structure

```
[System Instructions]
  - Role and behavior constraints
  - Citation format requirements
  - Hallucination guardrails

[Retrieved Context]
  - Document chunks with source metadata
  - Ordered by relevance or strategically positioned

[Conversation History] (if multi-turn)
  - Previous Q&A pairs

[Current Query]
  - User's question
```

### System Prompt Template

```
You are a helpful assistant that answers questions based on the provided context.

RULES:
- Answer ONLY based on the provided context documents
- Cite sources using [n] notation after each claim
- If the context does not contain sufficient information to answer, say:
  "Based on the available documentation, I cannot fully answer this question."
- Never fabricate information that is not in the provided context
- If different sources contain conflicting information, acknowledge both and cite each
```

### Context Formatting Patterns

#### Pattern 1: Numbered Documents with Metadata

```
Context Documents:

[1] Source: api-reference-v3.md | Section: Rate Limits | Updated: 2025-06-15
The API enforces rate limits of 100 requests per minute for free tier accounts
and 1000 requests per minute for paid tier accounts. Exceeding the limit returns
HTTP 429 with a Retry-After header.

[2] Source: faq.md | Section: Billing | Updated: 2025-08-01
Rate limit increases are available for Enterprise customers. Contact sales
for custom limits above 1000 RPM.

[3] Source: changelog-v3.2.md | Section: Breaking Changes | Updated: 2025-09-10
Rate limit headers now use the standard RateLimit-* header format per RFC 9110,
replacing the previous X-RateLimit-* headers.
```

#### Pattern 2: Structured XML-Style Tags

```xml
<context>
  <document id="1" source="api-reference-v3.md" section="Rate Limits" relevance="high">
    The API enforces rate limits of 100 requests per minute for free tier...
  </document>
  <document id="2" source="faq.md" section="Billing" relevance="medium">
    Rate limit increases are available for Enterprise customers...
  </document>
</context>
```

XML-style tags work well with Claude models, which are trained to respect XML structure.

#### Pattern 3: Minimal (for Simple Use Cases)

```
Based on the following information:
---
{chunk_1}
---
{chunk_2}
---
Answer the question: {query}
```

### Format Selection

| Pattern | Best For | Trade-off |
|---------|----------|-----------|
| Numbered with metadata | Production systems needing citations | More tokens consumed |
| XML-style tags | Anthropic Claude models | Verbose but structured |
| Minimal | Prototypes, simple Q&A | No source tracking |

## Lost-in-the-Middle Problem

Research by Liu et al. (2023) demonstrated that LLMs perform significantly better when relevant information is positioned at the beginning or end of the context window. Information in the middle is systematically underweighted, even in models with 100K+ context windows.

### Measured Impact

| Position of Answer | Performance |
|-------------------|------------|
| First chunk (position 1) | Highest accuracy |
| Last chunk (position N) | Second highest |
| Middle positions (3-7 of 10) | Significant degradation |

This is not a model bug — it reflects attention patterns in transformer architectures. The primacy and recency effects are consistent across model families.

### Mitigation Strategies

#### Strategy 1: Relevance-Ordered Positioning

Place the most relevant chunk first and second-most relevant last:

```python
def reorder_chunks(chunks: list, scores: list) -> list:
    if len(chunks) <= 2:
        return chunks
    
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    best = ranked[0][0]
    second_best = ranked[1][0]
    rest = [c for c, _ in ranked[2:]]
    
    return [best] + rest + [second_best]
```

#### Strategy 2: Fewer, Better Chunks

Reduce the number of chunks rather than stuffing the context window:

| Approach | When to Use |
|----------|------------|
| Top-3 highly relevant | Simple factual queries |
| Top-5 with reranking | General Q&A |
| Top-10 with compression | Complex multi-faceted queries |
| Dynamic sizing by score threshold | Adaptive — varies per query |

```python
def dynamic_context_size(chunks: list, scores: list, threshold: float = 0.5) -> list:
    return [c for c, s in zip(chunks, scores) if s >= threshold]
```

#### Strategy 3: Contextual Compression

Extract only query-relevant sentences from each chunk before assembly:

```python
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0)
)
# Each chunk is compressed to only query-relevant content
```

#### Strategy 4: Explicit Relevance Markers

Add relevance signals that the model can use to prioritize:

```
[DOCUMENT 1 - HIGHLY RELEVANT]
Source: api-reference-v3.md, Section: Rate Limits
This document directly addresses the question about rate limits.
Content: The API enforces rate limits of 100 requests per minute...

[DOCUMENT 2 - PARTIALLY RELEVANT]
Source: faq.md, Section: Billing
This document contains supplementary information.
Content: Rate limit increases are available for Enterprise...
```

## Citation and Attribution

### Inline Citation Format

Train the model to cite as it generates:

```
The API enforces rate limits of 100 requests per minute for free tier [1] and
1000 requests per minute for paid tier [1]. Enterprise customers can request
custom limits [2]. As of v3.2, rate limit headers follow RFC 9110 format [3].

Sources:
[1] api-reference-v3.md, Section: Rate Limits
[2] faq.md, Section: Billing
[3] changelog-v3.2.md, Section: Breaking Changes
```

### Citation Verification

Post-process the response to verify that cited claims exist in the referenced chunks:

```python
def verify_citations(response: str, chunks: dict) -> dict:
    citations = extract_citations(response)  # Parse [n] references
    verified = {}
    for ref_num, claim_text in citations.items():
        source_chunk = chunks.get(ref_num)
        if source_chunk and claim_text_in_chunk(claim_text, source_chunk):
            verified[ref_num] = "verified"
        else:
            verified[ref_num] = "unverified"
    return verified
```

### Handling Missing Context

When retrieved chunks do not contain the answer:

```python
system_prompt = """
If the provided context does not contain sufficient information to answer
the question:
1. State clearly: "Based on the available documentation, I cannot fully
   answer this question."
2. Provide whatever partial answer IS supported by the context
3. Suggest what additional information would be needed
4. Never fabricate an answer from general knowledge
"""
```

## Context Window Budget

### Token Allocation Strategy

For a 128K context window model:

| Component | Tokens | Percentage | Notes |
|-----------|--------|------------|-------|
| System prompt | 500-2,000 | 1-2% | Instructions, role, format |
| Retrieved context | 10,000-60,000 | 8-47% | Main variable |
| Conversation history | 5,000-20,000 | 4-16% | Multi-turn only |
| Current query | 100-500 | <1% | User question |
| Output buffer | 2,000-8,000 | 2-6% | Expected response length |
| Safety margin | 5,000-10,000 | 4-8% | Prevents truncation |

### Adaptive Context Sizing

```python
def compute_context_budget(
    model_context_window: int,
    system_prompt_tokens: int,
    conversation_history_tokens: int,
    max_output_tokens: int,
    safety_margin: int = 500
) -> int:
    return (model_context_window
            - system_prompt_tokens
            - conversation_history_tokens
            - max_output_tokens
            - safety_margin)

# Example: GPT-4o with 128K context
budget = compute_context_budget(
    model_context_window=128000,
    system_prompt_tokens=1500,
    conversation_history_tokens=10000,
    max_output_tokens=4000,
    safety_margin=500
)
# budget = 112,000 tokens available for retrieved context
```

### Context Utilization Monitoring

Track what percentage of retrieved context actually contributes to the answer:

```python
def context_utilization(response: str, chunks: list) -> float:
    cited_chunks = count_cited_chunks(response)
    total_chunks = len(chunks)
    return cited_chunks / total_chunks if total_chunks > 0 else 0
```

If utilization is consistently below 40%, reduce top-k or improve reranking — paying for context that is ignored.

## Source Deduplication

When multiple retrieval passes return overlapping chunks, deduplicate before assembly.

### Deduplication Strategies

| Strategy | How | When |
|----------|-----|------|
| Exact ID match | Remove chunks with same document ID | Multi-query retrieval |
| Content hash | Hash chunk text, remove duplicates | Hybrid search overlap |
| Semantic similarity | Remove chunks with cosine > 0.95 | Overlapping chunk windows |
| Source-level | Keep best chunk per source document | Diverse source coverage |

```python
def deduplicate_chunks(chunks: list, threshold: float = 0.95) -> list:
    seen_hashes = set()
    unique = []
    for chunk in chunks:
        content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique.append(chunk)
    return unique
```

## Multi-Turn Context Management

For conversational RAG, manage context across turns without exploding token usage.

### Strategies

| Strategy | Description | Trade-off |
|----------|------------|-----------|
| Retrieve per turn | New retrieval each turn using latest query | Fresh context, no stale info |
| Context carry-forward | Keep previous turn's context + new retrieval | Continuity, token growth |
| Conversation summary | Summarize prior turns, retrieve for condensed query | Token-efficient, may lose detail |
| Sliding window | Keep last N turns of context | Bounded token usage |

### Conversation-Aware Query Rewriting

Rewrite the current query to be self-contained using conversation history:

```python
rewrite_prompt = """Given the conversation history, rewrite the latest
question to be self-contained (understandable without the history).

History:
User: What are the API rate limits?
Assistant: Free tier gets 100 RPM, paid gets 1000 RPM.

Latest question: "Can I increase it?"

Rewritten: "Can I increase the API rate limit above 1000 requests per minute?"
"""
```

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| No citation requirement in prompt | Unverifiable responses | Require [n] notation, list sources |
| Stuffing entire context window | Lost-in-the-middle degradation | Fewer, better chunks with reranking |
| No fallback for missing context | Hallucination when retrieval fails | Explicit "I don't know" instruction |
| Static top-k regardless of query | Wasted tokens on simple queries | Dynamic context sizing |
| No deduplication after multi-retrieval | Redundant chunks waste tokens | Deduplicate by content hash |
| Ignoring context utilization metric | Paying for unused context | Track and optimize |
