# Plugins & MCP Ecosystem

Sources: OpenCode source (plugin.ts, hook.ts), official docs
(opencode.ai/docs/plugins), npm registry, MCP specification,
modelcontextprotocol.io, PulseMCP, Smithery, OWASP MCP Top 10

Covers: OpenCode plugin system (distinct from MCP), trusted plugins catalog,
MCP server directories and registries, community MCP servers by category,
security considerations, context budget strategies.

## OpenCode Plugins vs MCP Servers

These are two different extension systems — do not confuse them.

| Aspect | OpenCode Plugin | MCP Server |
|--------|----------------|------------|
| What it is | npm package with hooks | External tool server |
| Config key | `"plugin"` | `"mcp"` |
| Runs where | Inside OpenCode process | Subprocess or remote URL |
| Can do | Add agents, hooks, commands, tools | Expose tools via protocol |
| Install | `"plugin": ["package-name"]` | Config in `"mcp"` section |
| Auth | npm install | Per-server (API key, OAuth) |

## Plugin Configuration

```jsonc
{
  "plugin": [
    "oh-my-opencode",                    // npm package name
    "opencode-morph-fast-apply",         // Another npm package
    "@scope/my-plugin",                  // Scoped package
    "file://./my-local-plugin"           // Local development
  ]
}
```

Plugins are npm packages installed in the project. They run inside OpenCode's
process and can hook into the agent lifecycle.

### Plugin API Surface

Plugins can:
- Register custom agents (with prompts, tools, permissions)
- Add slash commands (`/command`)
- Add hooks (pre-message, after-message, pre-tool, after-tool, session start/end)
- Inject tools (functions callable by agents)
- Modify agent behavior via middleware

### Plugin Development

```typescript
// Minimal plugin structure
import { definePlugin } from "opencode/plugin"

export default definePlugin({
  name: "my-plugin",
  setup(app) {
    // Add an agent
    app.agent("my-agent", {
      description: "...",
      prompt: "...",
      mode: "subagent",
    })
    // Add a hook
    app.hook("message.pre", async (ctx) => {
      // Modify message before sending
    })
    // Add a command
    app.command("/mycommand", {
      description: "...",
      handler: async (ctx) => { ... }
    })
  }
})
```

## Trusted OpenCode Plugins

### oh-my-opencode (omo)

The most popular OpenCode plugin. Adds opinionated agent orchestration:
Sisyphus (primary), Oracle (reasoning), Explorer, Librarian, and more.
Includes skill injection, delegation system, and category-based routing.

```jsonc
{ "plugin": ["oh-my-opencode"] }
```

- **What it adds**: 10+ agents, todo system, skill loading, delegation
- **Config**: `oh-my-opencode.json` in project root for overrides
- **Relation to agent-creator skill**: See `opencode-agent-creator` skill for
  creating custom agents within the omo framework

### opencode-morph-fast-apply

Speeds up file edits by using a specialized diff-apply model (Morph)
instead of the main LLM for applying code changes. Reduces latency and cost.

```jsonc
{ "plugin": ["opencode-morph-fast-apply"] }
```

### opencode-wakatime

Tracks coding time in OpenCode sessions via WakaTime. Sends heartbeats
for each agent interaction.

```jsonc
{ "plugin": ["opencode-wakatime"] }
```

### opencode-helicone-session

Routes LLM calls through Helicone proxy for observability, logging,
cost tracking, and caching. Adds session-level tracking.

```jsonc
{ "plugin": ["opencode-helicone-session"] }
```

### opencode-vibeguard

Adds safety rails to agent behavior — prevents destructive actions,
enforces review of generated code, adds guardrails for sensitive operations.

```jsonc
{ "plugin": ["opencode-vibeguard"] }
```

### opencode-supermemory

Persistent memory across sessions. Stores context, decisions, and
preferences so agents remember past conversations.

```jsonc
{ "plugin": ["opencode-supermemory"] }
```

### opencode-mcp-tool-search

Lazy-loads MCP tools on demand instead of registering all tools upfront.
Critical for managing context budget when you have many MCP servers.

