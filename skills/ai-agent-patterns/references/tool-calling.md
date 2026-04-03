# Tool Calling Patterns

Sources: OpenAI (Function Calling Documentation, 2024-2025), Anthropic (Tool Use Documentation, 2024-2025), Google (Gemini Function Calling, 2025), MCP Specification (Model Context Protocol, 2025), LangChain (Tool Documentation, 2025)

Covers: tool definition schemas, structured output, parallel tool calls, error handling, tool selection strategies, and MCP integration.

## Tool Definition Fundamentals

A tool definition tells the model what the tool does, what parameters it accepts, and what it returns. Quality of tool definitions directly impacts agent reliability — invest more time here than in prompt engineering.

### Anatomy of a Good Tool Definition

```json
{
  "name": "search_database",
  "description": "Search the product database by query string. Returns up to 10 matching products with name, price, and availability. Use when the user asks about product information, pricing, or stock status.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language search query. Example: 'red running shoes under $100'"
      },
      "category": {
        "type": "string",
        "enum": ["electronics", "clothing", "home", "sports"],
        "description": "Product category to filter results. Omit to search all categories."
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return (1-10, default 5)"
      }
    },
    "required": ["query"]
  }
}
```

### Tool Description Best Practices

| Practice | Example |
|----------|---------|
| State WHEN to use the tool | "Use when the user asks about product information" |
| Include input examples | "Example: 'red running shoes under $100'" |
| Describe output shape | "Returns up to 10 matching products with name, price, availability" |
| Specify constraints | "max_results: 1-10, default 5" |
| Use enums for fixed options | `"enum": ["electronics", "clothing"]` |
| Mark required vs optional | `"required": ["query"]` |

### Common Tool Definition Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Vague description | Model picks wrong tool | Describe when AND when not to use |
| Missing examples | Model guesses parameter format | Add 2-3 examples in description |
| No enum constraints | Model invents invalid values | Use enum for fixed option sets |
| Missing required fields | Model omits critical parameters | Mark required explicitly |
| Overly complex schema | Model struggles with nested objects | Flatten where possible |
| Same capability in multiple tools | Model picks randomly | Deduplicate or add routing guidance |

## Structured Output

Force the model to return data in a specific format using JSON Schema constraints. Critical for agents that feed tool outputs into downstream processing.

### Provider Comparison

| Provider | Method | JSON Guarantee | Schema Support |
|----------|--------|---------------|----------------|
| OpenAI | `response_format: { type: "json_schema" }` | Yes (constrained decoding) | Full JSON Schema |
| Anthropic | Tool use with single tool | Yes (via tool result) | JSON Schema in tool params |
| Google Gemini | `response_mime_type: "application/json"` | Yes | JSON Schema |
| OpenAI | `response_format: { type: "json_object" }` | Partial (valid JSON, no schema) | None |

### Structured Output via Tool Use

Force structured output by defining a "response" tool and requiring the model to call it:

```typescript
const tools = [{
  name: "respond_with_analysis",
  description: "Structure your analysis into this format",
  parameters: {
    type: "object",
    properties: {
      summary: { type: "string", description: "One-paragraph summary" },
      findings: {
        type: "array",
        items: {
          type: "object",
          properties: {
            title: { type: "string" },
            severity: { type: "string", enum: ["low", "medium", "high", "critical"] },
            description: { type: "string" }
          },
          required: ["title", "severity", "description"]
        }
      },
      recommendation: { type: "string" }
    },
    required: ["summary", "findings", "recommendation"]
  }
}];

// Force the model to use this tool
const response = await client.messages.create({
  model: "claude-sonnet-4-20250514",
  tools: tools,
  tool_choice: { type: "tool", name: "respond_with_analysis" },
  messages: [{ role: "user", content: "Analyze this codebase for security issues..." }]
});
```

### tool_choice Options

| Value | Behavior | Use When |
|-------|----------|----------|
| `auto` | Model decides whether to call tools | General agent loop |
| `required` | Model must call at least one tool | Every step needs tool use |
| `{ type: "tool", name: "X" }` | Model must call specific tool | Forcing structured output |
| `none` | Model cannot call tools | Final synthesis step |

## Parallel Tool Calls

Models can request multiple tool calls in a single response. Execute independent calls concurrently for lower latency.

### Detection and Execution

```typescript
const response = await client.chat.completions.create({
  model: "gpt-4o",
  messages: messages,
  tools: tools,
  parallel_tool_calls: true  // OpenAI: explicit opt-in
});

// Response may contain multiple tool calls
const toolCalls = response.choices[0].message.tool_calls;

if (toolCalls.length > 1) {
  // Execute independent calls in parallel
  const results = await Promise.all(
    toolCalls.map(async (call) => {
      const result = await executeTool(call.function.name, call.function.arguments);
      return { tool_call_id: call.id, content: JSON.stringify(result) };
    })
  );

  // Return all results to model
  messages.push(response.choices[0].message);
  for (const result of results) {
    messages.push({ role: "tool", ...result });
  }
}
```

