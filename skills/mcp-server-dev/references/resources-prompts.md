# Resources and Prompts

Sources: MCP Specification (2025-06-18), TypeScript SDK v2 Server Guide, FastMCP 3 documentation, modelcontextprotocol.io architecture overview

Covers: resource types (static, dynamic templates, subscriptions), URI design, MIME types, prompt templates with arguments, completions, multi-message prompts, and the boundary between resources, tools, and prompts.

## Resources Overview

Resources provide read-only data that the host application retrieves and attaches as LLM context. Unlike tools (which the LLM invokes), resources are application-controlled — the host decides which resources to fetch.

### Resource vs Tool

| Dimension | Resource | Tool |
|-----------|----------|------|
| Who controls | Application/user | Model |
| Direction | Read-only data retrieval | Action execution |
| Side effects | None | May modify state |
| Discovery | `resources/list`, `resources/templates/list` | `tools/list` |
| Invocation | `resources/read` | `tools/call` |
| Use case | Context, schemas, configs, docs | Queries, mutations, API calls |

Rule of thumb: if the LLM needs to decide when to fetch data, make it a tool. If the application should preload context, make it a resource.

## Static Resources

A static resource has a fixed URI that always returns the same type of data:

### TypeScript

```typescript
server.registerResource(
  'db-schema',
  'db://schema',
  {
    title: 'Database Schema',
    description: 'Complete database schema with all tables and columns',
    mimeType: 'application/json'
  },
  async (uri) => ({
    contents: [{
      uri: uri.href,
      text: JSON.stringify(await db.getSchema(), null, 2)
    }]
  })
);
```

### Python (FastMCP)

```python
@mcp.resource("db://schema", mime_type="application/json")
def get_schema() -> str:
    """Complete database schema with all tables and columns."""
    return json.dumps(db.get_schema(), indent=2)
```

### Protocol Operations

| Method | Purpose |
|--------|---------|
| `resources/list` | Returns all static resources with URIs and metadata |
| `resources/read` | Fetches content for a specific URI |

## Dynamic Resource Templates

Templates define URI patterns with parameters, enabling flexible queries:

### TypeScript

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
  'table-data',
  new ResourceTemplate('db://tables/{tableName}', {
    list: async () => ({
      resources: (await db.listTables()).map(t => ({
        uri: `db://tables/${t.name}`,
        name: t.name,
        description: `Data from ${t.name} table`
      }))
    })
  }),
  {
    title: 'Table Data',
    description: 'Read data from a specific database table',
    mimeType: 'application/json'
  },
  async (uri, { tableName }) => ({
    contents: [{
      uri: uri.href,
      text: JSON.stringify(await db.query(`SELECT * FROM ${tableName} LIMIT 100`))
    }]
  })
);
```

### Python (FastMCP)

```python
@mcp.resource("db://tables/{table_name}", mime_type="application/json")
def get_table_data(table_name: str) -> str:
    """Read data from a specific database table."""
    rows = db.query(f"SELECT * FROM {table_name} LIMIT 100")
    return json.dumps(rows, indent=2)
```

### Protocol Operations

| Method | Purpose |
|--------|---------|
| `resources/templates/list` | Returns available URI templates with metadata |
| `resources/read` with resolved URI | Fetches content for a specific template instance |

### Template URI Syntax

Templates use RFC 6570-like syntax:

| Pattern | Example URI | Parameters |
|---------|-------------|------------|
| `users://{userId}/profile` | `users://123/profile` | `userId: "123"` |
| `files://{path}` | `files:///src/index.ts` | `path: "/src/index.ts"` |
| `weather://{city}/{date}` | `weather://london/2024-06-15` | `city: "london"`, `date: "2024-06-15"` |

## URI Design

### Scheme Conventions

| Scheme | Use Case | Example |
|--------|----------|---------|
| `file://` | Local filesystem | `file:///Users/dev/project/README.md` |
| `db://` | Database resources | `db://tables/users`, `db://schema` |
| Custom scheme | Domain-specific | `github://repos/{owner}/{repo}` |
| `https://` | Web resources | `https://api.example.com/docs` |

### URI Best Practices

- Use lowercase schemes and paths
- Use `/` for hierarchy, not query parameters
- Include enough context in the URI for the client to understand the resource without reading it
- Avoid encoding secrets or PII in URIs — they appear in logs

## MIME Types

Set `mimeType` to help clients render content appropriately:

| MIME Type | Content |
|-----------|---------|
| `text/plain` | Plain text, logs, output |
| `text/markdown` | Documentation, README files |
| `application/json` | Structured data, API responses |
| `text/csv` | Tabular data |
| `text/html` | Web content |
| `application/octet-stream` | Binary data (base64-encoded) |

When returning binary content, encode as base64 and use the `blob` field instead of `text`:

```typescript
contents: [{
  uri: uri.href,
  blob: Buffer.from(imageData).toString('base64'),
  mimeType: 'image/png'
}]
```

## Resource Subscriptions

Clients can subscribe to resource changes for real-time updates:

```typescript
// Server notifies when a resource changes:
server.notification({
  method: 'notifications/resources/updated',
  params: { uri: 'db://schema' }
});
```

