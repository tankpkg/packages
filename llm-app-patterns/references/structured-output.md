# Structured Output

Sources: Huyen (AI Engineering), Bouchard & Peters (Building LLMs for Production), 2024–2026 production engineering analysis

Covers: output method comparison, schema design, retry logic, partial extraction, validation pipelines, provider patterns.

## Why Structured Output Is Non-Trivial

Ask an LLM for JSON and you get JSON — most of the time. In production at scale you get:
- Markdown code fences wrapping the JSON
- Trailing commas, unquoted keys, invalid syntax
- Extra explanation before or after the JSON block
- Fields with wrong types or missing required keys
- Syntactically valid JSON with semantically wrong values

Structured output eliminates these failure modes by constraining generation at the token level rather than relying on prompt instructions.

## Method Comparison

| Method | Schema Guarantee | Retry | Complexity | Use When |
|--------|-----------------|-------|------------|----------|
| Prompt-only ("return JSON") | None | Manual | Low | Prototyping only |
| JSON mode | Valid syntax only | Manual | Low | Simple output, flexible schema |
| Function calling / tool use | Schema-constrained | Manual | Medium | Tool invocation + extraction |
| Native structured outputs | Schema-constrained | Automatic | Medium | Single-provider production |
| Instructor + Pydantic | Schema-constrained | Automatic | Low | Multi-provider, type-safe |

Never rely on prompt-only instructions for data pipelines. Schema failures cascade into downstream failures that are hard to debug.

## Prompt-Only (Avoid in Production)

```
System: You are a data extractor. Return only valid JSON.
User: Extract sentiment from this review: {text}
Expected: {"sentiment": "positive", "score": 0.9}
Actual (20% of the time): "The sentiment is positive with a confidence of 0.9."
```

Acceptable for prototyping. Not acceptable when downstream code parses the response.

## JSON Mode

Guarantees syntactically valid JSON. Does not guarantee schema compliance. The model can add, omit, or mistype fields.

```
Request:
    response_format = "json_object"
    system = "Return JSON with keys: name (str), score (float 0-1), reason (str)"

Response guaranteed: valid parseable JSON
Response NOT guaranteed: correct keys, correct types
```

Use for: simple extraction where the schema is loose and you validate downstream.

## Native Structured Outputs

Constrained decoding prevents the model from generating tokens that would violate the JSON schema. The response is guaranteed to parse and validate against the schema.

### How It Works

```
Define schema (JSON Schema or Pydantic model)
    → Convert to constrained grammar
    → Model samples tokens only from valid next tokens
    → Response always validates against schema
```

### Pseudocode Pattern

```
schema = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "score":     {"type": "number", "minimum": 0, "maximum": 1},
        "reason":    {"type": "string"},
    },
    "required": ["sentiment", "score", "reason"],
    "additionalProperties": false
}

response = llm.generate(messages, response_format=schema)
# response.parsed is guaranteed to match schema
```

Available in: OpenAI (gpt-4o and newer), Anthropic (via tool use), Google Gemini (native JSON mode with schema).

## Instructor + Pydantic (Recommended for Production)

Instructor wraps any LLM provider with automatic validation and retry. Define the schema once as a Python class; Instructor handles the rest.

### Core Pattern

```python
class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    score: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(min_length=10, description="One-sentence explanation")

result = instructor_client.extract(
    model="claude-3-5-sonnet",
    response_model=SentimentResult,
    messages=[{"role": "user", "content": text}],
    max_retries=3,
)
# result is a typed SentimentResult; failed validations auto-retry with error context
```

On validation failure, Instructor appends the exact error to the next message ("score must be <= 1.0, got 1.7") and retries. LLMs correct validation errors when given precise feedback.

### Provider Compatibility

| Provider | Instructor Mode | Notes |
|----------|----------------|-------|
| OpenAI | Native | Uses structured outputs endpoint |
| Anthropic | Tool use | Forces a single tool call |
| Gemini | JSON mode | Uses schema parameter |
| Ollama (local) | JSON mode | Model-dependent reliability |
| Any | Generic | Parses and retries on failure |

Use Instructor when targeting multiple providers or needing consistent retry behavior across models.

## Schema Design for LLMs

Schemas that are clear to humans are not always clear to models. Design schemas for the model's generation process.

### Design Rules

