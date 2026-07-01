# Resource Atom Anatomy

Sources: Tank specification (AGENTS.md), MCP resource specification (2025-2026)

Covers: the Tank `kind: "resource"` atom schema, required and optional fields,
URI scheme conventions, how resources differ from instructions (pull vs push),
and the relationship between Tank resource atoms and MCP resources.

## The Resource Atom in the Tank Type System

Tank defines seven atom kinds. Each serves a distinct role in shaping agent
behavior. The resource atom occupies a specific niche: **data the agent can
read on demand**.

| Atom Kind     | Delivery Model | Agent Interaction                |
| ------------- | -------------- | -------------------------------- |
| `instruction` | Push (always)  | Injected into every prompt       |
| `resource`    | Pull (demand)  | Read when the agent requests it  |
| `hook`        | Event-driven   | Triggered by lifecycle events    |
| `agent`       | Delegation     | Spawned as a named sub-agent     |
| `rule`        | Event-driven   | Machine-enforced constraint      |
| `tool`        | Invocation     | Called as an MCP tool             |
| `prompt`      | Invocation     | Rendered from a template         |

The critical distinction: instructions are **always loaded** into the agent's
context window. Resources are **available but not loaded** until the agent or
another atom requests them.

## Required Fields

The resource atom has one required field:

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture"
}
```

### `uri` (required, string)

The URI that identifies and locates the resource content. Must be a valid
URI string. The scheme portion determines how the resource is resolved.

## Optional Fields

### `name` (optional, string)

A human-readable identifier for the resource. Useful when multiple resources
exist in a bundle and agents or hooks need to reference a specific one.

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "name": "project-architecture"
}
```

### `description` (optional, string)

A brief explanation of what the resource contains. Helps agents decide
whether to read this resource for a given task.

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "name": "project-architecture",
  "description": "High-level codebase map with module boundaries and data flow"
}
```

### `extensions` (optional, object)

Platform-specific overrides. Adapters own the shape of their extension data.
Tank passes extensions through without validation.

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "extensions": {
    "opencode": { "autoLoad": true },
    "cursor": { "pinned": true }
  }
}
```

## URI Schemes

The `uri` field supports multiple schemes. Each scheme determines how the
adapter resolves the resource content at runtime.

### `tank://` -- Package-Relative Resources

Points to a file bundled within the Tank package itself. The adapter resolves
the path relative to the package root.

```
tank://context/architecture
tank://data/schema-map
tank://guides/style-guide
```

Convention: use `tank://` for any content that ships with the package and
does not change between environments. The path segments after the scheme
are logical names, not filesystem paths -- the adapter maps them to actual
files.

### `file://` -- Local Filesystem Resources

Points to a file on the local filesystem. Can be absolute or relative to
the project root.

```
file://./references/style-guide.md
file://./assets/api-schema.json
file:///absolute/path/to/config.yaml
```

Use `file://` when the resource content lives outside the package -- for
example, a generated file in the project's build output or a config file
in the repository root.

Permission requirement: `filesystem.read` must include the target path.

### `mcp://` -- MCP Server Resources

Points to a resource exposed by an MCP server. The adapter delegates
resolution to the MCP client connected to the named server.

```
mcp://database-server/schema/users
mcp://docs-server/api-reference/auth
```

Format: `mcp://{server-name}/{resource-path}`

The server name must match a configured MCP server in the agent's
environment. The resource path is passed to the MCP server's
`resources/read` endpoint.

Permission requirement: `network.outbound` must include the MCP server
if it is remote.

### `https://` -- Remote HTTP Resources

Points to a read-only HTTP endpoint. The adapter fetches the content via
a standard GET request.

```
https://api.example.com/v1/config
https://raw.githubusercontent.com/org/repo/main/schema.json
```

Use `https://` for external data sources that the agent needs at runtime.
Prefer `tank://` or `file://` for content that can be bundled.

Permission requirement: `network.outbound` must include the hostname.

## URI Naming Conventions

Follow these conventions for consistent, discoverable URIs:

| Convention              | Example                          | Rationale                       |
| ----------------------- | -------------------------------- | ------------------------------- |
| Lowercase with hyphens  | `tank://context/code-map`        | Consistent with Tank naming     |
| Logical path segments   | `tank://guides/style-guide`      | Describes content, not location |
| Version suffix if needed| `tank://schemas/api-v2`          | Supports schema evolution       |
| No file extensions      | `tank://data/config` not `.json` | URI is abstract, not a path     |
| Descriptive leaf name   | `tank://context/module-boundaries` | Self-documenting               |