The client receives the notification and can re-read the resource. Subscriptions require the server to declare the `resources.subscribe` capability.

### When to Use Subscriptions

| Scenario | Use Subscriptions | Alternative |
|----------|-------------------|-------------|
| File watcher | Yes | Poll with `resources/read` |
| Database schema changes | Yes | Include in tool response |
| Config updates | Yes | Read on each tool call |
| Static documentation | No | Single `resources/read` |

## Prompts Overview

Prompts are reusable templates that users invoke explicitly. They structure interactions with the LLM by providing pre-built message sequences.

### Prompt vs Tool vs Resource

| Primitive | Controlled By | Purpose |
|-----------|--------------|---------|
| Prompt | User (explicit invocation) | Canned interaction patterns |
| Tool | Model (automatic selection) | Actions and queries |
| Resource | Application | Context and data |

## Prompt Registration

### TypeScript

```typescript
import { completable } from '@modelcontextprotocol/server';

server.registerPrompt(
  'explain-code',
  {
    title: 'Explain Code',
    description: 'Generate a clear explanation of a code snippet',
    argsSchema: z.object({
      code: z.string().describe('Code to explain'),
      language: completable(
        z.string().describe('Programming language'),
        (value) => ['typescript', 'python', 'go', 'rust', 'java']
          .filter(l => l.startsWith(value.toLowerCase()))
      ),
      audience: z.enum(['beginner', 'intermediate', 'expert']).default('intermediate')
    })
  },
  ({ code, language, audience }) => ({
    messages: [{
      role: 'user' as const,
      content: {
        type: 'text' as const,
        text: `Explain this ${language} code for a ${audience} developer:\n\n\`\`\`${language}\n${code}\n\`\`\``
      }
    }]
  })
);
```

### Python (FastMCP)

```python
@mcp.prompt()
def explain_code(code: str, language: str = "python", audience: str = "intermediate") -> str:
    """Generate a clear explanation of a code snippet."""
    return f"Explain this {language} code for a {audience} developer:\n\n```{language}\n{code}\n```"
```

## Completions

Wrap schema fields with `completable()` to provide autocompletion suggestions:

```typescript
language: completable(
  z.string().describe('Language'),
  (value) => ['typescript', 'python', 'go'].filter(l => l.startsWith(value))
)
```

The client calls `completion/complete` and the server returns matching suggestions. Works for both prompt arguments and resource template parameters.

## Multi-Message Prompts

Prompts can return multiple messages to set up a conversation:

### TypeScript

```typescript
server.registerPrompt(
  'debug-session',
  {
    title: 'Debug Session',
    argsSchema: z.object({ error: z.string(), context: z.string() })
  },
  ({ error, context }) => ({
    messages: [
      {
        role: 'user' as const,
        content: { type: 'text' as const, text: `Error: ${error}\nContext: ${context}` }
      },
      {
        role: 'assistant' as const,
        content: { type: 'text' as const, text: 'Let me analyze this error systematically.' }
      },
      {
        role: 'user' as const,
        content: { type: 'text' as const, text: 'What is the root cause and how do I fix it?' }
      }
    ]
  })
);
```

### Python (FastMCP)

```python
from fastmcp.prompts.base import UserMessage, AssistantMessage

@mcp.prompt()
def debug_session(error: str, context: str) -> list:
    """Guided debugging session."""
    return [
        UserMessage(f"Error: {error}\nContext: {context}"),
        AssistantMessage("Let me analyze this error systematically."),
        UserMessage("What is the root cause and how do I fix it?")
    ]
```

## Prompts with Embedded Resources

Prompts can reference resources to include context:

```typescript
({ projectPath }) => ({
  messages: [{
    role: 'user' as const,
    content: [
      { type: 'text' as const, text: 'Review this project:' },
      {
        type: 'resource' as const,
        resource: {
          uri: `file://${projectPath}/README.md`,
          mimeType: 'text/markdown',
          text: readFileSync(join(projectPath, 'README.md'), 'utf-8')
        }
      }
    ]
  }]
})
```

## Protocol Operations

| Method | Purpose |
|--------|---------|
| `prompts/list` | Discover available prompts |
| `prompts/get` | Retrieve prompt with resolved arguments |
| `completion/complete` | Get autocompletion suggestions |

## Design Patterns

### Database Server Primitives

| Primitive | Name | Purpose |
|-----------|------|---------|
| Resource | `db://schema` | Database schema for context |
| Resource Template | `db://tables/{name}` | Table data access |
| Tool | `query` | Execute SQL queries |
| Tool | `list-tables` | Discover available tables |
| Prompt | `analyze-data` | Guided data analysis workflow |

### API Wrapper Primitives

| Primitive | Name | Purpose |
|-----------|------|---------|
| Resource | `api://docs` | API documentation |
| Tool | `api-get` | GET requests |
| Tool | `api-post` | POST requests |
| Prompt | `explore-api` | Guided API exploration |

### File System Primitives

| Primitive | Name | Purpose |
|-----------|------|---------|
| Resource Template | `file://{path}` | File contents |
| Tool | `list-files` | Directory listing |
| Tool | `read-file` | Read file contents |
| Tool | `write-file` | Write file contents |
| Tool | `search-files` | Search by content or pattern |
