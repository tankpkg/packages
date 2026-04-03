# Tool Design Patterns

Sources: MCP Specification (2025-06-18), TypeScript SDK v2 Server Guide, FastMCP 3 documentation, Anthropic MCP reference server implementations

Covers: tool naming conventions, description writing for LLM selection, inputSchema and outputSchema design, annotations, error handling patterns, progress reporting, multi-tool server architecture, and real-world tool examples.

## Tool Anatomy

Every MCP tool has these components:

| Component | Required | Purpose |
|-----------|----------|---------|
| `name` | Yes | Unique identifier within the server |
| `title` | No | Human-readable display name |
| `description` | Yes | Drives LLM tool selection |
| `inputSchema` | Yes | JSON Schema (or Zod/Pydantic) for parameters |
| `outputSchema` | No | JSON Schema for structured return values |
| `annotations` | No | Behavioral hints (readOnly, destructive, idempotent) |

The LLM sees `name`, `description`, and `inputSchema` when deciding whether to call a tool. The `description` is the most important field — it determines whether the LLM picks the right tool.

## Naming Conventions

Use clear, action-oriented names:

| Pattern | Examples | When |
|---------|---------|------|
| `verb-noun` | `search-users`, `create-ticket`, `delete-file` | Standard CRUD operations |
| `noun-verb` | `database-query`, `file-upload` | When noun context matters more |
| `namespace-action` | `github-list-repos`, `slack-send-message` | Multi-domain servers |

Rules:
- Kebab-case for consistency across languages
- Avoid generic names: `get-data` tells the LLM nothing; `get-user-profile` is specific
- Prefix with domain when a server wraps an external service
- Keep under 64 characters

## Writing Effective Descriptions

The description is a prompt to the LLM. Write it to answer: "When should the model use this tool?"

### Good vs Bad Descriptions

| Bad | Good |
|-----|------|
| "Query the database" | "Execute a read-only SQL query against the PostgreSQL database. Returns up to 1000 rows as JSON. Use list-tables first to discover available tables." |
| "Send a message" | "Send a Slack message to a channel or user. Requires channel name (e.g., #general) or user ID. Supports markdown formatting." |
| "Process file" | "Convert a CSV file to JSON format. Accepts file path, delimiter, and encoding. Returns the JSON content as text." |

### Description Checklist

1. **What it does** — one sentence, specific action
2. **When to use it** — conditions that make this the right tool
3. **What it needs** — key parameter expectations
4. **What it returns** — output format and shape
5. **Constraints** — limits, prerequisites, side effects

### Cross-Tool Relationships

Document dependencies in descriptions or server instructions:

```
"Execute a SQL query. Always call list-tables first to discover
available tables. Use describe-table to check column types before
writing WHERE clauses."
```

This guides the LLM's tool call sequence without hardcoding it.

## inputSchema Design

### JSON Schema Best Practices

```typescript
inputSchema: z.object({
  query: z.string()
    .min(1)
    .max(500)
    .describe('SQL SELECT query — read-only, no INSERT/UPDATE/DELETE'),
  database: z.enum(['production', 'staging', 'analytics'])
    .describe('Target database'),
  limit: z.number()
    .int()
    .min(1)
    .max(1000)
    .default(100)
    .describe('Maximum rows to return')
}).strict()
```

### Schema Rules

| Rule | Why |
|------|-----|
| Use `.strict()` (Zod) or `additionalProperties: false` | Prevents injection of unexpected fields |
| Add `.describe()` to every field | LLM uses descriptions to fill parameters correctly |
| Set `.min()` / `.max()` constraints | Prevents abuse (huge payloads, empty strings) |
| Use `.enum()` for fixed options | Constrains LLM to valid choices |
| Provide `.default()` values | Reduces required parameters, improves UX |
| Use `.optional()` sparingly | Every optional field is a decision the LLM must make |

### Common Input Patterns

```typescript
// Pagination
z.object({
  cursor: z.string().optional().describe('Pagination cursor from previous response'),
  limit: z.number().int().min(1).max(100).default(20)
})

// Date range
z.object({
  startDate: z.string().date().describe('Start date (YYYY-MM-DD)'),
  endDate: z.string().date().describe('End date (YYYY-MM-DD)')
})

// File reference
z.object({
  path: z.string().min(1).describe('Absolute file path'),
  encoding: z.enum(['utf-8', 'ascii', 'binary']).default('utf-8')
})

// Search with filters
z.object({
  query: z.string().min(1),
  filters: z.object({
    status: z.enum(['active', 'archived', 'all']).default('active'),
    createdAfter: z.string().date().optional()
  }).optional()
})
```

### Python Equivalent with Pydantic

```python
from pydantic import BaseModel, Field

class QueryParams(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="SQL SELECT query")
    database: Literal["production", "staging", "analytics"] = Field(description="Target database")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum rows")

    model_config = {"extra": "forbid"}  # Equivalent to additionalProperties: false
```

## outputSchema Design

Structured output lets the LLM parse results reliably:

```typescript
outputSchema: z.object({
  results: z.array(z.object({
    id: z.string(),
    title: z.string(),
    score: z.number()
  })),
  totalCount: z.number(),
  hasMore: z.boolean()
})
```

Return both `content` (for display) and `structuredContent` (for parsing):

```typescript
return {
  content: [{ type: 'text', text: `Found ${results.length} items` }],
  structuredContent: { results, totalCount, hasMore }
};
```