## How Resources Differ from Instructions

This comparison is the most common source of confusion. Internalize it.

### Instruction Atom Behavior

```json
{ "kind": "instruction", "content": "./SKILL.md" }
```

- Content is loaded into the agent's system prompt or context window at
  session start.
- Every message the agent processes includes the instruction content.
- Cost: consumes tokens on every turn, even when irrelevant.
- Benefit: guarantees the agent always has the behavioral context.
- Best for: persona, rules, constraints, behavioral directives.

### Resource Atom Behavior

```json
{ "kind": "resource", "uri": "tank://context/architecture" }
```

- Content is registered as available but not loaded by default.
- The agent (or a companion agent/hook) reads the resource when needed.
- Cost: zero tokens when not read; full content when read.
- Benefit: large data sets do not bloat every prompt.
- Best for: reference data, schemas, maps, specs, style guides.

### Side-by-Side Comparison

| Dimension           | Instruction                | Resource                    |
| ------------------- | -------------------------- | --------------------------- |
| Loading model       | Push (always injected)     | Pull (read on demand)       |
| Context cost        | Every turn                 | Only when accessed          |
| Content type        | Behavioral (rules, tone)   | Data (schemas, maps, specs) |
| Size sweet spot     | Under 50 lines             | Any size                    |
| Mutability          | Static per session         | Can resolve dynamically     |
| Required field      | `content` (file path)      | `uri` (URI string)          |

## Relationship to MCP Resources

Tank resource atoms and MCP resources are related but operate at different
abstraction layers.

### MCP Resources (Protocol Level)

MCP defines a `resources/list` and `resources/read` protocol for servers
to expose data to clients. An MCP resource has:

- A URI (unique identifier)
- A name and optional description
- A MIME type
- Content (text or binary blob)

MCP resources are a **transport mechanism** -- they define how data moves
between a server and a client over the MCP protocol.

### Tank Resource Atoms (Package Level)

A Tank resource atom is a **package primitive** that declares data an agent
can access. It may or may not be backed by an MCP resource.

- `tank://` and `file://` URIs: resolved by the adapter directly, no MCP
  involved.
- `mcp://` URIs: delegated to an MCP server's `resources/read` endpoint.
- `https://` URIs: fetched via HTTP, no MCP involved.

### When They Overlap

A Tank resource atom with an `mcp://` URI is a thin wrapper around an MCP
resource. The Tank atom adds:

- Package-level declaration (the resource is part of a versioned bundle)
- Permission enforcement (the `permissions` block gates access)
- Discoverability (agents know the resource exists from the manifest)
- Composition (the resource can be paired with agent/hook atoms)

### When They Do Not Overlap

A Tank resource atom with a `tank://`, `file://`, or `https://` URI has
no MCP involvement. The adapter resolves the URI directly without any
MCP server interaction.

Rule of thumb: use `mcp://` only when the data originates from an MCP
server that is already configured in the environment. For everything else,
use `tank://` (bundled) or `file://` (local).

## Minimal Valid Resource Atom

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture"
}
```

## Fully Specified Resource Atom

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "name": "project-architecture",
  "description": "Module boundaries, data flow, and dependency graph for the monorepo",
  "extensions": {
    "opencode": { "autoLoad": true }
  }
}
```

## Validation Rules

The adapter validates resource atoms at package load time:

| Rule                          | Enforcement                              |
| ----------------------------- | ---------------------------------------- |
| `kind` must be `"resource"`   | Schema validation                        |
| `uri` must be a valid URI     | URI parsing (scheme required)            |
| `uri` scheme must be known    | Warn on unknown schemes                  |
| `name` must be unique in bundle | Collision detection across atoms       |
| Permissions must cover access | `filesystem.read` for `file://`, `network.outbound` for `https://` and remote `mcp://` |

## Anti-Patterns

| Anti-Pattern                          | Problem                                   | Fix                                |
| ------------------------------------- | ----------------------------------------- | ---------------------------------- |
| Using a resource for behavioral rules | Agent may not read it; rules get ignored  | Use an instruction atom instead    |
| Hardcoding absolute `file://` paths   | Breaks on other machines                  | Use `tank://` or relative paths    |
| No `name` on multiple resources       | Ambiguous references from agents/hooks    | Add a descriptive `name` field     |
| `mcp://` without configured server    | Resolution fails at runtime               | Verify server exists or use `tank://` |
| Giant resource with no description    | Agent cannot decide if it is relevant     | Add a concise `description` field  |
