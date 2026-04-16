---
name: "@tank/resource-creator"
description: |
  Author Tank resource atoms -- URI-addressable data or context that agents
  can read on demand. Covers the resource atom schema (required `uri` field),
  URI scheme conventions, static vs dynamic resources, the pull-model
  distinction (resources are read on demand, instructions are always injected),
  relationship to MCP resources, permission implications, and composing
  resources with agent atoms. Includes worked examples for project context
  maps, style guides, config resources, and agent+resource combos.
  Synthesizes Tank specification (AGENTS.md), MCP resource specification,
  and production bundle patterns.

  Trigger phrases: "create resource", "resource atom", "tank resource",
  "uri resource", "context resource", "agent context", "readable resource",
  "resource uri", "agent data source", "on-demand context",
  "resource vs instruction", "project context map", "style guide resource",
  "config resource", "compose resource with agent"
---

# Tank Resource Creator

## Core Philosophy

1. **Pull over push.** Resources exist so agents can fetch context when
   needed, not have it forced into every prompt. Use a resource when the
   data is large, situational, or only relevant to specific tasks.
   -> See `references/resource-design.md`

2. **URIs are contracts.** The `uri` field is the single required field on
   a resource atom. Treat it like an API endpoint -- stable, descriptive,
   and versioned when the schema changes.
   -> See `references/resource-atom-anatomy.md`

3. **Resources are not instructions.** Instructions inject behavioral
   context unconditionally. Resources provide data the agent can choose to
   read. Confusing the two bloats context windows or starves agents of
   needed information.

4. **Compose with agents.** The highest-value pattern pairs a resource atom
   with an agent atom -- the agent reads the resource as input to its task.
   Design resources with a specific consumer in mind.
   -> See `references/worked-examples.md`

5. **Scope permissions to the resource.** A resource that reads the
   filesystem needs `filesystem.read` permission. A resource backed by a
   remote MCP endpoint needs `network.outbound`. Never grant broader
   permissions than the resource requires.

## Quick-Start: Common Problems

### "Expose a project architecture map to agents"

1. Create a markdown file describing the codebase structure.
2. Add a resource atom: `{ "kind": "resource", "uri": "tank://context/architecture" }`.
3. Wire it in `tank.json` alongside an instruction or agent atom.
   -> See `references/worked-examples.md` (Project Context Resource)

### "Give an agent a style guide to reference"

1. Write the style guide as a markdown reference file.
2. Add a resource atom pointing to it.
3. Pair it with an agent atom that has `tools: ["read"]` so it can access
   the resource content.
   -> See `references/worked-examples.md` (Style Guide Resource)

### "Serve dynamic config that changes per environment"

1. Use a `file://` or MCP-backed URI that resolves at runtime.
2. Add the resource atom with the dynamic URI.
3. Ensure the `permissions` block covers the access pattern.
   -> See `references/resource-design.md` (Static vs Dynamic Resources)

### "Decide: resource or instruction?"

1. Check the decision tree below.
2. If the content is always needed and under 50 lines, use an instruction.
3. If the content is situational, large, or task-specific, use a resource.
   -> See `references/resource-design.md`

## Decision Trees

### Resource vs Instruction

| Signal                                    | Use Resource     | Use Instruction  |
| ----------------------------------------- | ---------------- | ---------------- |
| Content is always relevant to every task  | No               | Yes              |
| Content is large (>50 lines)              | Yes              | Bloats context   |
| Content is only needed for specific tasks | Yes              | Wasteful         |
| Content changes per environment/run       | Yes              | Cannot           |
| Content is behavioral (rules, persona)    | Rarely           | Yes              |
| Content is data (schemas, maps, specs)    | Yes              | Overkill         |

### URI Scheme Selection

| Data Location                    | URI Scheme       | Example                              |
| -------------------------------- | ---------------- | ------------------------------------ |
| Bundled file in the package      | `tank://`        | `tank://context/architecture`        |
| Local filesystem path            | `file://`        | `file://./references/style-guide.md` |
| Remote MCP resource endpoint     | `mcp://`         | `mcp://server-name/resource-path`    |
| HTTPS endpoint (read-only)       | `https://`       | `https://api.example.com/config`     |

### Manifest Wiring

| Component         | Location in tank.json                     |
| ----------------- | ----------------------------------------- |
| Resource atom     | `atoms[]` with `kind: "resource"`         |
| URI binding       | `uri` field on the resource atom          |
| Companion agent   | Separate atom with `kind: "agent"`        |
| Permissions       | Top-level `permissions` object            |

## Reference Index

| File                                  | Contents                                          |
| ------------------------------------- | ------------------------------------------------- |
| `references/resource-atom-anatomy.md` | Schema, required fields, URI schemes, relationship to MCP resources |
| `references/resource-design.md`       | When to use resources, URI conventions, static vs dynamic, permissions |
| `references/worked-examples.md`       | 4+ worked resource examples with full tank.json snippets |
