# Testing and Deployment

Sources: MCP Inspector documentation (2026), TypeScript SDK v2 examples, FastMCP 3 testing guide, Vercel/Cloudflare Workers deployment patterns, Docker MCP server guides

Covers: MCP Inspector for interactive testing, programmatic testing patterns (TypeScript and Python), CI/CD integration, deployment to Vercel serverless, Cloudflare Workers, Docker, local npm/PyPI publishing, and registry submission (smithery.ai, glama.ai).

## MCP Inspector

The MCP Inspector is the primary tool for interactive testing and debugging MCP servers. It provides a web UI for discovering tools, resources, and prompts, and executing them with custom parameters.

### Installation and Usage

```bash
# Run against a local stdio server:
npx @modelcontextprotocol/inspector node server.js

# Run against a Python server:
npx @modelcontextprotocol/inspector python server.py

# Run against a remote HTTP server:
npx @modelcontextprotocol/inspector --url http://localhost:3000/mcp

# FastMCP shortcut:
fastmcp dev server.py
```

### Inspector Capabilities

| Feature | Description |
|---------|-------------|
| Tool discovery | Lists all registered tools with schemas |
| Tool execution | Execute tools with custom JSON parameters |
| Resource browsing | List and read static resources and templates |
| Prompt testing | List prompts and render with arguments |
| Notification viewer | See server notifications in real-time |
| Request/response log | Full JSON-RPC message history |
| Connection status | Transport state and session info |

### Inspector Workflow

1. Start inspector with your server command
2. Verify all tools appear in the tools panel
3. Execute each tool with valid and invalid inputs
4. Check error responses return `isError: true` with useful messages
5. Verify resources list and read correctly
6. Test prompts render with expected message structure
7. Check server instructions appear in the connection panel

## Programmatic Testing: TypeScript

### Unit Testing Tools

```typescript
import { McpServer, StdioServerTransport } from '@modelcontextprotocol/server';
import { Client } from '@modelcontextprotocol/client';
import { InMemoryTransport } from '@modelcontextprotocol/client/transport';

describe('MCP Server', () => {
  let server: McpServer;
  let client: Client;

  beforeEach(async () => {
    server = new McpServer({ name: 'test', version: '1.0.0' });
    // Register tools...

    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    await server.connect(serverTransport);
    client = new Client({ name: 'test-client', version: '1.0.0' });
    await client.connect(clientTransport);
  });

  afterEach(async () => {
    await client.close();
    await server.close();
  });

  test('list tools returns registered tools', async () => {
    const { tools } = await client.listTools();
    expect(tools).toHaveLength(3);
    expect(tools.map(t => t.name)).toContain('search-users');
  });

  test('search-users returns results', async () => {
    const result = await client.callTool('search-users', {
      query: 'alice',
      limit: 5
    });
    expect(result.isError).toBeFalsy();
    const data = JSON.parse(result.content[0].text);
    expect(data.users).toHaveLength(1);
  });

  test('invalid input returns isError', async () => {
    const result = await client.callTool('search-users', {
      query: '',  // Empty — should fail validation
      limit: -1   // Negative — should fail validation
    });
    expect(result.isError).toBe(true);
  });
});
```

### Integration Testing with Real Transport

```typescript
import { spawn } from 'child_process';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/transport';

test('server works via stdio', async () => {
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['./dist/server.js']
  });
  const client = new Client({ name: 'test', version: '1.0.0' });
  await client.connect(transport);

  const { tools } = await client.listTools();
  expect(tools.length).toBeGreaterThan(0);

  await client.close();
});
```

## Programmatic Testing: Python (FastMCP)

### Unit Testing with InMemoryTransport

```python
import pytest
from fastmcp import FastMCP, Client

mcp = FastMCP("test-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Division by zero")
    return a / b

@pytest.mark.anyio
async def test_list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "add" in names
        assert "divide" in names

@pytest.mark.anyio
async def test_add():
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 2, "b": 3})
        assert result[0].text == "5"

@pytest.mark.anyio
async def test_divide_by_zero():
    async with Client(mcp) as client:
        result = await client.call_tool("divide", {"a": 10, "b": 0})
        assert result.isError is True
```

`Client(mcp)` uses `InMemoryTransport` — no network, no process spawning. Fast and isolated for unit tests.

### Testing with Real HTTP Transport