```jsonc
{ "plugin": ["opencode-mcp-tool-search"] }
```

## MCP Server Registries & Directories

### Official Registry
**registry.modelcontextprotocol.io** — Curated by Anthropic/MCP team.
Verified servers with quality standards. Best first stop.

### PulseMCP
**pulsemcp.com** — 8,600+ community-submitted MCP servers. Largest directory.
Includes reviews and categories. Good for discovery, but verify quality.

### Smithery
**smithery.ai** — 3,700+ servers. Provides hosted MCP instances (no local
install needed). Can proxy servers for easier setup.

### mcp.so
Community directory with searchable categories and installation instructions.

### GitHub Awesome Lists
- `punkpeye/awesome-mcp-servers` (32k+ stars) — Curated list
- `modelcontextprotocol/servers` — Official reference implementations

## Community MCP Servers by Category

### Developer Tools
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| GitHub | `ghcr.io/github/github-mcp-server` | Issues, PRs, code search, repos |
| Playwright | `@playwright/mcp@latest` | Browser automation, testing |
| Sentry | `https://mcp.sentry.dev/mcp` | Error monitoring, issue triage |
| Linear | `https://mcp.linear.app/sse` | Issue tracking, project mgmt |
| Grafana | `https://mcp.grafana.com/sse` | Dashboards, alerting, logs |

### Data & Knowledge
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| Context7 | `https://mcp.context7.com/mcp` | Live library documentation |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Database queries |
| SQLite | `@modelcontextprotocol/server-sqlite` | Local database |
| Redis | `@modelcontextprotocol/server-redis` | Cache, key-value store |
| Qdrant | `@qdrant/mcp-server-qdrant` | Vector search |

### Productivity & Communication
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| Slack | `@anthropics/mcp-server-slack` | Messages, channels, search |
| Google Drive | `@anthropics/mcp-server-gdrive` | Docs, sheets, files |
| Notion | `@notionhq/notion-mcp-server` | Pages, databases, search |
| Todoist | `@anthropics/mcp-server-todoist` | Task management |
| Gmail | `@anthropics/mcp-server-gmail` | Email read/send |

### Cloud & Infrastructure
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| AWS | `@aws/mcp` | S3, Lambda, CloudWatch, etc. |
| Cloudflare | `@cloudflare/mcp-server-cloudflare` | Workers, KV, R2 |
| Terraform | `hashicorp/terraform-mcp-server` | IaC planning and apply |
| Kubernetes | `@modelcontextprotocol/server-k8s` | Cluster management |

### Files & System
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | Read/write files |
| Git | `@modelcontextprotocol/server-git` | Repository operations |
| Memory | `@modelcontextprotocol/server-memory` | Persistent key-value |
| Fetch | `@modelcontextprotocol/server-fetch` | HTTP requests |

### AI & Search
| Server | Package/URL | What It Does |
|--------|-------------|--------------|
| Exa | `exa-mcp-server` | Web search, content retrieval |
| Brave Search | `@anthropics/mcp-server-brave-search` | Web search |
| Grep.app | `https://mcp.grep.app` | GitHub code search |
| Sequential Thinking | `@modelcontextprotocol/server-sequential-thinking` | Chain-of-thought |

## Security Considerations

### The Threat Landscape

Research shows **43% of analyzed MCP servers** are vulnerable to command
injection attacks. The MCP ecosystem is young and many servers are not
security-audited.

### OWASP MCP Top 10 Threats

1. **Tool Poisoning** — Malicious tool descriptions that manipulate agent
   behavior. #1 threat. A tool's description can instruct the agent to
   exfiltrate data or execute unintended actions.
2. **Excessive Permissions** — MCP servers requesting broader access than needed.
3. **MCP Rug Pulls** — Server behavior changing after initial trust is granted.
4. **Server Spoofing** — Fake servers impersonating legitimate services.
5. **Command Injection** — Unsanitized inputs passed to shell commands.
6. **Data Exfiltration** — Tools leaking sensitive data to external endpoints.
7. **Insecure Credentials** — API keys in plain text configs or logs.
8. **Token Theft** — OAuth tokens intercepted or stored insecurely.
9. **Excessive Tool Calls** — Runaway tool loops consuming resources/money.
10. **Lack of Audit Trail** — No logging of what tools did with what data.

