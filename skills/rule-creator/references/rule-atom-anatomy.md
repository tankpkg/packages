# Rule Atom Anatomy

Sources: Tank specification (AGENTS.md), OPA/Rego policy language, Sentinel (HashiCorp), AWS SCPs

Covers: the complete `kind: "rule"` atom schema -- every field, its type, constraints, and
relationship to the Tank lifecycle event system.

## What a Rule Atom Is

A rule atom is a declarative JSON object inside a `tank.json` `atoms` array. It expresses
a single validation constraint: "at this lifecycle point, if this condition matches,
apply this policy." The Tank runtime evaluates rules -- no code executes. Rules are
the declarative counterpart to hook atoms.

```json
{
  "kind": "rule",
  "event": "pre-command",
  "policy": "block",
  "match": "rm -rf",
  "reason": "Destructive file deletion is prohibited in this project"
}
```

## Required Fields

### `kind`

Always the literal string `"rule"`. Identifies this atom as a machine-enforced
validation constraint.

```json
"kind": "rule"
```

### `event`

The canonical lifecycle event this rule binds to. The rule fires when the runtime
reaches this event. Use events from the Tank canonical event table.

```json
"event": "pre-command"
```

Rules bind to events identically to hooks. The difference: hooks execute handler
code; rules evaluate a policy decision from data.

### `policy`

The enforcement action. One of three values:

| Policy  | Behavior                                         | Agent impact              |
| ------- | ------------------------------------------------ | ------------------------- |
| `block` | Halt the operation. The agent cannot proceed.    | Hard stop, must reroute   |
| `warn`  | Surface the reason. The agent may continue.      | Soft guidance, no halt    |
| `allow` | Explicitly permit. Overrides broader restrictions.| Green-light signal        |

```json
"policy": "block"
```

#### Policy semantics

- **block**: The runtime prevents the triggering action from executing. The agent
  receives the `reason` and must find an alternative. Use for irreversible or
  dangerous operations.
- **warn**: The runtime surfaces the `reason` to the agent as advisory context.
  The operation proceeds. Use for code quality, style, and soft constraints.
- **allow**: The runtime explicitly permits the operation. Useful in allow-list
  patterns where a catch-all block exists and specific operations are exempted.

## Strongly Recommended Fields

### `reason`

A human-readable string explaining why the rule exists. The agent reads this.
Write it as an instruction the agent can act on.

```json
"reason": "Use structured error handling instead of bare try/catch with no action"
```

Good reasons:
- Explain the risk: "Credential files must not be committed to version control"
- Suggest an alternative: "Use `trash` CLI instead of `rm -rf` for safe deletion"
- Reference a standard: "Violates project TypeScript strict mode -- no `as any` casts"

Bad reasons:
- Vague: "Not allowed"
- Accusatory: "You should know better"
- Missing: (omitted entirely)

## Optional Fields

### `match`

A string or pattern the runtime checks against the event payload. The matching
semantics depend on the adapter (substring, glob, regex). Keep patterns simple
and portable.

```json
"match": "rm -rf"
```

Match targets by event type:

| Event              | Match target                              |
| ------------------ | ----------------------------------------- |
| `pre-command`      | The shell command string                  |
| `post-command`     | The shell command string                  |
| `pre-tool-use`     | The tool name (canonical or custom)       |
| `post-tool-use`    | The tool name                             |
| `pre-file-write`   | The file path or content                  |
| `post-file-write`  | The file path or content                  |
| `pre-file-read`    | The file path                             |
| `pre-mcp-tool-use` | The MCP tool name                         |
| `pre-stop`         | (no match target -- fires unconditionally)|

When `match` is omitted, the rule fires unconditionally for every occurrence
of the bound event.

### `name`

An optional identifier for the rule. Useful for logging, debugging, and
referencing specific rules in documentation.

```json
"name": "no-force-push"
```

### `extensions`

Platform-specific overrides. Adapters translate generic rule semantics into
platform-native enforcement. Extensions are passed through without validation.

```json
"extensions": {
  "cursor": { "severity": "error" },
  "opencode": { "scope": "project" }
}
```

## Complete Field Reference

| Field        | Required | Type   | Values / Constraints                    |
| ------------ | -------- | ------ | --------------------------------------- |
| `kind`       | Yes      | string | `"rule"` (literal)                      |
| `event`      | Yes      | string | Any canonical event from Tank spec      |
| `policy`     | Yes      | string | `"block"`, `"warn"`, `"allow"`          |
| `reason`     | No*      | string | Human-readable explanation              |
| `match`      | No       | string | Pattern matched against event payload   |
| `name`       | No       | string | Identifier for logging/debugging        |
| `extensions` | No       | object | Platform-specific overrides             |