When `isError` is true, output schema validation is skipped — error messages bypass the schema.

## Annotations

Annotations hint at tool behavior without changing execution:

```typescript
annotations: {
  title: 'Delete File',
  readOnlyHint: false,       // Modifies state
  destructiveHint: true,      // Irreversible
  idempotentHint: true,       // Safe to retry
  openWorldHint: false         // No external interaction
}
```

### Annotation Decision Table

| Tool Type | readOnly | destructive | idempotent | openWorld |
|-----------|----------|-------------|------------|-----------|
| Database query | true | false | true | false |
| Create record | false | false | false | false |
| Delete record | false | true | true | false |
| API call (read) | true | false | true | true |
| Send email | false | false | false | true |
| File write (overwrite) | false | false | true | false |

## Error Handling Patterns

### Error Categories

| Category | isError | Example |
|----------|---------|---------|
| User-fixable input error | true | "Invalid date format. Use YYYY-MM-DD." |
| Resource not found | true | "User with ID 123 not found." |
| Rate limit / temporary | true | "Rate limited. Retry in 30 seconds." |
| Permission denied | true | "Insufficient permissions for this operation." |
| Internal server error | throw | Unexpected crashes — SDK catches and wraps |

### Structured Error Pattern

```typescript
function toolError(code: string, message: string): CallToolResult {
  return {
    content: [{ type: 'text', text: JSON.stringify({ error: code, message }) }],
    isError: true
  };
}

// Usage:
if (!user) return toolError('NOT_FOUND', `User ${id} not found`);
if (!hasPermission) return toolError('FORBIDDEN', 'Admin role required');
```

## Progress Reporting

For long-running tools, report progress so the client can display status:

```typescript
async ({ files }, ctx): Promise<CallToolResult> => {
  const token = ctx.mcpReq._meta?.progressToken;
  for (let i = 0; i < files.length; i++) {
    await processFile(files[i]);
    if (token !== undefined) {
      await ctx.mcpReq.notify({
        method: 'notifications/progress',
        params: { progressToken: token, progress: i + 1, total: files.length }
      });
    }
  }
  return { content: [{ type: 'text', text: `Done: ${files.length} files` }] };
}
```

`progress` must increase monotonically. `total` is optional but recommended. Skip notification if no `progressToken` is provided.

## Multi-Tool Server Architecture

### Grouping Strategies

| Strategy | When | Example |
|----------|------|---------|
| Domain-based | Wrapping one service | `github-*`: list-repos, create-issue, search-code |
| CRUD-based | Database/resource server | `users-list`, `users-get`, `users-create`, `users-delete` |
| Workflow-based | Sequential operations | `pipeline-start`, `pipeline-status`, `pipeline-cancel` |
| Capability-based | Mixed concerns | `query` (read), `mutate` (write), `export` (output) |

### Server Instructions for Multi-Tool Servers

Use the `instructions` field to document tool relationships:

```typescript
const server = new McpServer(
  { name: 'db-server', version: '1.0.0' },
  {
    instructions: `
      Workflow: list-tables -> describe-table -> query
      Always list tables before querying. Always describe a table before
      writing WHERE clauses. Query tool is read-only — use mutate for writes.
      Results are paginated — use the cursor from the response for next page.
    `
  }
);
```

## Real-World Tool Examples

### Database Query Tool

```typescript
server.registerTool('query', {
  title: 'SQL Query',
  description: 'Execute a read-only SQL query. Call list-tables and describe-table first.',
  inputSchema: z.object({
    sql: z.string().min(1).max(2000).describe('SQL SELECT query'),
    params: z.array(z.union([z.string(), z.number()])).optional()
  }).strict(),
  annotations: { readOnlyHint: true, idempotentHint: true }
}, async ({ sql, params }) => {
  if (!/^\s*SELECT\b/i.test(sql)) {
    return { content: [{ type: 'text', text: 'Only SELECT queries allowed' }], isError: true };
  }
  const rows = await db.query(sql, params);
  return { content: [{ type: 'text', text: JSON.stringify(rows, null, 2) }] };
});
```

### File Operations Tool

```typescript
server.registerTool('read-file', {
  title: 'Read File',
  description: 'Read file contents. Path must be within the project directory.',
  inputSchema: z.object({
    path: z.string().min(1).describe('Relative path from project root'),
    encoding: z.enum(['utf-8', 'binary']).default('utf-8')
  }).strict(),
  annotations: { readOnlyHint: true }
}, async ({ path, encoding }) => {
  const resolved = resolve(PROJECT_ROOT, path);
  if (!resolved.startsWith(PROJECT_ROOT)) {
    return { content: [{ type: 'text', text: 'Path traversal denied' }], isError: true };
  }
  const content = await readFile(resolved, encoding);
  return { content: [{ type: 'text', text: content }] };
});
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| God tool that does everything | LLM cannot choose correctly | Split into focused single-purpose tools |
| No parameter descriptions | LLM guesses argument values | Add `.describe()` to every field |
| Returning raw error stack | Leaks internals, LLM cannot act on it | Return structured error with `isError: true` |
| Accepting arbitrary JSON | Injection surface | Use strict schemas with `additionalProperties: false` |
| Tool name matches another server's tool | Shadowing attack vector | Namespace: `myserver-tool-name` |
| Description says "internal use only" | LLM ignores it anyway | Remove the tool or restrict via capabilities |
