# Worked Examples: Tool Bundles

Sources: MCP Specification (2025-06-18), Tank AGENTS.md, production MCP server configurations from @modelcontextprotocol packages, Playwright MCP, and community servers

Covers: four complete tool bundle implementations demonstrating local STDIO
wiring, remote HTTP with OAuth, tool with command/env configuration, and a
composite bundle pairing a tool atom with an instruction atom.

## Example 1: Local STDIO Server -- Filesystem

The `@modelcontextprotocol/server-filesystem` server provides file read/write
tools over STDIO. This is the simplest wiring pattern.

### Directory Structure

```
bundles/filesystem/
  tank.json
```

No SKILL.md needed -- filesystem tools are self-explanatory.

### tank.json

```json
{
  "name": "@tank/filesystem",
  "version": "1.0.0",
  "description": "Wire the MCP filesystem server for local file operations. Provides read_file, write_file, list_directory, search_files, and move_file tools. Triggers: filesystem mcp, file tools, local file access, mcp filesystem.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": ["**/*"] },
    "subprocess": true
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "tool",
      "name": "filesystem",
      "extensions": {
        "claude-code": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
          "env": {}
        },
        "opencode": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
          "env": {}
        },
        "cursor": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
          "env": {}
        }
      }
    }
  ]
}
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| No instruction atom | Tools like `read_file` and `write_file` are self-documenting |
| `subprocess: true` | STDIO transport requires spawning the server process |
| `filesystem.write: ["**/*"]` | Server writes files -- permission must reflect this |
| `"."` as final arg | Scopes the server to the current working directory |
| No `network.outbound` | Purely local -- no network access needed |

## Example 2: Remote HTTP Server with OAuth -- GitHub

A hypothetical remote GitHub MCP server hosted at `mcp.github.com` that
requires OAuth to access the GitHub API on behalf of the user.

### Directory Structure

```
bundles/github-remote/
  tank.json
  SKILL.md
