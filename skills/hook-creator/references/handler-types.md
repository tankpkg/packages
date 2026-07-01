# Handler Types: DSL vs JS/TS

Sources: Tank specification (AGENTS.md), quality-gate reference implementation (bundles/quality-gate/hooks/quality-gate.ts), adapter translation patterns

Covers: DSL handler actions and syntax, JS/TS handler architecture and API, canonical tool names for match patterns, migration path from DSL to JS, and platform adapter considerations.

## Two Handler Types

Tank hooks support exactly two handler types. Every hook atom must declare
one of them in its `handler` field.

| Property        | DSL Handler                          | JS/TS Handler                         |
| --------------- | ------------------------------------ | ------------------------------------- |
| Declaration     | `{ "type": "dsl", "actions": [...] }`| `{ "type": "js", "entry": "./path" }` |
| Portability     | All adapters                         | Adapter-dependent                     |
| Statefulness    | Stateless                            | Can maintain state                    |
| External calls  | None                                 | Shell, agents, APIs                   |
| Complexity      | Simple match-and-act                 | Arbitrary logic                       |
| Testing         | Declarative validation               | Unit/integration tests                |
| Recommended for | 80% of hooks                         | Complex gates and orchestration       |

## DSL Handlers

### Syntax

```json
{
  "kind": "hook",
  "event": "pre-command",
  "handler": {
    "type": "dsl",
    "actions": [
      { "action": "block", "match": "rm -rf", "reason": "Destructive command blocked" },
      { "action": "allow", "match": "npm test" },
      { "action": "rewrite", "match": "npm run dev", "to": "npm run dev -- --port 3001" }
    ]
  }
}
```

Actions are evaluated top-to-bottom. First match wins. If no action matches,
the default behavior is to allow the operation.

### DSL Actions

#### block

Prevent the operation from executing.

| Field    | Required | Description                                     |
| -------- | -------- | ----------------------------------------------- |
| `action` | Yes      | `"block"`                                       |
| `match`  | Yes      | String or pattern to match against               |
| `reason` | Yes      | Human-readable reason shown to the agent          |

```json
{ "action": "block", "match": "sudo", "reason": "Elevated privileges not allowed" }
```

The agent receives the reason and can adapt its approach. Use clear,
actionable reasons so the agent understands what to do instead.

#### allow

Explicitly permit the operation. Use to create allowlists when combined with
a catch-all block at the end.

| Field    | Required | Description                                     |
| -------- | -------- | ----------------------------------------------- |
| `action` | Yes      | `"allow"`                                       |
| `match`  | Yes      | String or pattern to match against               |

```json
{ "action": "allow", "match": "npm test" }
```

#### rewrite

Transform the operation before it executes. Only valid on pre-events.

| Field    | Required | Description                                     |
| -------- | -------- | ----------------------------------------------- |
| `action` | Yes      | `"rewrite"`                                     |
| `match`  | Yes      | String or pattern to match against               |
| `to`     | Yes      | Replacement string                               |

```json
{ "action": "rewrite", "match": "python", "to": "python3" }
```

#### injectContext

Add information to the agent's context. Valid on any event.

| Field     | Required | Description                                    |
| --------- | -------- | ---------------------------------------------- |
| `action`  | Yes      | `"injectContext"`                               |
| `content` | Yes      | String to inject, or file path to read          |

```json
{ "action": "injectContext", "content": "Always run tests before committing." }
```

### Match Patterns

The `match` field supports:

| Pattern Type  | Example                | Behavior                          |
| ------------- | ---------------------- | --------------------------------- |
| Exact string  | `"rm -rf /"`           | Exact substring match             |
| Glob          | `"*.test.ts"`          | File-path style matching          |
| Regex         | `"/^sudo\\s/"`         | Regex when wrapped in `/.../"     |

### Allowlist Pattern

Combine `allow` and `block` to create a restrictive allowlist:

```json
{
  "actions": [
    { "action": "allow", "match": "npm test" },
    { "action": "allow", "match": "npm run lint" },
    { "action": "allow", "match": "npm run build" },
    { "action": "block", "match": "*", "reason": "Only npm test/lint/build allowed" }
  ]
}
```

## JS/TS Handlers

### File Structure

Place handler files in a `hooks/` directory within the package:

```
bundles/{package-name}/
  hooks/
    my-hook.ts      # Handler source
  tank.json         # References ./hooks/my-hook.ts
```

### Handler Signature

Export a default async function that receives an event object and a context
object:

```typescript
export default async function handler(
  event: {
    type: string;
    properties?: Record<string, unknown>;
  },
  ctx: {
    client: {
      session: {
        prompt: (opts: unknown) => Promise<unknown>;
      };
    };
    $: (
      strings: TemplateStringsArray,
      ...args: unknown[]
    ) => { text: () => Promise<string> };
  },
): Promise<void> {
  // Hook logic here
}
```

### Context API

The `ctx` object provides:

| Method / Property         | Purpose                                          |
| ------------------------- | ------------------------------------------------ |
| `ctx.$\`command\``         | Execute a shell command, returns `{ text() }`    |
| `ctx.client.session.prompt`| Send a message back to the agent session         |

For `pre-stop` hooks, the context additionally supports:

