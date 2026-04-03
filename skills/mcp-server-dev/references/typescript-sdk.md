# TypeScript SDK v2

Sources: MCP TypeScript SDK v2 documentation (2026), MCP Specification (2025-06-18), modelcontextprotocol/typescript-sdk repository

Covers: McpServer API, tool/resource/prompt registration with Zod, transports (stdio, Streamable HTTP), Express and Hono middleware, server instructions, completions, logging, progress, server-initiated requests (sampling, elicitation), and shutdown patterns.

## Installation

```bash
npm install @modelcontextprotocol/server zod
# For Streamable HTTP with Express:
npm install @modelcontextprotocol/express @modelcontextprotocol/node
# For Hono (Cloudflare Workers, Deno, Bun):
npm install @modelcontextprotocol/hono
```

The SDK is split into packages:

| Package | Purpose |
|---------|---------|
| `@modelcontextprotocol/server` | Core McpServer, transports, primitives |
| `@modelcontextprotocol/node` | Node.js Streamable HTTP transport |
| `@modelcontextprotocol/express` | Express middleware with DNS rebinding protection |
| `@modelcontextprotocol/hono` | Hono middleware for Web Standard runtimes |

## McpServer Basics

```typescript
import { McpServer, StdioServerTransport } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

const server = new McpServer(
  { name: 'my-server', version: '1.0.0' },
  {
    instructions: 'Call list_tables before running queries. Results limited to 1000 rows.',
    capabilities: { logging: {} }
  }
);
```

The `instructions` field describes cross-tool relationships and constraints. Clients may inject these into the system prompt. Keep instructions concise — do not duplicate tool descriptions.

## Registering Tools

Tools are the primary MCP primitive. Register with `registerTool`:

```typescript
server.registerTool(
  'search-users',
  {
    title: 'Search Users',
    description: 'Search users by name or email. Returns matching user profiles.',
    inputSchema: z.object({
      query: z.string().describe('Search term — name or email'),
      limit: z.number().min(1).max(100).default(10)
    }),
    outputSchema: z.object({
      users: z.array(z.object({
        id: z.string(),
        name: z.string(),
        email: z.string()
      }))
    }),
    annotations: {
      readOnlyHint: true,
      openWorldHint: false
    }
  },
  async ({ query, limit }) => {
    const users = await db.searchUsers(query, limit);
    const output = { users };
    return {
      content: [{ type: 'text', text: JSON.stringify(output) }],
      structuredContent: output
    };
  }
);
```

### Key Registration Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Unique identifier — kebab-case recommended |
| `title` | No | Human-readable display name |
| `description` | Yes | Drives LLM tool selection — be specific |
| `inputSchema` | Yes | Zod schema for argument validation |
| `outputSchema` | No | Zod schema for structured return values |
| `annotations` | No | Hints: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` |

### Tool Annotations

Annotations hint at behavior without changing execution:

| Annotation | Default | Meaning |
|-----------|---------|---------|
| `readOnlyHint` | false | Tool does not modify state |
| `destructiveHint` | true | Tool may perform irreversible actions |
| `idempotentHint` | false | Safe to retry with same arguments |
| `openWorldHint` | true | Tool interacts with external systems |

### Error Handling

Return `isError: true` for tool-level errors the LLM can reason about:

```typescript
async ({ url }): Promise<CallToolResult> => {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      return {
        content: [{ type: 'text', text: `HTTP ${res.status}: ${res.statusText}` }],
        isError: true
      };
    }
    return { content: [{ type: 'text', text: await res.text() }] };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Failed: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true
    };
  }
}
```

When `isError` is true, output schema validation is skipped. If a handler throws instead of returning `isError`, the SDK catches it automatically — but explicit try/catch gives control over the error message.

### ResourceLink Outputs

Return resource links instead of embedding large content:

```typescript
return {
  content: [{
    type: 'resource_link',
    uri: 'file:///projects/readme.md',
    name: 'README',
    mimeType: 'text/markdown'
  }]
};
```

## Registering Resources

Static resource at a fixed URI:

```typescript
server.registerResource(
  'schema',
  'db://schema/main',
  { title: 'Database Schema', mimeType: 'application/json' },
  async (uri) => ({
    contents: [{ uri: uri.href, text: JSON.stringify(await db.getSchema()) }]
  })
);
```

Dynamic resource with URI template:

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
  'user-profile',
  new ResourceTemplate('users://{userId}/profile', {
    list: async () => ({
      resources: (await db.listUsers()).map(u => ({
        uri: `users://${u.id}/profile`,
        name: u.name
      }))
    })
  }),
  { title: 'User Profile', mimeType: 'application/json' },
  async (uri, { userId }) => ({
    contents: [{ uri: uri.href, text: JSON.stringify(await db.getUser(userId)) }]
  })
);
```

## Registering Prompts

```typescript
server.registerPrompt(
  'review-code',
  {
    title: 'Code Review',
    description: 'Review code for best practices and issues',
    argsSchema: z.object({
      code: z.string(),
      language: completable(
        z.string().describe('Programming language'),
        (value) => ['typescript', 'python', 'go', 'rust']
          .filter(l => l.startsWith(value))
      )
    })
  },
  ({ code, language }) => ({
    messages: [{
      role: 'user' as const,
      content: { type: 'text' as const, text: `Review this ${language} code:\n\n${code}` }
    }]
  })
);
```

Use `completable()` to wrap schema fields that support autocompletion.

## Transport: stdio

For local servers spawned by Claude Desktop, OpenCode, or CLI tools:

```typescript
const transport = new StdioServerTransport();
await server.connect(transport);
```

Shutdown:

```typescript
process.on('SIGINT', async () => {
  await server.close();
  process.exit(0);
});
```

## Transport: Streamable HTTP

For remote servers accessible over the network:

```typescript
import { createMcpExpressApp } from '@modelcontextprotocol/express';