```python
import httpx
import pytest

@pytest.fixture
async def server_url():
    # Start server in background
    proc = await asyncio.create_subprocess_exec(
        "fastmcp", "run", "server.py",
        "--transport", "streamable-http", "--port", "8765"
    )
    await asyncio.sleep(2)  # Wait for startup
    yield "http://localhost:8765"
    proc.terminate()

@pytest.mark.anyio
async def test_http_health(server_url):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{server_url}/mcp", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        })
        assert resp.status_code == 200
```

## CI/CD Integration

### GitHub Actions (TypeScript)

```yaml
name: Test MCP Server
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npm test
      - run: npm run build
      # Smoke test with Inspector
      - run: |
          npx @modelcontextprotocol/inspector \
            --test node dist/server.js
```

### GitHub Actions (Python)

```yaml
name: Test FastMCP Server
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e ".[dev]"
      - run: pytest tests/
```

## Deployment: Vercel Serverless

```typescript
// api/mcp.ts (Vercel Edge Function)
import { McpServer } from '@modelcontextprotocol/server';
import { createMcpHonoApp } from '@modelcontextprotocol/hono';

const server = new McpServer({ name: 'vercel-mcp', version: '1.0.0' });
// Register tools...

const app = createMcpHonoApp(server, {
  sessionIdGenerator: undefined  // Stateless for serverless
});

export default app;
```

```json
// vercel.json
{
  "rewrites": [{ "source": "/mcp/(.*)", "destination": "/api/mcp" }]
}
```

Key considerations for serverless:
- Use stateless mode (`sessionIdGenerator: undefined`)
- No persistent connections — each request is independent
- Cold starts may affect first-request latency
- Environment variables for secrets (Vercel project settings)

## Deployment: Cloudflare Workers

```typescript
// src/index.ts
import { McpServer } from '@modelcontextprotocol/server';
import { createMcpHonoApp } from '@modelcontextprotocol/hono';

const server = new McpServer({ name: 'cf-mcp', version: '1.0.0' });
// Register tools...

const app = createMcpHonoApp(server, {
  sessionIdGenerator: undefined
});

export default app;
```

```toml
# wrangler.toml
name = "my-mcp-server"
main = "src/index.ts"
compatibility_date = "2026-01-01"

[vars]
API_KEY = "set-in-dashboard"
```

Deploy: `wrangler deploy`

## Deployment: Docker

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

```bash
docker build -t my-mcp-server .
docker run -p 3000:3000 \
  -e API_KEY="$API_KEY" \
  --read-only \
  my-mcp-server
```

For stdio servers that need to run in Docker:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "my-mcp-server"]
    }
  }
}
```

The `-i` flag keeps stdin open for stdio transport.

## Publishing: npm

```json
// package.json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "bin": { "my-mcp-server": "./dist/server.js" },
  "files": ["dist"],
  "keywords": ["mcp", "model-context-protocol"]
}
```

```bash
npm publish
```

Users install: `npx my-mcp-server` or configure in their MCP client.

## Publishing: PyPI

```toml
# pyproject.toml
[project]
name = "my-mcp-server"
version = "1.0.0"
dependencies = ["fastmcp>=3.0"]

[project.scripts]
my-mcp-server = "my_mcp_server:main"
```

```bash
uv build && uv publish
```

Users install: `uvx my-mcp-server` or `pip install my-mcp-server`.

## Publishing: Registries

### smithery.ai

1. Create account at smithery.ai
2. Add `smithery.yaml` to your repository:

```yaml
name: my-mcp-server
description: Brief description
startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      apiKey:
        type: string
    required: [apiKey]
  commandFunction: |
    (config) => ({
      command: "npx",
      args: ["-y", "my-mcp-server"],
      env: { API_KEY: config.apiKey }
    })
```

3. Submit via smithery.ai dashboard

### glama.ai

Submit your server at glama.ai/mcp/servers. Include:
- Repository URL
- Server description
- Configuration instructions
- Example tool definitions

## Testing Checklist

| Test Type | What to Verify |
|-----------|---------------|
| Tool discovery | All tools appear with correct names and schemas |
| Valid input | Tools return expected results |
| Invalid input | Tools return `isError: true` with helpful messages |
| Edge cases | Empty strings, max values, special characters |
| Error conditions | Network failures, missing data, timeouts |
| Resources | List and read all resources |
| Prompts | Render with correct message structure |
| Auth (remote) | Unauthorized requests rejected, valid tokens accepted |
| Security | Path traversal, injection attempts blocked |
| Performance | Response time within acceptable bounds |
