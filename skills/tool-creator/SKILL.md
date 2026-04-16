---
name: "@tank/tool-creator"
description: |
  Author Tank tool atoms that wire MCP (Model Context Protocol) servers into
  agent harnesses. Covers the tool atom schema (name, extensions, permissions),
  STDIO vs HTTP transport wiring, OAuth configuration for remote servers,
  permission scoping (network.outbound), extension bags for cross-platform
  support (Claude Code, OpenCode, Cursor), and composing tool atoms with
  instruction atoms for usage guidance. Does NOT reimplement MCP servers --
  teaches how to declare thin wiring layers that register upstream servers.
  Synthesizes MCP Specification (2025-06-18), Tank AGENTS.md atom system,
  and production MCP server configuration patterns.

  Trigger phrases: "create mcp tool", "wire mcp server", "tank tool atom",
  "mcp wiring bundle", "register mcp server", "tool atom", "add mcp to tank",
  "mcp tool bundle", "create tool bundle", "mcp config as tank package",
  "wire tool into agent", "tank mcp integration", "tool atom schema",
  "mcp server wiring", "convert mcp config to tank"
---

# Tool Creator

## Core Philosophy

1. **Thin wiring, not reimplementation** -- A tool atom declares "register
   this MCP server." It never contains server code. The upstream server is
   the source of truth; the atom is a pointer.
2. **Extension bags carry platform details** -- The `kind: "tool"` atom has
   one required field: `name`. Everything else (command, args, env, url,
   oauth) lives in `extensions` keyed by platform. This keeps the atom
   portable while letting each harness get exactly what it needs.
3. **Permission scoping protects the user** -- A tool bundle that calls a
   remote server MUST declare `network.outbound` with the exact hostnames.
   A local STDIO server needs `subprocess: true`. State this in `tank.json`
   permissions, not buried in extension bags.
4. **Compose instruction + tool** -- A bare tool atom registers machinery.
   Pair it with an instruction atom that explains WHEN and WHY to use the
   tool. Agents perform better when they understand intent, not just API.
5. **One bundle per server** -- Each MCP server gets its own Tank bundle.
   Do not bundle unrelated servers together. Users install what they need.

## Quick-Start: Common Problems

### "I have an MCP server config and want to package it as a Tank bundle"

1. Identify the transport: STDIO (local binary/script) or HTTP (remote URL)
2. Create `bundles/{server-name}/tank.json` with a tool atom
3. Add extension bags for each target platform
4. Set permissions: `subprocess: true` for STDIO, `network.outbound` for HTTP
5. Optionally add an instruction atom with usage guidance
   -> See `references/tool-atom-anatomy.md`

### "I need to wire a remote MCP server that requires OAuth"

1. Declare the tool atom with `name` matching the server identity
2. Add `extensions` with the OAuth metadata (provider URL, scopes, client ID)
3. Set `network.outbound` to the server hostname AND the OAuth provider
4. Document required env vars for credentials in the instruction atom
   -> See `references/worked-examples.md` (remote HTTP + OAuth example)

### "How is a tool atom different from an MCP server?"

1. An MCP server is running code that exposes tools/resources/prompts
2. A tool atom is a Tank manifest entry that tells the agent harness:
   "connect to this MCP server and make its tools available"
3. The tool atom is to an MCP server what a `docker-compose.yml` service
   entry is to a Docker image -- declaration, not implementation
   -> See `references/mcp-primer.md`

### "My tool atom works in OpenCode but not in Claude Code"

1. Each platform reads different extension bag keys
2. Verify extension bags exist for all target platforms
3. Check that env var names match platform conventions
4. Use `references/tool-atom-anatomy.md` extension bag reference table

## Decision Trees

### Transport Selection

| Signal | Transport | Permission Needed |
|--------|-----------|-------------------|
| Server runs as local binary/script | STDIO | `subprocess: true` |
| Server is a remote URL | HTTP | `network.outbound: ["hostname"]` |
| Server needs authentication | HTTP + OAuth | `network.outbound: ["hostname", "auth-provider"]` |
| Server needs local files | STDIO | `subprocess: true`, `filesystem.read` |

### Bundle Complexity

| Scenario | Atoms Needed |
|----------|-------------|
| Simple STDIO server, self-explanatory | 1 tool atom |
| STDIO server with non-obvious usage | 1 tool + 1 instruction |
| Remote server with OAuth + usage guide | 1 tool + 1 instruction |
| Server with custom pre-use validation | 1 tool + 1 instruction + 1 hook |

### Extension Bag Platform Keys

| Platform | Extension Key | Transport Config Fields |
|----------|--------------|------------------------|
| Claude Code | `claude-code` | `command`, `args`, `env` (STDIO); `url` (HTTP) |
| OpenCode | `opencode` | `command`, `args`, `env` (STDIO); `url`, `headers` (HTTP) |
| Cursor | `cursor` | `command`, `args`, `env` (STDIO); `url` (HTTP) |
| Windsurf | `windsurf` | `command`, `args`, `env` (STDIO) |
| Generic | `default` | Fallback for unrecognized platforms |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Bundling server source code | Bundle becomes stale, hard to update | Point to upstream package via `command`/`url` |
| No instruction atom | Agent sees tools but lacks usage context | Add instruction explaining when/why |
| Wildcard network permissions | Security risk | List exact hostnames in `network.outbound` |
| Hardcoded credentials in extensions | Secret leakage | Use env var references (`${ENV_VAR}`) |
| Multiple servers in one bundle | Violates single-responsibility | One bundle per MCP server |

## Reference Index

| File | Contents |
|------|----------|
| `references/mcp-primer.md` | MCP architecture, host/client/server model, STDIO vs HTTP transports, OAuth flow, tool vs resource vs prompt primitives, how agents discover and invoke MCP tools |
| `references/tool-atom-anatomy.md` | Tank tool atom schema, required and optional fields, extension bags per platform, permission scoping, composing tool + instruction atoms, tank.json manifest patterns |
| `references/worked-examples.md` | Four complete tool bundle examples: local STDIO wrap, remote HTTP with OAuth, tool with command/env config, tool + instruction composite bundle |