*Strongly recommended. Omitting `reason` produces rules the agent cannot learn from.

## Canonical Events Rules Can Bind To

Rules can bind to any canonical event. The most common bindings:

### Shell events

| Event          | Fires when                    | Typical use                  |
| -------------- | ----------------------------- | ---------------------------- |
| `pre-command`  | Before a shell command runs   | Block dangerous commands     |
| `post-command` | After a shell command returns | Audit command history        |

### Tool events

| Event          | Fires when                    | Typical use                  |
| -------------- | ----------------------------- | ---------------------------- |
| `pre-tool-use` | Before any tool invocation    | Tool allow-lists, deny-lists |
| `post-tool-use`| After a tool returns          | Output validation            |

### File events

| Event              | Fires when                    | Typical use                |
| ------------------ | ----------------------------- | -------------------------- |
| `pre-file-write`   | Before a file is written      | Block writes to protected paths |
| `post-file-write`  | After a file is written       | Content quality checks     |
| `pre-file-read`    | Before a file is read         | Sensitive file access control |

### MCP events

| Event               | Fires when                   | Typical use               |
| ------------------- | ---------------------------- | ------------------------- |
| `pre-mcp-tool-use`  | Before an MCP tool call      | MCP tool restrictions     |
| `post-mcp-tool-use` | After an MCP tool returns    | Response validation       |

### Session and stop events

| Event          | Fires when                    | Typical use                  |
| -------------- | ----------------------------- | ---------------------------- |
| `pre-stop`     | Agent attempts to stop        | Final quality gates          |
| `session-idle` | Session goes idle             | Timeout warnings             |

### Conversation events

| Event           | Fires when                    | Typical use                 |
| --------------- | ----------------------------- | --------------------------- |
| `post-response` | After the agent responds      | Output content policies     |
| `pre-user-prompt`| Before user input is processed| Input sanitization rules   |

## Minimal Valid Rule

The absolute minimum:

```json
{
  "kind": "rule",
  "event": "pre-command",
  "policy": "block"
}
```

This blocks every shell command unconditionally. Not useful, but valid.

## Recommended Minimal Rule

Include `match` and `reason` for a rule that actually works:

```json
{
  "kind": "rule",
  "event": "pre-command",
  "policy": "block",
  "match": "rm -rf /",
  "reason": "Root filesystem deletion is catastrophic and irreversible"
}
```

## Rule vs Hook Decision

| Characteristic         | Rule                        | Hook                         |
| ---------------------- | --------------------------- | ---------------------------- |
| Expressed as           | JSON data                   | TypeScript/JavaScript code   |
| Complexity             | Match + policy              | Arbitrary logic              |
| Composability          | Array of atoms              | Single handler per event     |
| Portability            | Cross-platform (adapters)   | Platform-dependent runtime   |
| Debugging              | Inspect JSON                | Debug code execution         |
| Dynamic conditions     | Not supported               | Full language access         |
| External API calls     | Not supported               | Supported                    |
| State management       | Stateless                   | Can maintain state           |

Choose rules when the constraint is expressible as "if X matches, then Y."
Choose hooks when the constraint requires logic, conditionals, or side effects.

## Placement in tank.json

Rules live inside the `atoms` array alongside other atom kinds:

```json
{
  "name": "@tank/my-safety-rules",
  "version": "1.0.0",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" },
    { "kind": "rule", "event": "pre-command", "policy": "block", "match": "rm -rf", "reason": "..." },
    { "kind": "rule", "event": "pre-tool-use", "policy": "warn", "match": "bash", "reason": "..." }
  ]
}
```

Order within the array does not determine evaluation order. The runtime evaluates
all rules bound to a given event. See `references/policy-design.md` for
precedence and composition patterns.

## Validation Checklist

Before publishing a rule atom:

- [ ] `kind` is exactly `"rule"`
- [ ] `event` is a valid canonical event from the Tank spec
- [ ] `policy` is one of `"block"`, `"warn"`, `"allow"`
- [ ] `reason` is present and actionable
- [ ] `match` targets the correct payload for the bound event
- [ ] Rule is testable -- you can deliberately trigger the condition
- [ ] Rule lives inside a multi-atom bundle (bundles/, not skills/)
