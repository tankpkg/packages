# Authentication and Transport

Sources: MCP Specification (2025-06-18), TypeScript SDK v2 documentation, FastMCP 3 auth documentation, OWASP MCP Security Cheat Sheet (2026)

Covers: transport mechanisms (stdio, Streamable HTTP, SSE), transport selection, Streamable HTTP session management, OAuth 2.1 for remote MCP servers, bearer token authentication, DNS rebinding protection, and secure credential storage.

## Transport Overview

MCP supports two transport mechanisms. The transport layer abstracts communication from the protocol layer — the same JSON-RPC 2.0 messages work across both.

| Transport | Use Case | Session | Network |
|-----------|----------|---------|---------|
| stdio | Local servers spawned as child processes | Single client | None (process pipes) |
| Streamable HTTP | Remote servers accessible over network | Multi-client, stateful or stateless | HTTP/HTTPS |

### Deprecated: SSE Transport

The SSE (Server-Sent Events) transport is deprecated in favor of Streamable HTTP. Streamable HTTP subsumes SSE capabilities — it uses HTTP POST for client-to-server messages and optional SSE for server-to-client streaming.

Migrate existing SSE servers to Streamable HTTP. The SDK handles backward compatibility.

## stdio Transport

stdio uses standard input/output streams for direct process communication. The host spawns the server as a child process and communicates via stdin/stdout.

### When to Use stdio

- Claude Desktop, OpenCode, Cursor, or other local AI applications
- CLI tools that spawn MCP servers
- Development and testing
- Single-user, single-machine scenarios

### TypeScript

```typescript
import { McpServer, StdioServerTransport } from '@modelcontextprotocol/server';

const server = new McpServer({ name: 'local-server', version: '1.0.0' });
// ... register tools ...

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python (FastMCP)

```python
mcp = FastMCP("local-server")
# ... register tools ...

if __name__ == "__main__":
    mcp.run()  # Defaults to stdio transport
```

### stdio Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/path/to/server/index.js"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### stdio Characteristics

| Property | Value |
|----------|-------|
| Latency | Lowest (no network) |
| Security | Process isolation only |
| Concurrency | Single client |
| Authentication | Not needed (trusted local process) |
| Deployment | Bundled with host application |

## Streamable HTTP Transport

Streamable HTTP uses HTTP POST for client-to-server messages with optional SSE for streaming responses. This is the standard for remote, multi-client servers.

### When to Use Streamable HTTP

- Remote servers accessible over the internet
- Multi-user/multi-client scenarios
- Serverless deployment (Vercel, Cloudflare Workers)
- Servers that need authentication

### TypeScript with Express

```typescript
import { randomUUID } from 'node:crypto';
import { createMcpExpressApp } from '@modelcontextprotocol/express';

const server = new McpServer({ name: 'remote-server', version: '1.0.0' });
// ... register tools ...

const app = createMcpExpressApp(server, {
  sessionIdGenerator: () => randomUUID()
});

app.listen(3000, () => console.log('MCP server on port 3000'));
```

### TypeScript with Hono (Cloudflare Workers, Deno, Bun)

```typescript
import { createMcpHonoApp } from '@modelcontextprotocol/hono';

const server = new McpServer({ name: 'edge-server', version: '1.0.0' });
const app = createMcpHonoApp(server, {
  sessionIdGenerator: () => randomUUID()
});

export default app;  // Cloudflare Workers export
```

### Python (FastMCP)

```bash
fastmcp run server.py --transport streamable-http --port 8000
```

Or programmatically:

```python
mcp = FastMCP("remote-server")
# ... register tools ...

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
```

### Session Management

Stateful sessions track client connections:

```typescript
const transports = new Map<string, NodeStreamableHTTPServerTransport>();

const app = createMcpExpressApp(server, {
  sessionIdGenerator: () => randomUUID(),
  onSessionCreated: (sessionId, transport) => {
    transports.set(sessionId, transport);
  },
  onSessionClosed: (sessionId) => {
    transports.delete(sessionId);
  }
});
```

Set `sessionIdGenerator: undefined` for stateless mode — simpler deployment but no resumability or server-initiated requests.

### Stateful vs Stateless

| Mode | sessionIdGenerator | Use Case |
|------|-------------------|----------|
| Stateful | `() => randomUUID()` | Long-lived connections, server push, resumability |
| Stateless | `undefined` | Serverless, simple request-response |

## DNS Rebinding Protection

DNS rebinding attacks make cross-origin requests appear same-origin by resolving an attacker's domain to localhost. All localhost MCP servers need protection.

### Automatic Protection

`createMcpExpressApp()` and `createMcpHonoApp()` enable Host header validation by default:

```typescript
// Auto-protected for localhost:
const app = createMcpExpressApp(server);

