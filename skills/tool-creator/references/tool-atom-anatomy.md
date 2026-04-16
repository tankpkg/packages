# Tool Atom Anatomy

Sources: Tank AGENTS.md atom system, MCP Specification (2025-06-18), production MCP configuration patterns from Claude Code, OpenCode, and Cursor

Covers: the Tank `kind: "tool"` atom schema, required and optional fields,
extension bags for cross-platform wiring, permission scoping in tank.json,
composing tool atoms with instruction atoms, and the full manifest structure
for tool bundles.

## The Tool Atom Schema

A tool atom is the simplest multi-atom primitive. It has one required field:

```json
{
  "kind": "tool",
  "name": "github"
}
```

That is a valid tool atom. The `name` field identifies the MCP server being
wired. Convention: use the server's well-known name (e.g., `github`,
`filesystem`, `fetch`, `playwright`, `postgres`).

### Required Fields

| Field | Type | Purpose |
|-------|------|---------|
| `kind` | `"tool"` | Identifies this atom as a tool registration |
| `name` | string | The MCP server identity. Used by adapters to generate config entries |

### Optional Fields

Any additional fields beyond `kind` and `name` are either:
- Standard atom fields (`extensions`)
- Extension-bag territory (platform-specific config)

The tool atom itself is deliberately minimal. Platform-specific details
(command paths, URLs, environment variables, OAuth metadata) belong in
extension bags.

## Extension Bags: Platform-Specific Wiring

Extension bags carry the configuration each platform needs to connect to the
MCP server. Tank adapters read their platform key and ignore others.

```json
{
  "kind": "tool",
  "name": "github",
  "extensions": {
    "claude-code": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "opencode": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "cursor": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

### Extension Bag Fields by Transport

#### STDIO Transport

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `command` | string | Yes | Executable to spawn (e.g., `npx`, `uvx`, `node`, `python`) |
| `args` | string[] | No | Arguments passed to the command |
| `env` | object | No | Environment variables. Use `${VAR}` for secret references |
| `cwd` | string | No | Working directory for the spawned process |

#### HTTP Transport

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `url` | string | Yes | The MCP server endpoint URL |
| `headers` | object | No | Static headers (e.g., API keys) |
| `oauth` | object | No | OAuth metadata (provider URL, scopes, client ID) |

#### OAuth Metadata (nested under HTTP extensions)

| Field | Type | Purpose |
|-------|------|---------|
| `provider` | string | OAuth authorization server URL |
| `scopes` | string[] | Requested permission scopes |
| `clientId` | string | Public client identifier |
| `clientIdEnvVar` | string | Env var containing client ID (alternative to inline) |

### Platform Key Reference

| Platform | Key | Notes |
|----------|-----|-------|
| Claude Code (claude) | `claude-code` | Writes to `~/.claude/mcp_servers.json` or project `.mcp.json` |
| OpenCode | `opencode` | Writes to `opencode.json` mcpServers section |
| Cursor | `cursor` | Writes to `.cursor/mcp.json` |
| Windsurf | `windsurf` | Writes to `~/.windsurf/mcp_servers.json` |
| Generic fallback | `default` | Used when no platform-specific key matches |

When multiple platforms share identical config (common for STDIO), repeat
the block under each key rather than relying on `default`. Explicit is
better -- adapters may add platform-specific fields in the future.

## Permission Scoping in tank.json

The `permissions` field in `tank.json` controls what the bundle is allowed to
do at the system level. Tool atoms have specific permission requirements
based on transport.

### STDIO Server Permissions

```json
{
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": true
  }
}
```

`subprocess: true` is required because the host spawns the MCP server as a
child process. Without it, the adapter cannot start the server.

If the MCP server itself accesses the filesystem, add the relevant paths:

```json
{
  "permissions": {
    "filesystem": {
      "read": ["**/*"],
      "write": ["./output/**"]
    },
    "subprocess": true
  }
}
```

### HTTP Server Permissions

```json
{
  "permissions": {
    "network": {
      "outbound": ["api.github.com", "github.com"]
    },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  }
}
```

List every hostname the tool communicates with. Include both the MCP server
host and any OAuth provider hosts.

### Permission Decision Table

| Transport | subprocess | network.outbound | filesystem.write |
|-----------|-----------|-------------------|-----------------|
| STDIO, no file writes | `true` | `[]` | `[]` |
| STDIO, writes files | `true` | `[]` | specific paths |
| STDIO, calls APIs | `true` | API hostnames | `[]` |
| HTTP, no OAuth | `false` | server hostname | `[]` |
| HTTP, with OAuth | `false` | server + auth hostnames | `[]` |

## Composing Tool + Instruction Atoms

A tool atom alone registers machinery. An instruction atom adds context.
Combine them in the `atoms` array for bundles where the agent needs guidance.

### When to Add an Instruction Atom

| Scenario | Instruction Needed? |
|----------|-------------------|
| Tools are self-explanatory (filesystem read/write) | No |
| Tools require specific workflows (GitHub PR flow) | Yes |
| Tools have non-obvious limitations | Yes |
| Tools interact with other tools in the bundle | Yes |
| Server exposes 10+ tools | Yes (guide prioritization) |

### Structure of a Composed Bundle

```json
{
  "atoms": [
    {
      "kind": "tool",
      "name": "github",
      "extensions": { ... }
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

The instruction atom's `content` field points to a SKILL.md file that
describes when and how to use the wired tools. This file follows standard
Tank SKILL.md conventions (frontmatter + body under 200 lines).

### Instruction Content Guidelines for Tool Bundles

The SKILL.md paired with a tool atom should cover:

1. What the MCP server does (one paragraph)
2. Which tools are most important (prioritized list)
3. Common workflows combining multiple tools
4. Gotchas, rate limits, or authentication prerequisites
5. Environment variables the user must set

Keep it under 100 lines for simple servers, up to 200 for complex ones.

## Full Manifest Structure

A complete `tank.json` for a tool bundle:

```json
{
  "name": "@tank/{server-name}",
  "version": "1.0.0",
  "description": "Wire the {server-name} MCP server for {purpose}. Triggers: ...",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": true
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "tool",
      "name": "{server-name}",
      "extensions": {
        "claude-code": { "command": "...", "args": [...], "env": {...} },
        "opencode": { "command": "...", "args": [...], "env": {...} },
        "cursor": { "command": "...", "args": [...], "env": {...} }
      }
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Directory | `bundles/{server-name}/` | `bundles/github/` |
| Package name | `@tank/{server-name}` | `@tank/github` |
| Tool atom name | `{server-name}` (no prefix) | `github` |
| Instruction file | `SKILL.md` | Always |

### Versioning

- Start at `1.0.0` for new bundles
- Bump minor when adding platform support or updating extension configs
- Bump major when changing the MCP server package (breaking upstream change)
- The bundle version is independent of the upstream MCP server version

## Validation Checklist

Before publishing a tool bundle, verify:

- [ ] `name` in tank.json matches `@tank/{directory-name}`
- [ ] Tool atom `name` matches the MCP server identity
- [ ] Extension bags exist for at least two platforms
- [ ] `subprocess: true` if transport is STDIO
- [ ] `network.outbound` lists all remote hostnames if transport is HTTP
- [ ] No secrets inline -- all credentials use `${ENV_VAR}` references
- [ ] Instruction atom present if tools require usage guidance
- [ ] `tank publish --dry-run` passes without errors

See `references/worked-examples.md` for complete bundle implementations.
