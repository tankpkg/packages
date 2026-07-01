# Resource Design Patterns

Sources: Tank specification (AGENTS.md), MCP specification (2025-2026),
information architecture patterns

Covers: when to use a resource vs an instruction atom, URI naming conventions,
static vs dynamic resources, composing resources with agents, and permission
implications for each URI scheme.

## The Resource Selection Framework

Every piece of context in a Tank bundle must be delivered through an atom.
The first design decision is always: **instruction or resource?**

### The Three Questions

Ask these in order. Stop at the first "yes."

1. **Is this behavioral context (rules, tone, persona)?**
   Yes -> Instruction atom. Agents need behavioral context on every turn.

2. **Is this small (<50 lines) and always relevant?**
   Yes -> Instruction atom. The context cost is negligible.

3. **Is this data, reference material, or situational context?**
   Yes -> Resource atom. Pull it when needed, save tokens otherwise.

### Decision Matrix

| Content Type                  | Size    | Frequency Needed | Atom Type     |
| ----------------------------- | ------- | ---------------- | ------------- |
| Persona / role definition     | Small   | Every turn       | Instruction   |
| Coding standards / rules      | Small   | Every turn       | Instruction   |
| API schema reference          | Large   | Some tasks       | Resource      |
| Project architecture map      | Medium  | Some tasks       | Resource      |
| Style guide                   | Medium  | Some tasks       | Resource      |
| Environment configuration     | Small   | Some tasks       | Resource      |
| Database schema documentation | Large   | Rare tasks       | Resource      |
| Third-party API specs         | Large   | Rare tasks       | Resource      |
| Error code catalog            | Medium  | Debugging only   | Resource      |
| Deployment runbook            | Large   | Deployment only  | Resource      |

### Edge Cases

**Small but situational content (10-30 lines, not always needed):**
Use a resource. Even though the content is small, injecting it into every
prompt wastes tokens across hundreds of turns. A 20-line resource read
once costs 20 tokens. A 20-line instruction costs 20 tokens per turn --
over 100 turns, that is 2000 tokens wasted.

**Large but always-needed content (>100 lines, every task):**
Split it. Extract the always-needed core (rules, constraints) into an
instruction atom (<50 lines). Put the full reference material into a
resource atom. The instruction tells the agent the resource exists.

**Behavioral context that varies by task:**
Use a resource with a descriptive `description` field. The agent reads the
behavioral context only when the task matches. This is the one case where
behavioral content belongs in a resource.

## URI Naming Conventions

### Namespace Structure

Organize URIs with logical path segments that group related resources:

```
tank://context/{resource-name}      -- Project-level context
tank://schemas/{schema-name}        -- Data schemas and API specs
tank://guides/{guide-name}          -- Style guides, runbooks, standards
tank://data/{dataset-name}          -- Static data sets
tank://config/{config-name}         -- Configuration data
```

### Naming Rules

| Rule                         | Good                           | Bad                              |
| ---------------------------- | ------------------------------ | -------------------------------- |
| Lowercase with hyphens       | `tank://guides/code-style`     | `tank://Guides/CodeStyle`        |
| Descriptive leaf names       | `tank://context/module-map`    | `tank://context/data`            |
| No file extensions           | `tank://schemas/user-api`      | `tank://schemas/user-api.json`   |
| Logical grouping             | `tank://guides/commit-format`  | `tank://commit-format`           |
| Version suffix when needed   | `tank://schemas/api-v2`        | `tank://schemas/api-new`         |
| Unique within the bundle     | (enforce at validation time)   | Duplicate URIs cause collisions  |

### URI Length

Keep URIs under 80 characters. If the path exceeds this, the naming
is too granular -- consolidate or restructure.

## Static vs Dynamic Resources

### Static Resources

Content is fixed at package publish time. The adapter reads a bundled file.

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "name": "project-architecture"
}
```

Characteristics:
- Deterministic -- same content on every read.
- No external dependencies -- works offline.
- Versioned with the package -- changes require a new publish.
- No permission implications beyond `filesystem.read`.

Best for: architecture maps, style guides, schema references, error
catalogs, coding standards.

### Dynamic Resources (file://)

Content is read from the local filesystem at runtime. The actual content
depends on the state of the filesystem when the agent reads it.

```json
{
  "kind": "resource",
  "uri": "file://./generated/api-schema.json",
  "name": "api-schema"
}
```

Characteristics:
- Content may change between reads.
- Depends on the file existing at the expected path.
- Useful for generated artifacts, build output, or project-specific files.
- Requires `filesystem.read` permission covering the path.

Best for: generated schemas, build artifacts, project-specific configs
that live outside the package.

### Dynamic Resources (mcp://)

Content is fetched from an MCP server at runtime. The server may compute
the response dynamically.

```json
{
  "kind": "resource",
  "uri": "mcp://database-server/schema/users",
  "name": "users-schema"
}
```

Characteristics:
- Content is computed or fetched on demand.
- Requires a configured and running MCP server.
- May involve network latency.
- Requires `network.outbound` if the MCP server is remote.

Best for: live database schemas, API specs from running services,
real-time configuration.

### Dynamic Resources (https://)

Content is fetched from an HTTP endpoint at runtime.

```json
{
  "kind": "resource",
  "uri": "https://api.internal.example.com/v1/feature-flags",
  "name": "feature-flags"
}
```

Characteristics:
- Content depends on the remote server state.
- Requires network access.
- May be slow or unavailable.
- Requires `network.outbound` with the hostname.

Best for: feature flags, remote configuration, external API specs that
change frequently.

### Selection Guide

| Factor                     | Static (`tank://`) | File (`file://`) | MCP (`mcp://`)  | HTTP (`https://`) |
| -------------------------- | ------------------ | ---------------- | --------------- | ----------------- |
| Offline support            | Yes                | Yes              | Depends         | No                |
| Deterministic content      | Yes                | No               | No              | No                |
| Versioned with package     | Yes                | No               | No              | No                |
| External dependency        | None               | Filesystem       | MCP server      | HTTP endpoint     |
| Permission requirement     | None               | `fs.read`        | `network` maybe | `network`         |
| Latency                    | Zero               | Low              | Variable        | Variable          |