| Method                    | Purpose                                          |
| ------------------------- | ------------------------------------------------ |
| `ctx.continueWithMessage` | Block the stop and send agent back to work       |
| `ctx.delegateToAgent`     | Spawn a subagent for review/analysis              |
| `ctx.modifiedFiles`       | Array of `{ path, hunks? }` changed in session   |

### Blocking vs Non-Blocking in JS

For pre-events (pre-stop, pre-tool-use, pre-command):

- **Return normally** to allow the action.
- **Call `ctx.continueWithMessage(msg)`** to block and redirect the agent.
- **Throw an error** to block with a generic error message.

For post-events, the return value is ignored. Use `ctx.client.session.prompt`
to inject follow-up context.

### State Management

JS handlers can maintain state across invocations using module-level
variables:

```typescript
const runCount = new Map<string, number>();

export default async function handler(event, ctx) {
  const sessionId = event.properties?.sessionID as string;
  const count = (runCount.get(sessionId) ?? 0) + 1;
  runCount.set(sessionId, count);
  // Use count to vary behavior on re-runs
}
```

See `bundles/quality-gate/hooks/quality-gate.ts` for a production example of
this pattern (re-run counter for iterative review).

### Delegating to Subagents

JS handlers can delegate work to named agents defined as companion atoms:

```typescript
const reviewOutput = await ctx.delegateToAgent("code-reviewer", prompt);
```

The subagent must be declared as a separate `kind: "agent"` atom in the same
package's `tank.json`. See `bundles/quality-gate/tank.json` for wiring.

## Canonical Tool Names

Use these names in DSL `match` fields and agent `tools` arrays:

| Tool Name  | Purpose                              | Example Match                      |
| ---------- | ------------------------------------ | ---------------------------------- |
| `bash`     | Shell command execution              | Block `rm -rf`, allow `npm test`   |
| `read`     | File reading                         | Block reading `.env` files         |
| `write`    | File creation/overwrite              | Block writing to `dist/`           |
| `edit`     | Partial file editing                 | Block edits to `package-lock.json` |
| `grep`     | Content search                       | Allow searching any file           |
| `glob`     | File pattern matching                | Allow globbing any directory       |
| `lsp`      | Language server operations           | Allow symbol lookup                |
| `mcp`      | MCP server tool invocation           | Block external API calls           |
| `browser`  | Browser automation                   | Block navigation to external sites |
| `fetch`    | HTTP requests                        | Block outbound network calls       |
| `git`      | Git operations                       | Block force push                   |
| `task`     | Task/todo management                 | Allow task updates                 |
| `notebook` | Notebook operations                  | Allow read, block execute          |

Custom tool names are also accepted. Adapters translate canonical names to
platform-specific equivalents.

## Migration Path: DSL to JS

Start with DSL. Migrate to JS when you hit a limitation.

### Step 1: Identify the trigger

The DSL handler works but you need one of:
- Conditional logic beyond simple matching
- Shell command execution
- Subagent delegation
- State across invocations
- Structured output parsing

### Step 2: Create the JS handler

1. Create `hooks/` directory in the package.
2. Write the handler file exporting a default async function.
3. Move the DSL match logic into the handler's body.

### Step 3: Update tank.json

Replace the DSL handler declaration:

```json
// Before (DSL)
{
  "kind": "hook",
  "event": "pre-command",
  "handler": {
    "type": "dsl",
    "actions": [{ "action": "block", "match": "rm -rf", "reason": "Destructive" }]
  }
}

// After (JS)
{
  "kind": "hook",
  "event": "pre-command",
  "handler": {
    "type": "js",
    "entry": "./hooks/command-gate.ts"
  }
}
```

### Step 4: Add companion atoms if needed

If the JS handler delegates to a subagent, add a `kind: "agent"` atom.
If the handler needs custom instructions, add a `kind: "instruction"` atom.

## Platform Adapter Considerations

Tank canonical events are translated by platform adapters:

| Tank Event        | Claude Code Equivalent    | OpenCode Equivalent      |
| ----------------- | ------------------------- | ------------------------ |
| `pre-stop`        | `PreToolUse` (stop check) | `pre-stop` hook          |
| `pre-command`     | `PreToolUse` (bash)       | `pre-command` hook       |
| `post-file-write` | `PostToolUse` (write)     | `post-file-write` hook   |
| `session-created` | Session init              | `session-created` hook   |

Write hooks against canonical event names. Adapters handle the translation.
Do not reference platform-specific event names in hook atoms.

## Testing Hooks

### DSL handlers

Validate the actions array declaratively:
- Confirm each action has required fields.
- Test match patterns against expected inputs.
- Verify first-match-wins ordering.

### JS handlers

Write standard unit tests:

```typescript
import handler from "./hooks/my-hook";

test("blocks destructive commands", async () => {
  const event = { type: "pre-command", properties: { command: "rm -rf /" } };
  const ctx = { /* mock context */ };
  await expect(handler(event, ctx)).rejects.toThrow();
});
```

For hooks that use `ctx.$` (shell commands), mock the template literal
function to return controlled output. For hooks that delegate to agents,
mock `ctx.delegateToAgent` to return expected review output.

See `bundles/quality-gate/hooks/quality-gate.ts` for patterns on parsing
structured agent output and managing re-run state.