// Auto-protected for 127.0.0.1:
const app = createMcpExpressApp(server, { host: '127.0.0.1' });

// No automatic protection when binding to all interfaces:
const app = createMcpExpressApp(server, {
  host: '0.0.0.0',
  allowedHosts: ['localhost', '127.0.0.1', 'myhost.local']
});
```

When binding to `0.0.0.0` or `::`, provide an explicit `allowedHosts` list.

### Manual Protection

If using `NodeStreamableHTTPServerTransport` directly, validate the Host header in middleware:

```typescript
app.use((req, res, next) => {
  const host = req.headers.host;
  if (!allowedHosts.includes(host)) {
    res.status(403).send('Forbidden');
    return;
  }
  next();
});
```

## OAuth 2.1 Authentication

Remote MCP servers use OAuth 2.1 for authentication. The MCP specification recommends OAuth with PKCE for client authorization.

### OAuth Flow for MCP

```
1. Client discovers server metadata:
   GET /.well-known/oauth-authorization-server

2. Client initiates Authorization Code + PKCE flow:
   GET /authorize?response_type=code&code_challenge=...

3. User authenticates and consents

4. Client exchanges code for tokens:
   POST /token (grant_type=authorization_code, code_verifier=...)

5. Client includes token in MCP requests:
   Authorization: Bearer <access_token>
```

### TypeScript OAuth Setup

Use the Express/Hono middleware with an OAuth provider:

```typescript
import { createMcpExpressApp } from '@modelcontextprotocol/express';

const app = createMcpExpressApp(server, {
  auth: {
    issuer: 'https://auth.example.com',
    audience: 'my-mcp-server',
    jwksUri: 'https://auth.example.com/.well-known/jwks.json'
  }
});
```

### Python OAuth Setup (FastMCP)

FastMCP provides built-in OAuth proxy for popular providers:

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubOAuthProvider

mcp = FastMCP(
    "my-server",
    auth=GitHubOAuthProvider(
        client_id="your-client-id",
        client_secret="your-client-secret",
        required_scopes=["read:user"]
    )
)
```

Available providers: Auth0, GitHub, Google, Azure, AWS Cognito, Discord, Supabase, WorkOS, Descope, PropelAuth.

### Access User Identity

```python
@mcp.tool()
async def get_my_repos(ctx: Context) -> list[dict]:
    """List repositories for the authenticated user."""
    token = ctx.request_context.access_token
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {token}"}
        )
        return resp.json()
```

## Bearer Token Authentication

For simpler authentication without full OAuth:

### Python (FastMCP)

```python
from fastmcp.server.auth.providers.jwt import JWTAuthProvider

mcp = FastMCP(
    "my-server",
    auth=JWTAuthProvider(
        jwks_uri="https://auth.example.com/.well-known/jwks.json",
        audience="my-server",
        issuer="https://auth.example.com"
    )
)
```

### Manual Token Validation (TypeScript)

```typescript
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'No token' });
  try {
    const payload = await verifyJWT(token, { audience: 'my-server' });
    req.user = payload;
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
});
```

## Secure Credential Storage

| Platform | Storage |
|----------|---------|
| macOS | Keychain (`security` CLI) |
| Windows | Credential Manager |
| Linux | Secret Service (GNOME Keyring, KWallet) |
| Server-side | Environment variables, Vault, AWS Secrets Manager |

Never store OAuth tokens in:
- MCP config files (JSON)
- Application settings files
- Environment variables in code
- Browser localStorage

## Transport Security Checklist

| Check | stdio | Streamable HTTP |
|-------|-------|-----------------|
| TLS required | No (local pipes) | Yes (HTTPS in production) |
| Authentication needed | No (trusted process) | Yes (OAuth 2.1 or bearer) |
| DNS rebinding protection | N/A | Yes (Host header validation) |
| Session binding | N/A | Bind to user identity |
| Rate limiting | N/A | Yes (per session/tenant) |
| CORS | N/A | Configure for browser clients |
| Credential storage | OS secure storage | OS secure storage or vault |

## Common Mistakes

| Mistake | Risk | Fix |
|---------|------|-----|
| HTTP without TLS for remote | Token interception | Always use HTTPS in production |
| Binding to 0.0.0.0 without Host validation | DNS rebinding | Use `allowedHosts` or bind to 127.0.0.1 |
| Shared tokens across servers | Aggregation risk, confused deputy | One credential per server, narrow scopes |
| Tokens in config files | Credential exposure | OS secure storage or vault |
| No session binding | Session hijack | Bind session to user identity |
| Stateful sessions on serverless | Session loss | Use stateless mode or external session store |