### Provider Support

| Provider | Parallel Calls | Control |
|----------|---------------|---------|
| OpenAI | Yes | `parallel_tool_calls: true/false` |
| Anthropic | Yes (automatic) | Model decides when to batch |
| Google Gemini | Yes | Automatic batching |
| LangGraph | Yes | Handled in state graph edges |

### Parallel Call Pitfalls

| Pitfall | Example | Fix |
|---------|---------|-----|
| Dependent calls executed in parallel | Call B needs result of Call A | Check for dependencies before parallel dispatch |
| Rate limiting on external APIs | 5 parallel calls to same API | Add concurrency limits per API |
| Partial failure handling | 3 of 5 calls succeed | Return partial results with error for failed calls |
| Order-dependent results | Results needed in specific order | Sort after parallel execution |

## Error Handling

Tool errors are the primary failure mode for agents. Handle them gracefully to prevent agent loops and wasted tokens.

### Error Return Pattern

Return structured errors that help the model recover:

```typescript
async function executeTool(name: string, args: string): Promise<string> {
  try {
    const parsedArgs = JSON.parse(args);
    const result = await tools[name](parsedArgs);
    return JSON.stringify({ success: true, data: result });
  } catch (error) {
    return JSON.stringify({
      success: false,
      error: {
        type: error.name,       // "ValidationError", "NotFoundError", "RateLimitError"
        message: error.message, // Human-readable description
        retry: isRetryable(error),
        suggestion: getSuggestion(error) // "Try a different search query" or "Wait 30 seconds"
      }
    });
  }
}
```

### Error Recovery Strategies

| Error Type | Strategy | Implementation |
|------------|----------|---------------|
| Validation error | Return error with correction hint | Include valid options in error message |
| Not found | Suggest alternative query | "No results for X. Try broader terms." |
| Rate limit | Exponential backoff | Wait 2^attempt seconds, max 3 retries |
| Timeout | Retry with shorter timeout | Reduce scope or use cached fallback |
| Auth failure | Escalate to user | "Authentication expired. Please re-authenticate." |
| Server error (5xx) | Retry with backoff | Max 2 retries, then report failure |

### Retry with Exponential Backoff

```typescript
async function executeWithRetry(
  fn: () => Promise<any>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (!isRetryable(error) || attempt === maxRetries) throw error;
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Model Context Protocol (MCP)

MCP standardizes how AI applications connect to external tools and context via MCP servers. Each server exposes tools, resources, and prompts through a unified protocol.

### MCP Architecture

```
Agent (MCP Client)
  ├── MCP Server: Database
  │   ├── tool: query_database
  │   └── resource: schema://tables
  ├── MCP Server: File System
  │   ├── tool: read_file
  │   └── tool: write_file
  └── MCP Server: API Gateway
      ├── tool: call_api
      └── resource: openapi://spec
```

### MCP Tool Definition

```json
{
  "name": "query_database",
  "description": "Execute a read-only SQL query against the connected database.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "SQL SELECT query to execute"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum rows to return (default: 100, max: 1000)"
      }
    },
    "required": ["sql"]
  }
}
```

### MCP vs Direct Tool Integration

| Dimension | MCP | Direct Integration |
|-----------|-----|-------------------|
| Standardization | Protocol-level, any agent framework | Framework-specific |
| Discovery | Dynamic tool discovery at runtime | Static tool definitions |
| Security | Server-level sandboxing, permission model | Application-level |
| Overhead | Protocol layer adds latency | Direct function calls |
| Best for | Multi-tool ecosystems, third-party tools | Tight integrations, performance-critical |

## Tool Selection at Scale

When an agent has access to 20+ tools, selection accuracy drops. Strategies to maintain accuracy:

### On-Demand Tool Retrieval

```
1. Embed all tool descriptions into vector store
2. For each user query, retrieve top-5 most relevant tools
3. Present only those 5 tools to the model
4. Model selects from the reduced set
```

### Tool Categories and Routing

```
Incoming query → Classifier → Category
  Category: "data"     → [query_db, search_index, get_stats]
  Category: "files"    → [read_file, write_file, list_dir]
  Category: "comms"    → [send_email, send_slack, create_ticket]
```

### Hierarchical Tool Selection

| Level | Action | Example |
|-------|--------|---------|
| L1: Domain | Classify query domain | "This is a database question" |
| L2: Operation | Select operation type | "This needs a read query" |
| L3: Tool | Pick specific tool | "Use query_database" |

## Common Patterns

### Search-then-Act

```
1. search(query) → results
2. select_relevant(results) → items
3. act_on_item(item) → outcome
```

### Gather-then-Synthesize

```
1. Parallel: [fetch_source_a(), fetch_source_b(), fetch_source_c()]
2. synthesize(results_a, results_b, results_c) → report
```

### Confirm-then-Execute

```
1. plan_action(request) → action_plan
2. present_to_user(action_plan) → confirmation
3. if confirmed: execute(action_plan) → result
```