const app = createMcpExpressApp(server, {
  sessionIdGenerator: () => randomUUID()
});

const httpServer = app.listen(3000);
```

`createMcpExpressApp` provides DNS rebinding protection by default for localhost servers. For Hono-based servers (Cloudflare Workers, Deno, Bun):

```typescript
import { createMcpHonoApp } from '@modelcontextprotocol/hono';

const app = createMcpHonoApp(server, {
  sessionIdGenerator: () => randomUUID()
});
```

Set `sessionIdGenerator` to `undefined` for stateless mode — simpler but no resumability.

### Shutdown with Sessions

```typescript
const transports = new Map();
process.on('SIGINT', async () => {
  httpServer.close();
  for (const [id, transport] of transports) {
    await transport.close();
    transports.delete(id);
  }
  process.exit(0);
});
```

## Logging

Declare capability, then log from handlers:

```typescript
const server = new McpServer(
  { name: 'my-server', version: '1.0.0' },
  { capabilities: { logging: {} } }
);

// Inside any tool handler:
async (args, ctx): Promise<CallToolResult> => {
  await ctx.mcpReq.log('info', `Processing ${args.query}`);
  // ...
}
```

Levels: `debug`, `info`, `warning`, `error`, `critical`.

## Progress Reporting

Report incremental status for long-running operations:

```typescript
async ({ files }, ctx): Promise<CallToolResult> => {
  const progressToken = ctx.mcpReq._meta?.progressToken;
  for (let i = 0; i < files.length; i++) {
    await processFile(files[i]);
    if (progressToken !== undefined) {
      await ctx.mcpReq.notify({
        method: 'notifications/progress',
        params: { progressToken, progress: i + 1, total: files.length, message: `Processed ${files[i]}` }
      });
    }
  }
  return { content: [{ type: 'text', text: `Processed ${files.length} files` }] };
}
```

## Server-Initiated Requests

### Sampling

Request LLM completion from the connected client:

```typescript
async ({ text }, ctx): Promise<CallToolResult> => {
  const response = await ctx.mcpReq.requestSampling({
    messages: [{ role: 'user', content: { type: 'text', text: `Summarize: ${text}` } }],
    maxTokens: 500
  });
  return { content: [{ type: 'text', text: JSON.stringify(response.content) }] };
}
```

### Elicitation

Request user input via form or URL redirect:

```typescript
const result = await ctx.mcpReq.elicitInput({
  mode: 'form',
  message: 'Confirm deletion:',
  requestedSchema: {
    type: 'object',
    properties: { confirm: { type: 'boolean', title: 'Delete all files?' } },
    required: ['confirm']
  }
});
if (result.action === 'accept' && result.content.confirm) {
  // proceed
}
```

Use `mode: 'url'` for sensitive data (API keys, payments) — never collect secrets via form elicitation.

## TypeScript Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| `structuredContent` type error | Using `interface` instead of `type` | Use `type` alias or spread: `{ ...result }` |
| Tool not appearing | Missing or empty `description` | Add specific description explaining when to use |
| Schema validation fails | Zod v4 import path | Use `import * as z from 'zod/v4'` |
| DNS rebinding on localhost | No host validation | Use `createMcpExpressApp()` — protection is automatic |
| Session lost on reconnect | No event store | Add `InMemoryEventStore` for resumability |