## Composing Resources with Agents

The most powerful pattern in Tank bundles is the **agent + resource combo**.
An agent atom declares what it does; a resource atom provides the data it
needs to do it well.

### Composition Pattern

```json
{
  "atoms": [
    {
      "kind": "resource",
      "uri": "tank://guides/code-style",
      "name": "code-style-guide",
      "description": "TypeScript coding standards for this project"
    },
    {
      "kind": "agent",
      "name": "style-reviewer",
      "role": "Review code against the project style guide. Read the code-style-guide resource first, then check each file for violations.",
      "tools": ["read", "grep"],
      "readonly": true
    }
  ]
}
```

The agent's `role` field references the resource by name. The adapter makes
the resource available to the agent through its configured read mechanism.

### Design Rules for Agent+Resource Combos

| Rule                                         | Rationale                                    |
| -------------------------------------------- | -------------------------------------------- |
| Name every resource in a combo               | Agent needs a stable reference               |
| Describe the resource in the agent's `role`  | Agent knows to read it before acting         |
| Give the agent `read` tool access            | Required to fetch resource content           |
| One resource per concern                     | Keeps resources focused and reusable         |
| Keep the resource under 500 lines            | Larger resources degrade agent performance   |

### Multiple Resources per Agent

An agent can reference multiple resources when its task requires several
data sources:

```json
{
  "atoms": [
    { "kind": "resource", "uri": "tank://schemas/api-v2", "name": "api-schema" },
    { "kind": "resource", "uri": "tank://guides/error-codes", "name": "error-catalog" },
    {
      "kind": "agent",
      "name": "api-validator",
      "role": "Validate API implementations against the api-schema resource. Cross-reference error responses with the error-catalog resource.",
      "tools": ["read", "grep", "glob"]
    }
  ]
}
```

Limit to 3 resources per agent. Beyond that, consider splitting into
multiple agents with focused resource sets.

## Permission Implications

Every URI scheme has a permission footprint. Declare only what the resource
needs.

### Permission Matrix

| URI Scheme  | Permission Field         | Value Required                  |
| ----------- | ------------------------ | ------------------------------- |
| `tank://`   | (none)                   | Bundled content, always allowed |
| `file://`   | `filesystem.read`        | Path or glob covering the file  |
| `mcp://`    | `network.outbound`       | Server hostname (if remote)     |
| `https://`  | `network.outbound`       | `["api.example.com"]`           |

### Minimal Permission Examples

Static resource (no extra permissions):
```json
{
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  }
}
```

Resource reading a local generated file:
```json
{
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["./generated/**", "**/*"], "write": [] },
    "subprocess": false
  }
}
```

Resource reading from a remote API:
```json
{
  "permissions": {
    "network": { "outbound": ["api.example.com"] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  }
}
```

### Security Considerations

| Risk                              | Mitigation                                       |
| --------------------------------- | ------------------------------------------------ |
| Resource URI points to secrets    | Never use `file://` pointing to `.env` or creds  |
| MCP server returns untrusted data | Validate resource content in the consuming agent  |
| HTTPS endpoint changes content    | Pin to versioned endpoints, add cache headers     |
| Overly broad filesystem read      | Scope `filesystem.read` to specific directories   |

## Anti-Patterns

| Anti-Pattern                               | Problem                                    | Fix                                     |
| ------------------------------------------ | ------------------------------------------ | --------------------------------------- |
| Instruction for large reference data       | Bloats every prompt with 200+ lines        | Move to a resource atom                 |
| Resource for critical behavioral rules     | Agent may skip reading it                  | Use an instruction atom                 |
| Dynamic URI without fallback               | Agent fails if server/file is unavailable  | Provide a static fallback or error msg  |
| No description on resources in combos      | Agent cannot decide relevance              | Add a clear, concise description        |
| Bundling secrets in `tank://` resources    | Secrets shipped with the package           | Use `file://` pointing to `.env.local`  |
| Resource without a consuming agent/hook    | Orphaned data nobody reads                 | Remove or wire a consumer               |
