# MCP Primer for Tool Wiring

Sources: MCP Specification (2025-06-18), Anthropic MCP documentation, OWASP MCP Security Cheat Sheet

Covers: what MCP is, the host/client/server architecture, transport mechanisms,
authentication, and how the three MCP primitives (tools, resources, prompts)
map to agent capabilities. This reference focuses on the consumer side --
understanding MCP well enough to wire servers, not build them.

## What MCP Is

The Model Context Protocol is a JSON-RPC 2.0 based protocol that standardizes
how AI agent hosts (Claude Desktop, OpenCode, Cursor) connect to external
capability servers. Before MCP, every host had its own plugin format. MCP
provides one interface that works across hosts.

Key terminology:

| Term | Role | Example |
|------|------|---------|
| Host | The AI application the user runs | Claude Desktop, OpenCode, Cursor |
| Client | Protocol handler inside the host | One client per connected server |
| Server | External process exposing capabilities | `@modelcontextprotocol/server-github` |
| Transport | Wire format between client and server | STDIO pipes, HTTP requests |

The relationship is always: Host contains Client(s), each Client connects to
exactly one Server over a Transport.

## Architecture: How Hosts Discover Servers

Hosts maintain a configuration that lists MCP servers to connect to. The
configuration format varies by host, but the pattern is consistent:

1. User (or a package manager like Tank) adds a server entry to the config
2. Host reads the config on startup (or reload)
3. Host creates a Client for each server entry
4. Client connects to the Server using the declared transport
5. Client calls `initialize` to negotiate capabilities
6. Client calls `tools/list`, `resources/list`, `prompts/list` to discover
   what the server offers
7. Host presents discovered tools to the LLM as callable functions

This is the flow a Tank tool atom automates. Instead of editing host config
files manually, the tool atom declares the server connection, and the Tank
adapter writes the platform-specific config entry.

## Transport: STDIO vs HTTP

MCP defines two transport mechanisms. The transport choice is fundamental --
it determines how the server process is managed and how data flows.

### STDIO Transport

The host spawns the server as a child process. Communication happens over
the process's stdin (client-to-server) and stdout (server-to-client). Stderr
is reserved for logging.

```
Host Process
  |
  +-- spawns --> Server Process
       stdin  <-- JSON-RPC requests
       stdout --> JSON-RPC responses
       stderr --> diagnostic logs (ignored by protocol)
```

Characteristics:

| Property | Value |
|----------|-------|
| Lifecycle | Host manages server process (start/stop) |
| Connectivity | Local only -- no network |
| Authentication | Not needed -- same machine trust |
| Session | One client per process |
| Config required | `command` (executable), `args` (optional), `env` (optional) |

STDIO is the dominant transport for local tool servers. Most MCP servers in
the wild (GitHub, filesystem, fetch, Playwright) use STDIO.

### Streamable HTTP Transport

The server runs as an HTTP endpoint. The client sends JSON-RPC requests as
HTTP POST to a well-known path (typically `/mcp`). The server can return
responses inline or open a Server-Sent Events (SSE) stream for streaming.

```
Host Process
  |
  +-- HTTP POST /mcp --> Remote Server
  <-- 200 OK (JSON-RPC response)
  <-- or SSE stream (for streaming responses)
```

Characteristics:

| Property | Value |
|----------|-------|
| Lifecycle | Server runs independently -- host does not manage it |
| Connectivity | Network -- can be remote |
| Authentication | OAuth 2.1, bearer tokens, or API keys |
| Session | Multiple clients, stateful via session tokens |
| Config required | `url` (server endpoint), auth credentials |

HTTP transport is used for remote/hosted MCP servers, SaaS integrations, and
serverless deployments.

### Choosing Transport

| Scenario | Transport |
|----------|-----------|
| Server is an npm package the user installs | STDIO |
| Server is a Python script in the repo | STDIO |
| Server is hosted by a SaaS provider | HTTP |
| Server needs to serve multiple users | HTTP |
| Server accesses local filesystem | STDIO (inherits user permissions) |
| Server needs OAuth with a third-party API | HTTP (or STDIO with env tokens) |

## Authentication: OAuth 2.1 for Remote Servers

Remote HTTP servers typically require authentication. MCP specifies OAuth 2.1
as the standard auth flow:

1. Client discovers the OAuth metadata at the server's well-known endpoint
2. Client initiates Authorization Code + PKCE flow
3. User authenticates in browser, grants scopes
4. Client receives access token, attaches to subsequent MCP requests
5. Client uses refresh token to maintain session

For Tank tool atoms, this means:

- The tool atom's extension bag declares the OAuth provider URL and scopes
- The host handles the actual OAuth flow (redirect, token exchange)
- Tank bundles store client IDs but NEVER client secrets
- Env vars reference secrets: `"GITHUB_TOKEN": "${GITHUB_TOKEN}"`

Some simpler servers accept static bearer tokens or API keys instead of full
OAuth. These are passed via environment variables in STDIO or headers in HTTP.

## The Three MCP Primitives

MCP servers expose capabilities through three primitive types. Understanding
these is critical for writing accurate instruction atoms that guide usage.

### Tools

Tools are model-invoked functions. The LLM decides when to call them based
on the tool's name and description. Tools are the primary interaction point.

| Property | Purpose |
|----------|---------|
| `name` | Identifier the LLM uses to invoke the tool |
| `description` | Natural language guide for when to use it |
| `inputSchema` | JSON Schema defining required parameters |
| `outputSchema` | Optional schema for structured return values |
| `annotations` | Metadata: `readOnlyHint`, `destructiveHint`, `openWorldHint` |

Example tools from well-known servers:

