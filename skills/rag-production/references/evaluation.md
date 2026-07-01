# RAG Evaluation

Sources: Shahul et al. (RAGAS, 2023), DeepEval documentation, TruLens documentation, Arize Phoenix documentation, LangSmith documentation, 2024-2026 RAG evaluation research

Covers: RAGAS metrics, evaluation frameworks comparison, test set generation, quality gates for CI/CD, regression testing, and production monitoring.

## Why Evaluate RAG

RAG pipelines have many interacting components (chunking, embedding, retrieval, reranking, generation). Changing any one component can improve one metric while degrading another. Without automated evaluation, quality regressions hide behind "it seems to work." Evaluate every pipeline change against a fixed test set before deploying.

## RAGAS Metrics

### Core RAG Metrics

| Metric | What It Measures | Requires | Range |
|--------|-----------------|----------|-------|
| Faithfulness | Is the answer grounded in retrieved context? | Answer + context | 0-1 (higher = better) |
| Answer Relevance | Does the answer address the question? | Question + answer | 0-1 (higher = better) |
| Context Precision | Are relevant chunks ranked higher? | Question + context + reference | 0-1 (higher = better) |
| Context Recall | Did retrieval find all necessary information? | Context + reference answer | 0-1 (higher = better) |

### Faithfulness (Most Critical Metric)

Measures whether every claim in the generated answer can be traced to the retrieved context. A faithfulness score below 0.8 indicates the model is injecting information from training data — hallucinating.

**Computation pipeline:**

```
Step 1: Decompose answer into atomic statements
  Answer: "The API has 100 RPM free tier and 1000 RPM paid tier with RFC 9110 headers"
  Statements:
    s1: "The API has 100 RPM free tier"
    s2: "The API has 1000 RPM paid tier"
    s3: "The API uses RFC 9110 headers"

Step 2: For each statement, check if retrieved context entails it
  s1: entailed (context mentions 100 RPM) → 1
  s2: entailed (context mentions 1000 RPM) → 1
  s3: not entailed (context doesn't mention RFC 9110) → 0

Step 3: Faithfulness = 2/3 = 0.667
```

### Context Precision

Measures whether chunks that actually contribute to the answer are ranked near the top. Uses Average Precision — order matters.

```
Chunks: [relevant, irrelevant, relevant, irrelevant, irrelevant]
Verdicts: [1, 0, 1, 0, 0]

P@1 = 1/1 = 1.0 (first chunk is relevant)
P@3 = 2/3 = 0.667 (2 relevant in top 3)

AP = (1.0 * 1 + 0.667 * 1) / 2 = 0.833
```

Low context precision (< 0.7) means the reranker is not effectively promoting relevant chunks.

### Context Recall

Measures completeness — did the retriever find all the information needed to answer? Requires a reference answer for comparison.

```
Reference answer statements: [s1, s2, s3, s4]
Attributable to retrieved context: [s1: yes, s2: yes, s3: no, s4: yes]
Context Recall = 3/4 = 0.75
```

Low context recall (< 0.75) means the retriever is missing relevant chunks. Increase top-k, add hybrid search, or improve chunking.

### Running RAGAS Evaluation

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

eval_dataset = Dataset.from_dict({
    "question": ["What are the API rate limits?", ...],
    "answer": ["The API enforces 100 RPM for free tier...", ...],
    "contexts": [["chunk1 text", "chunk2 text"], ...],
    "ground_truth": ["Free tier: 100 RPM, Paid: 1000 RPM...", ...]
})

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    llm=ChatOpenAI(model="gpt-4o-mini"),  # Judge model
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small")
)

print(results)
# {'faithfulness': 0.87, 'answer_relevancy': 0.82,
#  'context_precision': 0.78, 'context_recall': 0.81}
```

## DeepEval (CI/CD-Native Evaluation)

DeepEval wraps RAG evaluation in pytest, enabling quality gates in CI/CD pipelines.

### Setup

```python
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase

faithfulness_metric = FaithfulnessMetric(
    threshold=0.80,
    model="gpt-4o-mini"
)

precision_metric = ContextualPrecisionMetric(
    threshold=0.70,
    model="gpt-4o-mini"
)

def test_rag_faithfulness():
    test_case = LLMTestCase(
        input="What are the API rate limits?",
        actual_output="The API has 100 RPM free tier and 1000 RPM paid tier.",
        retrieval_context=[
            "The API allows 100 requests per minute for free tier...",
            "Premium accounts get 1000 requests per minute..."
        ]
    )
    assert_test(test_case, [faithfulness_metric, precision_metric])
```

### GEval Custom Metrics

Define domain-specific metrics in natural language:

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

citation_metric = GEval(
    name="CitationQuality",
    criteria="""Evaluate whether the answer:
    1. Cites specific source documents using [n] notation
    2. Each citation corresponds to a real document in the context
    3. Claims without citations are flagged""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.RETRIEVAL_CONTEXT
    ],
    threshold=0.7
)
```

## Test Set Generation

### Manual Curation (Highest Quality)

Create 50-100 question-answer pairs manually from your corpus:

| Question Type | Count | Example |
|--------------|-------|---------|
| Factual lookup | 20-30 | "What is the rate limit for free tier?" |
| Multi-chunk | 10-15 | "Compare pricing across all tiers" |
| Temporal | 5-10 | "What changed in v3.2?" |
| Negative (unanswerable) | 5-10 | "What is the refund policy?" (not in docs) |
| Ambiguous | 5-10 | "How does it work?" (vague) |

### Synthetic Generation with RAGAS

