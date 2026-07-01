---
name: "@tank/rule-creator"
description: |
  Author Tank rule atoms -- declarative, machine-enforced validation constraints
  that block, allow, or warn on agent behavior at any lifecycle event. Covers the
  rule atom schema (event, policy, reason, match, extensions), policy design
  (block vs warn vs allow, ordering, precedence, false-positive mitigation),
  composing rule sets inside multi-atom bundles, and worked examples for safety,
  code-style, tool-gating, and combined rule+instruction patterns.
  Synthesizes Tank specification (AGENTS.md), policy-as-code patterns (OPA/Rego,
  Sentinel), and production rule bundle analysis.

  Trigger phrases: "create rule", "tank rule atom", "rule atom", "block policy",
  "warn policy", "allow policy", "safety rule", "enforce rule", "validation rule",
  "guard rule", "write a rule", "rule bundle", "policy set", "pre-command rule",
  "pre-tool-use rule", "block rm -rf", "block destructive", "code style rule"
---

# Rule Creator

Author declarative rule atoms that enforce constraints on agent behavior
without writing code. Rules are data, not logic -- the runtime evaluates them.

## Core Philosophy

1. **Rules are data, hooks are code** -- A rule declares "block X when Y" as
   a JSON object. A hook executes arbitrary TypeScript. Prefer rules for
   anything expressible as a match-and-act pair. Reach for hooks only when
   rules lack the expressiveness.
2. **Block is a last resort** -- Blocking halts the agent. Use `warn` for
   guidance, `allow` for explicit permission, `block` only for genuinely
   dangerous operations. Over-blocking creates a useless agent.
3. **Reason is not optional** -- Every rule must include a `reason` field
   explaining *why* the constraint exists. The agent reads reasons to adjust
   behavior before hitting the wall.
4. **Compose, don't monolith** -- Ship rule sets as arrays inside a bundle's
   `atoms`. Each rule targets one concern. Ten focused rules beat one
   mega-rule with complex match logic.
5. **Test by triggering** -- Verify a rule works by deliberately triggering
   its condition. A rule you have never seen fire is a rule you cannot trust.

## Quick-Start: Common Problems

### "Block a dangerous shell command"

1. Create a multi-atom bundle under `bundles/`
2. Add a `kind: "rule"` atom with `event: "pre-command"`
3. Set `policy: "block"`, add `match` and `reason`
   -> See `references/rule-atom-anatomy.md` for field schema
   -> See `references/worked-examples.md` for `rm -rf` example

### "Warn when agent writes bad patterns"

1. Add a `kind: "rule"` atom with `event: "post-file-write"`
2. Set `policy: "warn"`, match against the pattern (e.g., `as any`)
3. Pair with an instruction atom explaining the preferred alternative
   -> See `references/policy-design.md` for warn vs block guidance
   -> See `references/worked-examples.md` for `as any` example

### "Restrict which tools the agent can use"

1. Add a `kind: "rule"` atom with `event: "pre-tool-use"`
2. Set `policy: "allow"` with a `match` on the approved tool list
3. Add a second rule with `policy: "block"` as a catch-all deny
   -> See `references/worked-examples.md` for allow-list example

### "Ship a complete policy set"

1. Create a `bundles/{name}/` directory
2. Add an `atoms` array with multiple rule atoms + an instruction atom
3. The instruction explains the rationale; rules enforce it
   -> See `references/policy-design.md` for composition patterns
   -> See `references/worked-examples.md` for combined bundle example

## Decision Trees

### Policy Selection

| Signal                                    | Policy  | Rationale                              |
| ----------------------------------------- | ------- | -------------------------------------- |
| Data loss, credential leak, system damage | `block` | Irreversible harm, stop immediately    |
| Code smell, style violation, minor risk   | `warn`  | Educate without halting                |
| Known-safe operation in a restricted set  | `allow` | Explicit permission overrides defaults |

### Event Selection

| Constraint target      | Event                | Category |
| ---------------------- | -------------------- | -------- |
| Shell command content   | `pre-command`        | Shell    |
| Tool invocation         | `pre-tool-use`       | Tool     |
| File content after save | `post-file-write`    | File     |
| File content before save| `pre-file-write`     | File     |
| MCP tool call           | `pre-mcp-tool-use`   | MCP      |
| Agent finishing work    | `pre-stop`           | Stop     |
| Agent response          | `post-response`      | Convo    |

### Rule vs Hook

| Need                                        | Use   |
| ------------------------------------------- | ----- |
| Match string/pattern, act with fixed policy | Rule  |
| Conditional logic, external API calls       | Hook  |
| Multiple rules composing a policy set       | Rules |
| Dynamic rewriting of commands/content       | Hook  |
| Simple block/warn/allow on a known pattern  | Rule  |

## Atom Schema Quick Reference

```json
{
  "kind": "rule",
  "event": "pre-command",
  "policy": "block",
  "match": "rm -rf",
  "reason": "Destructive file deletion is not permitted",
  "extensions": {}
}
```

Required: `kind`, `event`, `policy`. Strongly recommended: `reason`.
Optional: `match`, `name`, `extensions`.

-> See `references/rule-atom-anatomy.md` for complete field reference.

## Reference Index

| File                               | Contents                                         |
| ---------------------------------- | ------------------------------------------------ |
| `references/rule-atom-anatomy.md`  | Full rule atom schema, fields, types, events     |
| `references/policy-design.md`      | Policy strategy, composition, precedence, safety |
| `references/worked-examples.md`    | 4+ complete rule examples with tank.json context |