| Server | Tool | Purpose |
|--------|------|---------|
| GitHub | `create_issue` | Create a GitHub issue |
| Filesystem | `read_file` | Read a file from disk |
| Fetch | `fetch` | HTTP GET/POST to a URL |
| Playwright | `browser_navigate` | Navigate browser to URL |

### Resources

Resources are application-controlled data sources. Unlike tools, the LLM
does not decide when to read resources -- the host application or user does.
Resources provide context that supplements tool usage.

| Property | Purpose |
|----------|---------|
| `uri` | Unique identifier (e.g., `file:///path`, `github://repo/issues`) |
| `name` | Human-readable label |
| `description` | What the resource contains |
| `mimeType` | Content type (text/plain, application/json) |

Resources are relevant to tool atoms only insofar as the instruction atom
should document what resources the server exposes alongside its tools.

### Prompts

Prompts are user-invoked templates -- canned interaction patterns. They are
less common than tools and resources.

| Property | Purpose |
|----------|---------|
| `name` | Identifier (often exposed as slash commands) |
| `description` | When to use this prompt |
| `arguments` | Parameters the user fills in |

## How Agents Invoke MCP Tools

When a Tank tool atom is installed and the adapter writes the config:

1. Host starts/connects to the MCP server
2. Host calls `tools/list` and receives tool definitions
3. Host injects these tools into the LLM's available function set
4. LLM sees tool names + descriptions alongside other tools
5. When the LLM decides to use a tool, it generates a `tools/call` request
6. Host routes the call through the Client to the Server
7. Server executes and returns results
8. Host passes results back to the LLM

The tool atom makes step 1-2 happen automatically. The instruction atom
(if present) helps step 4 by giving the LLM context about when the tools
are appropriate.

## MCP vs Tank Atoms: Disambiguation

These terms overlap and cause confusion. Clarify:

| Concept | Belongs To | Purpose |
|---------|-----------|---------|
| MCP Tool | MCP Protocol | A callable function exposed by an MCP server |
| MCP Resource | MCP Protocol | A readable data source exposed by an MCP server |
| MCP Prompt | MCP Protocol | A canned interaction template exposed by an MCP server |
| Tank `tool` atom | Tank Package System | A manifest entry that wires an MCP server to a host |
| Tank `resource` atom | Tank Package System | A manifest entry that provides data/context to an agent |
| Tank `instruction` atom | Tank Package System | A manifest entry that injects behavioral context |

A Tank `tool` atom registers an MCP server. That server may expose MCP tools,
resources, and prompts. The Tank atom is the wiring; the MCP server is the
capability provider.

## Security Considerations for Tool Wiring

When wiring MCP servers via Tank tool atoms, enforce these constraints:

| Risk | Mitigation |
|------|-----------|
| Overly broad network access | Declare exact hostnames in `network.outbound` |
| Secret leakage in config | Use env var references, never inline secrets |
| Tool poisoning (malicious tool descriptions) | Only wire trusted, audited MCP servers |
| Privilege escalation via subprocess | Use `subprocess: true` only for STDIO servers |
| Confused deputy (server accesses resources on behalf of user) | Scope OAuth to minimum required permissions |

See `references/tool-atom-anatomy.md` for how these map to `tank.json` fields.

## Server Discovery and Capability Negotiation

When a host connects to an MCP server, the first exchange is the
`initialize` handshake. Understanding this flow explains what happens
behind the scenes after a Tank tool atom registers a server.

### The Initialize Handshake

```
Client -> Server:  initialize { protocolVersion, capabilities, clientInfo }
Server -> Client:  initialize response { protocolVersion, capabilities, serverInfo }
Client -> Server:  notifications/initialized
```

The client declares its capabilities (e.g., "I support sampling"). The server
declares its capabilities (e.g., "I provide tools and resources"). Both sides
agree on the protocol version. This negotiation happens once per connection.

### Capability Discovery

After initialization, the client queries available primitives:

| Request | Response | Purpose |
|---------|----------|---------|
| `tools/list` | Array of tool definitions | Discover callable functions |
| `resources/list` | Array of resource URIs | Discover available data |
| `prompts/list` | Array of prompt templates | Discover canned interactions |

The host injects discovered tools into the LLM's function-calling schema.
Resource URIs are made available for context attachment. Prompt templates
may appear as slash commands in the host's UI.

### Tool Invocation Flow

When the LLM decides to call a tool:

```
LLM output:     tool_use { name: "create_issue", input: { title: "Bug", body: "..." } }
Host:            routes to the Client connected to the server owning "create_issue"
Client -> Server: tools/call { name: "create_issue", arguments: { title: "Bug", body: "..." } }
Server:          executes logic, returns result
Server -> Client: { content: [{ type: "text", text: "Created issue #42" }] }
Host:            passes result back to LLM as tool_result
```

The host maintains a mapping of tool names to servers. If two servers expose
tools with the same name, the host must disambiguate (typically by prefixing
the server name). This is another reason Tank uses one bundle per server --
name collisions are easier to manage when each bundle is independent.

## Lifecycle: Server Startup and Shutdown

### STDIO Lifecycle

1. Host reads config, finds STDIO server entry
2. Host spawns process: `command args...` with `env` applied
3. Host sends `initialize` over stdin
4. Server responds over stdout
5. Normal operation: JSON-RPC messages over stdin/stdout
6. On shutdown: host sends `notifications/cancelled`, then terminates process

### HTTP Lifecycle

1. Host reads config, finds HTTP server entry
2. Host sends `initialize` as HTTP POST to `url`
3. Server responds with capabilities
4. Normal operation: each tool call is an HTTP POST
5. Server manages its own lifecycle -- host does not stop it