```python
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

generator = TestsetGenerator.from_langchain(
    generator_llm=ChatOpenAI(model="gpt-4o"),
    critic_llm=ChatOpenAI(model="gpt-4o-mini"),
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small")
)

testset = generator.generate_with_langchain_docs(
    documents=documents,
    test_size=50,
    distributions={simple: 0.4, reasoning: 0.3, multi_context: 0.3}
)
```

### Synthetic Test Set Quality

| Method | Effort | Coverage | Realism |
|--------|--------|----------|---------|
| Manual curation | High | Limited by curator knowledge | High |
| RAGAS synthetic | Low | Broad coverage | Medium |
| User query logs | Medium | Real distribution | Highest |
| Hybrid (manual + synthetic) | Medium | Best coverage | High |

Start with synthetic for broad coverage, then add manual questions for edge cases and real user queries for production relevance.

## Quality Gates for CI/CD

### Gate Configuration

```yaml
# .github/workflows/rag-eval.yml
name: RAG Quality Gate
on:
  pull_request:
    paths:
      - 'src/rag/**'
      - 'prompts/**'
      - 'config/chunking.yaml'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run RAG evaluation
        run: pytest tests/rag_eval/ -v --tb=short
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - name: Check thresholds
        run: |
          python scripts/check_thresholds.py \
            --faithfulness 0.80 \
            --context-precision 0.70 \
            --context-recall 0.75 \
            --answer-relevance 0.75
```

### Threshold Guidelines

| Environment | Faithfulness | Context Precision | Context Recall | Answer Relevance |
|-------------|-------------|-------------------|----------------|-----------------|
| Development | >= 0.70 | >= 0.60 | >= 0.65 | >= 0.65 |
| Staging | >= 0.80 | >= 0.70 | >= 0.75 | >= 0.75 |
| Production | >= 0.85 | >= 0.75 | >= 0.80 | >= 0.80 |
| Regulated (finance, medical) | >= 0.90 | >= 0.80 | >= 0.85 | >= 0.85 |

## Regression Testing

### What Triggers Re-evaluation

| Change | Re-evaluate? | Rationale |
|--------|-------------|-----------|
| Chunking strategy/size | Yes | Directly affects retrieval |
| Embedding model | Yes | Different vector space |
| Prompt template | Yes | Affects generation quality |
| LLM model upgrade | Yes | Different generation behavior |
| New documents added | Spot-check | May affect existing queries |
| Reranker model change | Yes | Changes retrieval ordering |
| Vector DB migration | Yes | Index differences affect results |

### A/B Evaluation Pattern

```python
def compare_pipelines(test_set, pipeline_a, pipeline_b):
    results_a = run_evaluation(test_set, pipeline_a)
    results_b = run_evaluation(test_set, pipeline_b)
    
    comparison = {
        "faithfulness": results_b["faithfulness"] - results_a["faithfulness"],
        "context_precision": results_b["context_precision"] - results_a["context_precision"],
        "context_recall": results_b["context_recall"] - results_a["context_recall"],
    }
    
    # Accept pipeline_b only if no metric regresses more than 2%
    regressions = {k: v for k, v in comparison.items() if v < -0.02}
    if regressions:
        print(f"REJECT: Regressions detected: {regressions}")
    else:
        print(f"ACCEPT: All metrics stable or improved: {comparison}")
```

## Production Monitoring

### Sampling-Based Evaluation

Evaluate a random sample (3-5%) of production queries daily:

```python
import random

def daily_eval(sample_rate=0.05):
    recent = fetch_recent_rag_logs(hours=24)
    sample = random.sample(recent, int(len(recent) * sample_rate))
    
    results = evaluate_sample(sample, metrics=["faithfulness", "answer_relevancy"])
    
    if results["faithfulness"] < 0.75:
        alert("Faithfulness dropped below threshold", severity="critical")
    if results["answer_relevancy"] < 0.70:
        alert("Answer relevancy declining", severity="warning")
```

### Key Production Metrics

| Metric | Alert Threshold | Root Cause Investigation |
|--------|----------------|------------------------|
| Faithfulness (sampled) | < 0.75 | Check recent document ingestion, prompt changes |
| Retrieval latency P95 | > 500ms | Index size, embedding model load, cache miss rate |
| Cache hit rate | < 30% | Query diversity, normalization quality |
| Empty retrieval rate | > 10% | Missing documents, poor chunking for new query types |
| User negative feedback | > 10% | All of the above plus UX issues |

## Evaluation Cost Management

| Approach | Cost per 100 Test Cases | Quality |
|----------|------------------------|---------|
| GPT-4o as judge | ~$2-5 | Highest |
| GPT-4o-mini as judge | ~$0.10-0.30 | Good (recommended) |
| Claude 3.5 Haiku as judge | ~$0.05-0.15 | Good |
| Open-source judge (Mistral) | GPU cost only | Varies |

Use GPT-4o-mini for routine evaluation. Reserve GPT-4o for validating edge cases or when GPT-4o-mini scores seem unreliable.

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| No reference answers | Cannot compute context recall | Create golden set with reference answers |
| Using generation model as judge | Inflated scores (self-evaluation bias) | Use different model for judging |
| Evaluating only on easy queries | False confidence | Include multi-hop, negative, ambiguous queries |
| No regression testing on pipeline changes | Silent quality degradation | Automate eval in CI/CD |
| Optimizing for one metric | Other metrics degrade | Track all four RAGAS metrics together |
| Skipping evaluation entirely | "It works on my machine" | Build eval into pipeline from day one |
