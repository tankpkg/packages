# Tank.json Anatomy for Multi-Atom Bundles

Sources: Tank Contributing Standard (AGENTS.md), @tank/quality-gate bundle,
Tank registry conventions (2025-2026).

Covers: every field in tank.json for multi-atom packages, the atoms array
structure, each atom kind with required and optional fields, handler types,
extension bags, and validation rules.

## Top-Level Fields

Every tank.json (instruction-only or multi-atom) requires these fields:

| Field         | Type   | Required | Description                                    |
| ------------- | ------ | -------- | ---------------------------------------------- |
| `name`        | string | Yes      | `@tank/{kebab-name}`, matches directory name   |
| `version`     | string | Yes      | Semver, start at `1.0.0`                       |
| `description` | string | Yes      | One paragraph, shorter than SKILL.md desc      |
| `permissions` | object | Yes      | Network, filesystem, subprocess declarations   |
| `repository`  | string | Yes      | `https://github.com/tankpkg/packages`          |
| `atoms`       | array  | Bundle   | Array of atom objects (absent for skills)      |

### Name

Must exactly match `@tank/{directory-name}`. The directory portion uses
lowercase letters, digits, and hyphens only. Maximum 64 characters for
the kebab-name portion.

```json
"name": "@tank/quality-gate"
```

The name in tank.json must match the `name` field in SKILL.md frontmatter
if the package includes a SKILL.md.

### Version

Standard semver. Start at `1.0.0` for new packages. Bump according to
semver rules:

| Change                     | Bump  |
| -------------------------- | ----- |
| Breaking atom removal/rename | Major |
| New atom added             | Minor |
| Bug fix, doc update        | Patch |

### Description

One paragraph. Shorter than the SKILL.md description. Include key trigger
words so the registry search can find the package.

### Repository

Always `https://github.com/tankpkg/packages` for packages in the Tank
registry repository.

## Permissions Object

Declares the maximum capabilities any atom in the bundle can exercise.
Follow the principle of least privilege.

```json
"permissions": {
  "network": { "outbound": [] },
  "filesystem": { "read": ["**/*"], "write": [] },
  "subprocess": false
}
```

### Network

| Field      | Type     | Description                              |
| ---------- | -------- | ---------------------------------------- |
| `outbound` | string[] | Hostnames the package may contact        |

Empty array means no network access. Add specific hostnames only when
an atom needs to call an external API.

```json
"network": { "outbound": ["api.github.com", "registry.npmjs.org"] }
```

### Filesystem

| Field   | Type     | Description                              |
| ------- | -------- | ---------------------------------------- |
| `read`  | string[] | Glob patterns for readable paths         |
| `write` | string[] | Glob patterns for writable paths         |

`["**/*"]` for read means "read anything in the project." Write is empty
by default. Add specific paths only when a hook or script writes files.

```json
"filesystem": { "read": ["**/*"], "write": ["reports/*.json"] }
```

### Subprocess

Boolean. `false` by default. Set to `true` only when a hook handler or
script spawns child processes (e.g., running `git diff`, `npm test`).

## The Atoms Array

The `atoms` field is an array of atom objects. Each object must have a
`kind` field that determines its type and required fields. Order in the
array is declaration order, not execution order — the runtime resolves
execution based on events and triggers.

```json
"atoms": [
  { "kind": "instruction", "content": "./SKILL.md" },
  { "kind": "hook", "event": "pre-stop", "handler": { "type": "js", "entry": "./hooks/gate.ts" } },
  { "kind": "agent", "name": "reviewer", "role": "Code reviewer", "tools": ["read", "grep"] }
]
```

### Validation Rules

- Every atom must have a valid `kind` from the canonical set
- File paths in `content` and `handler.entry` must reference existing files
- Agent `tools` must use canonical tool names or custom strings
- No two agents in the same bundle should share a `name`
- Hook events must come from the canonical event list

## Atom Kind: instruction

Injects behavioral context into the agent's system prompt.

| Field     | Type   | Required | Description                        |
| --------- | ------ | -------- | ---------------------------------- |
| `kind`    | string | Yes      | `"instruction"`                    |
| `content` | string | Yes      | Relative path to markdown file     |

```json
{ "kind": "instruction", "content": "./SKILL.md" }
```

The referenced file is loaded into agent context when the package is
active. Keep instruction files under 200 lines. Use `references/` for
deep content that loads on demand.

## Atom Kind: hook

Runs code at specific lifecycle events. Hooks can block, rewrite, inject
context, or delegate to agents.

| Field     | Type   | Required | Description                        |
| --------- | ------ | -------- | ---------------------------------- |
| `kind`    | string | Yes      | `"hook"`                           |
| `event`   | string | Yes      | Canonical event name               |
| `handler` | object | Yes      | Handler definition (DSL or JS)     |
| `name`    | string | No       | Human-readable hook name           |

### Handler Types

**DSL handler** — declarative, portable, no code files needed:

```json
{
  "type": "dsl",
  "actions": [
    { "action": "block", "match": "rm -rf /", "reason": "Destructive command" },
    { "action": "rewrite", "match": "sudo ", "replace": "" }
  ]
}
```