### Security Best Practices

**Before adding any MCP server:**

1. **Check the source** — Is it from a known vendor (GitHub, Sentry, etc.)?
   Official vendor servers are generally safe. Community servers need review.

2. **Review permissions** — What can the server access? Filesystem servers
   should be scoped to specific directories:
   ```jsonc
   // GOOD: scoped
   "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
   // BAD: full access
   "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/"]
   ```

3. **Use environment variables** — Never hardcode API keys:
   ```jsonc
   // GOOD
   "environment": { "API_KEY": "{env:MY_API_KEY}" }
   // BAD
   "environment": { "API_KEY": "sk-live-abc123..." }
   ```

4. **Disable unused servers** — Don't leave servers enabled "just in case":
   ```jsonc
   "mcp": {
     "unused-server": { "enabled": false }
   }
   ```

5. **Use permission restrictions** — Limit what agents can do with MCP tools:
   ```jsonc
   "permission": {
     "mcp_server_dangerous_tool": "deny"
   }
   ```

6. **Prefer remote OAuth** over local API keys for enterprise servers.
   OAuth tokens auto-refresh and can be revoked centrally.

7. **Pin versions** — Don't use `@latest` in production:
   ```jsonc
   // GOOD
   "command": ["npx", "-y", "@playwright/mcp@1.2.3"]
   // RISKY
   "command": ["npx", "-y", "@playwright/mcp@latest"]
   ```

### Red Flags

| Signal | Risk |
|--------|------|
| No GitHub repo linked | Can't audit source code |
| Very few stars/downloads | Unvetted by community |
| Requests filesystem root access | Over-permissioned |
| No clear author/organization | Accountability unclear |
| Frequent `npx` with `@latest` | Supply chain risk |
| Server asks for credentials in tool descriptions | Social engineering |

## Context Budget Management

Each MCP server's tools consume context window tokens. Tool definitions
(names, descriptions, parameter schemas) are sent with every request.

### Token Cost Estimates

| Server | Approx. Tools | Approx. Tokens |
|--------|---------------|----------------|
| GitHub MCP | 30+ | ~15,000 |
| Playwright | 15+ | ~8,000 |
| Filesystem | 10 | ~3,000 |
| Context7 | 3 | ~1,500 |
| Sequential Thinking | 1 | ~500 |

### Budget Strategies

1. **Per-agent scoping** (best): Disable globally, enable per agent
   ```jsonc
   {
     "tools": { "github_*": false },
     "agent": {
       "pr-reviewer": { "tools": { "github_*": true } }
     }
   }
   ```

2. **Lazy loading**: Use `opencode-mcp-tool-search` plugin to load tools
   on demand rather than all at once.

3. **Server consolidation**: Use one multi-purpose server instead of many
   single-purpose ones where possible.

4. **Selective enabling**: Only enable servers for the current task:
   ```jsonc
   {
     "mcp": {
       "rarely-used": { "enabled": false }
     }
   }
   ```

## Plugin Decision Tree

| Need | Solution |
|------|----------|
| Agent orchestration + skills | `oh-my-opencode` |
| Faster file edits | `opencode-morph-fast-apply` |
| Time tracking | `opencode-wakatime` |
| LLM observability | `opencode-helicone-session` |
| Safety guardrails | `opencode-vibeguard` |
| Cross-session memory | `opencode-supermemory` |
| Too many MCP tools | `opencode-mcp-tool-search` |
| Live library docs | Context7 MCP (remote) |
| Browser automation | Playwright MCP (local) |
| Code search across GitHub | Grep.app MCP (remote) |
| Error monitoring | Sentry MCP (remote, OAuth) |
| Database access | PostgreSQL/SQLite MCP (local) |