| Rule | Wrong | Right |
|------|-------|-------|
| Use enums for constrained values | `category: str` | `category: Literal["bug", "feature", "docs"]` |
| Add Field descriptions | `name: str` | `name: str = Field(description="Full legal name, not username")` |
| Bound numeric ranges explicitly | `score: float` | `score: float = Field(ge=0.0, le=1.0)` |
| Bound list lengths | `items: list[str]` | `items: list[str] = Field(min_length=1, max_length=5)` |
| Avoid deep nesting | 4+ levels | Max 2–3 levels; extract in two passes if needed |
| Make optionality explicit | `detail: str \| None` | `detail: str \| None = Field(description="Null if not mentioned in text")` |
| Name fields with context | `v: float` | `confidence_score: float` |

### Discriminated Unions

When extracting multiple entity types with different schemas:

```python
class PersonEntity(BaseModel):
    entity_type: Literal["person"]
    name: str
    role: str

class OrgEntity(BaseModel):
    entity_type: Literal["organization"]
    name: str
    industry: str

# Pydantic discriminated union — type determined by entity_type field
Entity = Annotated[Union[PersonEntity, OrgEntity], Field(discriminator="entity_type")]

class ExtractionResult(BaseModel):
    entities: list[Entity]
```

The discriminator field (entity_type) lets the model and Pydantic agree on which sub-schema applies.

## Retry Logic

### Retry Budget by Context

| Use Case | max_retries | Reasoning |
|----------|-------------|-----------|
| Real-time, user-facing | 2 | Latency sensitive; surface failure to user |
| Background pipeline | 3 | Latency tolerant; prioritize correctness |
| Critical one-time extraction | 4 | High value; spare no retries |

### Manual Retry Pattern

```
function extract_with_retry(prompt, schema, max_attempts):
    error_context = ""
    for attempt in 1..max_attempts:
        raw = llm.generate(prompt + error_context)
        result = schema.validate(raw)
        if valid:
            return result
        error_context = "\nPrevious response error: " + result.error + ". Correct and retry."
    raise ExtractionError("Failed after " + max_attempts + " attempts")
```

## Partial Parsing and Streaming

When the model cannot produce a valid complete object at once, extract what it can as tokens stream in.

```
# Stream partial object — render fields as they arrive
for partial_result in instructor_client.stream_partial(response_model=DocumentSummary):
    if partial_result.title is not None:
        update_ui(title=partial_result.title)
    if partial_result.key_points is not None:
        update_ui(points=partial_result.key_points)

final_result = partial_result  # Last emission is complete
```

Use partial parsing to show incremental progress on long extractions (document summaries, research synthesis).

## Output Validation Pipeline

Layer validation from cheapest to most expensive.

```
LLM raw output
    → Syntax parse          (JSON.parse / model_validate_json)
    → Schema validation     (Pydantic — type and constraint checks)
    → Business rule checks  (custom validators — domain invariants)
    → Semantic validation   (optional LLM judge — "is this coherent?")
    → Accept or retry
```

### Custom Business Rule Validator

```python
class ProductReview(BaseModel):
    rating: int = Field(ge=1, le=5)
    sentiment: Literal["positive", "negative", "neutral"]

    @field_validator("sentiment")
    @classmethod
    def sentiment_aligns_with_rating(cls, sentiment, info):
        rating = info.data.get("rating")
        if rating and rating >= 4 and sentiment == "negative":
            raise ValueError(
                "Rating >= 4 with negative sentiment is contradictory."
            )
        return sentiment
```

Validators surface business logic as explicit constraints, not prompt instructions. The model gets precise error messages on retry.

## Method Selection Decision Tree

```
Is schema fixed and critical? (data pipeline, database write)
├─ YES → Native structured outputs or Instructor + Pydantic
│   ├─ Multiple providers? → Instructor (unified API)
│   └─ Single provider? → Native structured outputs
└─ NO → Is output simple key-value?
    ├─ YES → JSON mode (simpler, no schema overhead)
    └─ NO  → Prompt-only with downstream validation (prototyping)
```

## Common Failures

| Failure | Root Cause | Fix |
|---------|------------|-----|
| Extra fields in output | No `additionalProperties: false` | Pydantic models set this automatically |
| Number parsed as string | Loose schema | Use `float` / `int` type annotations |
| List truncated mid-generation | max_tokens too low | Increase max_tokens; set explicit max_length on list |
| Deep nested schema ignored | Model loses track beyond 2–3 levels | Flatten; extract in two sequential calls |
| Valid JSON, wrong semantic values | Schema validates structure not meaning | Add custom validators or LLM judge |
| Infinite retry on ambiguous enum | Enum values unclear to model | Add Field descriptions to enum options |
