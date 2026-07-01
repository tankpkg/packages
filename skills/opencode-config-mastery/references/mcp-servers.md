# MCP Server Configuration

Sources: OpenCode source (mcp/index.ts), official docs (opencode.ai/docs/mcp-servers),
opencode-tutorial.com/en/docs/mcp-servers, MCP specification

Covers: local and remote MCP server setup, OAuth configuration, per-agent
scoping, tool management, CLI commands, transport types, config format
differences, context budget management.

## OpenCode's MCP Config Format

**Important**: OpenCode's format differs from the community standard (`mcpServers`).

| Field | OpenCode | Standard (Claude Desktop) |
|-------|----------|---------------------------|
| Root key | `"mcp"` | `"mcpServers"` |
| Command | `"command": ["npx", "-y", "pkg"]` (array) | `"command": "npx"` + `"args": ["-y", "pkg"]` |
| Env vars | `"environment": {}` | `"env": {}` |
| Type | Required: `"type": "local"` or `"remote"` | Inferred |

## Local MCP Servers (STDIO)

Spawns a subprocess communicating via stdin/stdout.

```jsonc
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/home/user"],
      "environment": {
        "MY_API_KEY": "{env:MY_API_KEY}"
      },
      "enabled": true,
      "timeout": 10000
    }
  }
}
```

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `type` | `"local"` | Yes | — | Must be `"local"` |
| `command` | string[] | Yes | — | Command + args as array |
| `environment` | object | No | `{}` | Env vars for the subprocess |
| `enabled` | boolean | No | `true` | Toggle without removing config |
| `timeout` | number | No | `30000` | Tool fetch timeout (ms) |

**Command array**: First element is the executable, rest are arguments:
- `["npx", "-y", "package-name", "arg1"]`
- `["uvx", "python-mcp-server"]`
- `["bun", "x", "my-mcp"]`
- `["docker", "run", "-i", "--rm", "image-name"]`
- `["node", "./my-local-server.js"]`

**CWD**: The subprocess runs with `cwd` set to the project directory.

## Remote MCP Servers (HTTP/SSE)

Connects to an HTTP endpoint. Tries StreamableHTTP first, falls back to SSE.

```jsonc
{
  "mcp": {
    "my-remote": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer {env:MY_API_KEY}"
      },
      "enabled": true,
      "timeout": 5000
    }
  }
}
```

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `type` | `"remote"` | Yes | — | Must be `"remote"` |
| `url` | string | Yes | — | Server endpoint URL |
| `headers` | object | No | `{}` | HTTP headers |
| `enabled` | boolean | No | `true` | Toggle without removing |
| `oauth` | object/false | No | auto | OAuth config (see below) |
| `timeout` | number | No | `30000` | Tool fetch timeout (ms) |

## OAuth Authentication

OpenCode auto-detects OAuth-capable remote servers. Three modes:

### 1. Auto-detected (most common)
```jsonc
{
  "mcp": {
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp",
      "oauth": {}
    }
  }
}
```
Then run: `opencode mcp auth sentry`

### 2. Pre-registered credentials
```jsonc
{
  "mcp": {
    "my-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "clientId": "{env:MCP_CLIENT_ID}",
        "clientSecret": "{env:MCP_CLIENT_SECRET}",
        "scope": "tools:read tools:execute"
      }
    }
  }
}
```

### 3. Disable OAuth (API key auth instead)
```jsonc
{
  "mcp": {
    "my-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "oauth": false,
      "headers": {
        "Authorization": "Bearer {env:MY_API_KEY}"
      }
    }
  }
}
```

**Token storage**: `~/.local/share/opencode/mcp-auth.json`

## Tool Naming Convention

MCP tools are registered as `{serverName}_{toolName}`, with non-alphanumeric
chars replaced by `_`. Example: server named `"gh-search"` with tool
`"search-code"` becomes `gh_search_search_code`.

## Tool Management

### Disable globally
```jsonc
{
  "tools": {
    "my-mcp-server_*": false
  }
}
```

### Disable globally, enable per agent
```jsonc
{
  "mcp": {
    "expensive-mcp": {
      "type": "local",
      "command": ["npx", "-y", "expensive-mcp-server"]
    }
  },
  "tools": {
    "expensive-mcp*": false
  },
  "agent": {
    "specialist": {
      "tools": {
        "expensive-mcp*": true
      }
    }
  }
}
```

### Glob patterns for tool names
- `*` matches zero or more characters
- `?` matches exactly one character
- `"my-mcp*"` matches `my-mcp_search`, `my-mcp_list`, etc.

## CLI Commands

```bash
opencode mcp list                  # List servers and auth status
opencode mcp auth <server-name>    # Trigger OAuth browser flow
opencode mcp auth list             # View all OAuth statuses
opencode mcp logout <server-name>  # Remove stored credentials
opencode mcp debug <server-name>   # Debug connection + OAuth
```

## Overriding Remote/Org Defaults

Organizations serve MCP configs via `.well-known/opencode`. Users opt in:

```jsonc
{
  "mcp": {
    "jira": {
      "type": "remote",
      "url": "https://jira.example.com/mcp",
      "enabled": true
    }
  }
}
```

## Context Budget Management

MCP tool definitions consume context tokens. 50+ tools ≈ 67k tokens just
for definitions.

**Strategies**:
1. **Per-agent scoping**: Disable globally, enable only for relevant agents
2. **Selective enabling**: Only enable servers you actively need
3. **Lazy loading**: Use `opencode-mcp-tool-search` plugin for on-demand loading
4. **Fewer servers**: The GitHub MCP server alone can exceed context limits

## Quick-Start Examples

### Filesystem access
```jsonc
{
  "mcp": {
    "fs": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    }
  }
}
```

### Context7 (live documentation)
```jsonc
{
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

### GitHub code search (Grep by Vercel)
```jsonc
{
  "mcp": {
    "gh_grep": {
      "type": "remote",
      "url": "https://mcp.grep.app"
    }
  }
}
```

### Sentry (OAuth)
```jsonc
{
  "mcp": {
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp",
      "oauth": {}
    }
  }
}
```

### PostgreSQL
```jsonc
{
  "mcp": {
    "postgres": {
      "type": "local",
      // Connection string: see libpq docs. Provide credentials via PGUSER /
      // PGPASSWORD env vars (preferred) rather than embedding them in the URI.
      "command": ["npx", "-y", "@modelcontextprotocol/server-postgres",
                  "postgresql://localhost/mydb"]
    }
  }
}
```

### Playwright (browser automation)
```jsonc
{
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"]
    }
  }
}
```

### Docker-based server
```jsonc
{
  "mcp": {
    "github": {
      "type": "local",
      "command": ["docker", "run", "-i", "--rm",
                  "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                  "ghcr.io/github/github-mcp-server"],
      "environment": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"
      }
    }
  }
}
```