```

### tank.json

```json
{
  "name": "@tank/github-remote",
  "version": "1.0.0",
  "description": "Wire the remote GitHub MCP server over HTTP with OAuth. Provides issue, PR, repo, and search tools. Triggers: github mcp remote, github oauth mcp, github tools http.",
  "permissions": {
    "network": {
      "outbound": ["mcp.github.com", "github.com"]
    },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "tool",
      "name": "github-remote",
      "extensions": {
        "claude-code": {
          "url": "https://mcp.github.com/v1/mcp",
          "oauth": {
            "provider": "https://github.com/login/oauth",
            "scopes": ["repo", "read:org", "read:user"],
            "clientId": "Iv1.abc123def456"
          }
        },
        "opencode": {
          "url": "https://mcp.github.com/v1/mcp",
          "oauth": {
            "provider": "https://github.com/login/oauth",
            "scopes": ["repo", "read:org", "read:user"],
            "clientIdEnvVar": "GITHUB_OAUTH_CLIENT_ID"
          }
        },
        "cursor": {
          "url": "https://mcp.github.com/v1/mcp",
          "oauth": {
            "provider": "https://github.com/login/oauth",
            "scopes": ["repo", "read:org", "read:user"],
            "clientId": "Iv1.abc123def456"
          }
        }
      }
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| `subprocess: false` | HTTP transport -- no process to spawn |
| Both `mcp.github.com` and `github.com` in outbound | Server host + OAuth provider host |
| OAuth scopes minimized | Only `repo`, `read:org`, `read:user` -- not `admin` |
| `clientId` inline (public) | OAuth client IDs are not secrets -- safe to include |
| `clientIdEnvVar` variant for OpenCode | Some platforms prefer env var indirection |
| Instruction atom included | GitHub tools have complex workflows (PR creation, issue linking) |

### SKILL.md (excerpt for the instruction atom)

The SKILL.md paired with this tool would document:

- How to authenticate (first-run OAuth flow)
- Priority tools: `create_issue`, `create_pull_request`, `search_repos`
- Workflow: create branch -> commit -> open PR -> link to issue
- Rate limit awareness: 5000 requests/hour for authenticated users
- Required: user must have GitHub account and grant OAuth permissions

## Example 3: STDIO Server with Command and Env Config -- Playwright

The `@playwright/mcp` server provides browser automation tools. It requires
specific environment configuration for headless vs headed mode.

### Directory Structure

```
bundles/playwright/
  tank.json
```

### tank.json

```json
{
  "name": "@tank/playwright",
  "version": "1.0.0",
  "description": "Wire the Playwright MCP server for browser automation. Provides navigation, clicking, typing, screenshot, and PDF generation tools. Triggers: playwright mcp, browser automation, browser tools, web scraping mcp.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": ["./screenshots/**", "./pdfs/**"] },
    "subprocess": true
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "tool",
      "name": "playwright",
      "extensions": {
        "claude-code": {
          "command": "npx",
          "args": ["-y", "@playwright/mcp", "--headless"],
          "env": {
            "PLAYWRIGHT_BROWSERS_PATH": "${PLAYWRIGHT_BROWSERS_PATH:-0}"
          }
        },
        "opencode": {
          "command": "npx",
          "args": ["-y", "@playwright/mcp", "--headless"],
          "env": {
            "PLAYWRIGHT_BROWSERS_PATH": "${PLAYWRIGHT_BROWSERS_PATH:-0}"
          }
        },
        "cursor": {
          "command": "npx",
          "args": ["-y", "@playwright/mcp"],
          "env": {
            "PLAYWRIGHT_BROWSERS_PATH": "${PLAYWRIGHT_BROWSERS_PATH:-0}"
          }
        }
      }
    }
  ]
}
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| `--headless` flag for Claude Code and OpenCode | These run in terminal -- no GUI available |
| No `--headless` for Cursor | IDE context may support headed browser |
| `PLAYWRIGHT_BROWSERS_PATH` env var | Allows custom browser location; `0` default uses bundled |
| `filesystem.write` scoped to output dirs | Screenshots and PDFs need write access |
| No instruction atom | Playwright tools are well-named (`browser_navigate`, `browser_click`) |
| No `network.outbound` | Server runs locally; browser fetches are user-directed |

### Platform-Specific Variations

This example demonstrates a key pattern: extension bags can differ across
platforms beyond just the key name. Claude Code and OpenCode get `--headless`
because they run headless. Cursor omits it because the IDE provides a window
context. The tool atom handles this cleanly through per-platform bags.

## Example 4: Composite Bundle -- Fetch with Usage Guidance

The `@modelcontextprotocol/server-fetch` server wraps HTTP requests. Pairing
it with an instruction atom prevents common misuse (agents fetching
excessively, hitting rate limits, or leaking internal URLs).

### Directory Structure

```
bundles/fetch/
  tank.json
  SKILL.md
```

### tank.json

```json
{
  "name": "@tank/fetch",
  "version": "1.0.0",
  "description": "Wire the MCP fetch server with usage guidance for safe HTTP requests. Provides fetch tool for GET/POST with rate awareness. Triggers: fetch mcp, http tools, web request mcp, api fetch tool.",
  "permissions": {
    "network": {
      "outbound": ["*"]
    },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": true
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "tool",
      "name": "fetch",
      "extensions": {
        "claude-code": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-fetch"],
          "env": {}
        },
        "opencode": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-fetch"],
          "env": {}
        },
        "cursor": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-fetch"],
          "env": {}
        }
      }
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### SKILL.md

```markdown
---
name: "@tank/fetch"
description: |
  Usage guidance for the MCP fetch tool. Prevents excessive requests,
  URL leakage, and rate limit violations.

  Trigger phrases: "fetch tool", "http request", "web fetch", "api call"
---

# Fetch Tool Usage

## Rules

1. Prefer project-local data over fetching external URLs
2. Cache responses mentally -- do not re-fetch the same URL in one session
3. Never fetch internal/private network URLs (10.x, 192.168.x, localhost)
4. Respect rate limits: max 3 requests per minute to any single domain
5. Use GET for reading, POST only when the user explicitly requests mutation
6. Always tell the user what URL you are about to fetch before calling

## Tool Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `fetch` | HTTP GET/POST to a URL | User asks for web content, API data, or documentation |

## Common Patterns

- Fetching documentation: `fetch` with URL, then summarize
- API exploration: `fetch` the endpoint, parse the response JSON
- Web scraping: `fetch` the page, extract relevant text
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| `network.outbound: ["*"]` | Fetch tool can reach any URL -- wildcard is honest |
| Instruction atom with rules | Prevents agent from making unbounded requests |
| Rate limit guidance | Protects both the user and target servers |
| Internal URL prohibition | Prevents SSRF-like behavior from agent |
| Short SKILL.md (~30 lines) | Guidance for a single-tool server stays minimal |

## Pattern Summary

| Example | Transport | Atoms | Permissions Key | Complexity |
|---------|-----------|-------|-----------------|-----------|
| Filesystem | STDIO | 1 tool | subprocess | Minimal |
| GitHub Remote | HTTP | 1 tool + 1 instruction | network.outbound | OAuth |
| Playwright | STDIO | 1 tool | subprocess + filesystem.write | Platform-variant args |
| Fetch | STDIO | 1 tool + 1 instruction | subprocess + network wildcard | Usage guardrails |

## Scaffolding Checklist

When creating a new tool bundle from scratch:

1. Identify the upstream MCP server package name and version
2. Determine transport: check if the server uses STDIO or HTTP
3. Create `bundles/{name}/tank.json`
4. Add the tool atom with `kind: "tool"` and `name`
5. Add extension bags for at least Claude Code and OpenCode
6. Set `subprocess: true` for STDIO or `network.outbound` for HTTP
7. Decide if an instruction atom adds value (see decision table above)
8. If yes, create `SKILL.md` with usage guidance
9. Run `tank publish --dry-run` to validate
10. Test by installing the bundle and verifying the MCP server connects

See `references/tool-atom-anatomy.md` for the complete schema reference.
See `references/mcp-primer.md` for transport and authentication details.