DSL actions: `block`, `allow`, `rewrite`, `injectContext`.

**JS handler** — full code, can delegate to agents, access git, etc:

```json
{
  "type": "js",
  "entry": "./hooks/quality-gate.ts"
}
```

The entry file exports a default async function that receives an event
object and a context object. See @tank/quality-gate for the canonical
implementation.

### Canonical Hook Events

| Category      | Events                                                    |
| ------------- | --------------------------------------------------------- |
| Tool          | `pre-tool-use`, `post-tool-use`                           |
| File          | `pre-file-write`, `post-file-write`, `file-edited`        |
| Shell         | `pre-command`, `post-command`                              |
| MCP           | `pre-mcp-tool-use`, `post-mcp-tool-use`                   |
| Session       | `session-created`, `session-idle`, `session-error`         |
| Stop          | `pre-stop` (blocking — can force agent to continue)       |
| Task          | `task-start`, `task-complete`, `task-cancel`               |
| Conversation  | `pre-user-prompt`, `post-response`                        |
| System prompt | `system-prompt-transform`                                 |
| Context       | `pre-context-compact`, `post-context-compact`              |
| Subagent      | `subagent-start`, `subagent-complete`                     |

## Atom Kind: agent

Defines a named sub-agent with constrained tools and permissions.

| Field      | Type     | Required | Description                         |
| ---------- | -------- | -------- | ----------------------------------- |
| `kind`     | string   | Yes      | `"agent"`                           |
| `name`     | string   | Yes      | Unique name within the bundle       |
| `role`     | string   | Yes      | System prompt for the agent         |
| `tools`    | string[] | No       | Canonical tool names allowed        |
| `model`    | string   | No       | Model tier: fast/balanced/powerful   |
| `readonly` | boolean  | No       | If true, agent cannot write files   |

```json
{
  "kind": "agent",
  "name": "code-reviewer",
  "role": "Senior code reviewer. Flag bugs and security issues by severity.",
  "tools": ["read", "grep", "glob", "lsp"],
  "model": "fast",
  "readonly": true
}
```

Canonical tool names: `bash`, `read`, `write`, `edit`, `grep`, `glob`,
`lsp`, `mcp`, `browser`, `fetch`, `git`, `task`, `notebook`.

Model tiers: `fast`, `balanced`, `powerful`, `custom`.

## Atom Kind: rule

Declares a machine-enforced validation constraint. No code needed — the
runtime enforces the policy.

| Field    | Type   | Required | Description                          |
| -------- | ------ | -------- | ------------------------------------ |
| `kind`   | string | Yes      | `"rule"`                             |
| `event`  | string | Yes      | Canonical event name                 |
| `policy` | string | Yes      | `"block"`, `"warn"`, or `"allow"`    |
| `reason` | string | No       | Human-readable explanation           |

```json
{
  "kind": "rule",
  "event": "pre-stop",
  "policy": "block",
  "reason": "Unresolved issues found"
}
```

## Atom Kind: tool

Registers an MCP server the agent can invoke.

| Field  | Type   | Required | Description                          |
| ------ | ------ | -------- | ------------------------------------ |
| `kind` | string | Yes      | `"tool"`                             |
| `name` | string | Yes      | Tool identifier                      |

```json
{ "kind": "tool", "name": "custom-linter" }
```

Requires `network.outbound` or `subprocess: true` in permissions if the
tool communicates externally or spawns processes.

## Atom Kind: resource

Exposes data or context the agent can read.

| Field  | Type   | Required | Description                          |
| ------ | ------ | -------- | ------------------------------------ |
| `kind` | string | Yes      | `"resource"`                         |
| `uri`  | string | Yes      | URI to the resource                  |

```json
{ "kind": "resource", "uri": "file://./data/schema.json" }
```

## Atom Kind: prompt

Defines a reusable invocable template (slash command or callable prompt).

| Field      | Type   | Required | Description                        |
| ---------- | ------ | -------- | ---------------------------------- |
| `kind`     | string | Yes      | `"prompt"`                         |
| `name`     | string | Yes      | Command or template name           |
| `template` | string | Yes      | Template content or file path      |

```json
{ "kind": "prompt", "name": "review", "template": "Review {{files}} for {{criteria}}" }
```

## Extension Bags

Any atom can include an `extensions` object with platform-specific
overrides. Extensions are passed through without validation — adapters
own their shape.

```json
{
  "kind": "instruction",
  "content": "./SKILL.md",
  "extensions": {
    "cursor": { "alwaysApply": true },
    "opencode": { "scope": "global" }
  }
}
```

Use extension bags to customize behavior per platform without forking the
package. Platform names as keys, arbitrary objects as values.

## Complete Minimal Bundle Example

```json
{
  "name": "@tank/example-bundle",
  "version": "1.0.0",
  "description": "Example multi-atom bundle.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" },
    {
      "kind": "hook",
      "event": "pre-stop",
      "handler": { "type": "js", "entry": "./hooks/gate.ts" }
    },
    {
      "kind": "agent",
      "name": "checker",
      "role": "Validate output quality.",
      "tools": ["read", "grep"],
      "readonly": true
    }
  ]
}
```
