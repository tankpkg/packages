---
name: "@tank/mcp-server-dev"
description: |
  Build, test, secure, and deploy Model Context Protocol (MCP) servers in
  TypeScript and Python. Covers MCP architecture (hosts, clients, servers,
  transports), the three primitives (tools, resources, prompts), TypeScript
  SDK v2 (@modelcontextprotocol/sdk with McpServer, Zod schemas, Streamable
  HTTP, Express/Hono middleware), Python FastMCP 3 (decorators, Pydantic
  validation, lifespan, composition), tool design (inputSchema, outputSchema,
  annotations, error handling, progress, structured output), resource patterns
  (static URIs, dynamic templates, subscriptions), prompt templates, transport
  selection (stdio vs Streamable HTTP vs SSE), OAuth 2.1 authentication for
  remote servers, security hardening (OWASP MCP cheat sheet, tool poisoning
  defense, input validation, sandboxing, DNS rebinding protection), testing
  with MCP Inspector, deployment (Vercel, Cloudflare Workers, Docker,
  local stdio), and publishing to registries (npm, PyPI, smithery.ai).

  Synthesizes MCP Specification (2025-06-18), TypeScript SDK v2 docs,
  FastMCP 3 docs, OWASP MCP Security Cheat Sheet, and production server
  patterns from Anthropic reference implementations.

  Trigger phrases: "MCP server", "build MCP server", "MCP TypeScript",
  "MCP Python", "FastMCP", "model context protocol", "MCP tools",
  "MCP resources", "MCP prompts", "MCP transport", "Streamable HTTP",
  "MCP OAuth", "MCP security", "tool poisoning", "MCP Inspector",
  "MCP deploy", "MCP Vercel", "MCP Cloudflare Workers", "MCP Docker",
  "mcp-server-dev", "@modelcontextprotocol/sdk", "McpServer",
  "MCP testing", "MCP publish", "MCP stdio"
---

# MCP Server Development

## Core Philosophy

1. **Tools are the primary interface** — Most LLM interactions go through tools. Design tools first, add resources for context and prompts for canned workflows.
2. **Validate everything, trust nothing** — Tool inputs originate from LLM output shaped by potentially adversarial context. Validate with Zod/Pydantic, sanitize against injection, constrain with `additionalProperties: false`.
3. **Return errors, don't throw them** — Set `isError: true` so the LLM can self-correct. Thrown exceptions become opaque protocol errors the model cannot reason about.
4. **Choose transport by deployment** — stdio for local CLI integrations (Claude Desktop, OpenCode). Streamable HTTP for remote servers accessible over the network. Never mix them.
5. **Scope permissions to the minimum** — Each server gets its own credentials with narrow OAuth scopes. Broad tokens across servers create aggregation risk and confused deputy attacks.

## Quick-Start: Common Problems

### "How do I create a basic MCP server?"

| Language | Command |
|----------|---------|
| TypeScript | `npm init -y && npm i @modelcontextprotocol/server zod` |
| Python | `pip install fastmcp` or `uv add fastmcp` |

1. Register tools with typed schemas (Zod for TS, type hints for Python)
2. Choose transport: `StdioServerTransport` for local, `NodeStreamableHTTPServerTransport` for remote
3. Connect: `server.connect(transport)`
4. Test with MCP Inspector: `npx @modelcontextprotocol/inspector`
-> See `references/typescript-sdk.md` and `references/python-fastmcp.md`

### "My tool returns data but the LLM ignores it"

1. Check `description` — it drives LLM tool selection. Be specific about when and why to use the tool
2. Return `content: [{ type: 'text', text: '...' }]` — not raw objects
3. Add `outputSchema` for structured responses the LLM can parse reliably
4. Use `isError: true` for failures instead of empty responses
-> See `references/tool-design.md`

### "How do I add authentication to my remote server?"

1. Remote servers (Streamable HTTP) need OAuth 2.1 or bearer tokens
2. Use `@modelcontextprotocol/express` or FastMCP's auth providers for built-in OAuth
3. Validate tokens on every request — bind sessions to user identity
4. Never store tokens in config files; use OS secure credential storage
-> See `references/auth-transport.md`

### "How do I test my MCP server?"

1. MCP Inspector: `npx @modelcontextprotocol/inspector` — visual tool testing
2. Programmatic: create a client, call `tools/list` and `tools/call`, assert results
3. FastMCP: `InMemoryTransport` for unit tests without network
4. Integration: test against real data sources in CI
-> See `references/testing-deployment.md`

## Decision Trees

### SDK Selection

| Signal | SDK |
|--------|-----|
| TypeScript/Node.js project | `@modelcontextprotocol/server` (v2) + Zod |
| Python project | FastMCP 3 (`fastmcp`) |
| Go project | `mcp-go` |
| Wrapping an OpenAPI spec | FastMCP `from_openapi()` |
| Need both languages | Build two servers; compose at the host level |

### Transport Selection

| Deployment | Transport | Session |
|------------|-----------|---------|
| Claude Desktop / local CLI | stdio | Single client |
| Remote API server | Streamable HTTP | Multi-client, stateful |
| Legacy SSE requirement | SSE (deprecated) | Multi-client |
| Serverless (Vercel/CF Workers) | Streamable HTTP (stateless) | Per-request |

### Primitive Selection

| Need | Primitive | Who Controls |
|------|-----------|-------------|
| LLM executes an action | Tool | Model decides |
| Read-only context data | Resource | Application decides |
| Canned interaction pattern | Prompt | User invokes |
| Structured LLM output | Tool with `outputSchema` | Model decides |

## Reference Index

| File | Contents |
|------|----------|
| `references/typescript-sdk.md` | TypeScript SDK v2: McpServer, registerTool, registerResource, registerPrompt, Zod schemas, Express/Hono middleware, server instructions, completions |
| `references/python-fastmcp.md` | FastMCP 3: decorators, Pydantic, Context, lifespan, composition, OpenAPI import, dependency injection, middleware |
| `references/tool-design.md` | Tool definition patterns: inputSchema, outputSchema, annotations, error handling, progress reporting, ResourceLink outputs, multi-tool servers, naming conventions |
| `references/resources-prompts.md` | Resource patterns (static, dynamic templates, subscriptions), prompt templates, argument completions, URI design, MIME types |
| `references/auth-transport.md` | Transport mechanics (stdio, Streamable HTTP, SSE), OAuth 2.1 for remote servers, bearer tokens, session management, DNS rebinding protection |
| `references/security.md` | OWASP MCP security: tool poisoning defense, input/output validation, sandboxing, supply chain, cross-server isolation, prompt injection via return values |
| `references/testing-deployment.md` | MCP Inspector, programmatic testing, InMemoryTransport, deployment (Vercel, Cloudflare Workers, Docker, npm/PyPI publishing), CI/CD patterns |
