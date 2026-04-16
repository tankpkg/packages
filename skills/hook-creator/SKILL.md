---
name: "@tank/hook-creator"
description: |
  Author Tank hook atoms that intercept agent lifecycle events. Covers
  every canonical hook event (pre-tool-use, post-file-write, pre-stop,
  session-created, etc.), DSL handlers for portable logic (block, allow,
  rewrite, injectContext), JS/TS handlers for complex behavior, manifest
  wiring in tank.json, and production patterns from the quality-gate bundle.
  Synthesizes Tank specification (AGENTS.md), quality-gate reference
  implementation, and adapter translation patterns for Claude Code,
  OpenCode, Cursor, and Windsurf.

  Trigger phrases: "create hook", "write a hook", "hook atom", "tank hook",
  "pre-stop hook", "pre-tool-use hook", "post-file-write hook",
  "lifecycle hook", "block agent", "DSL handler", "JS handler",
  "hook handler", "agent gate", "safety gate", "intercept agent",
  "hook event"
---

# Tank Hook Creator

## Core Philosophy

1. **Hooks are guardrails, not gods.** A hook intercepts a single lifecycle
   event, makes a binary decision (block/allow/rewrite/inject), and exits.
   Keep them narrow and deterministic.

2. **DSL first, JS when forced.** DSL handlers are portable across every
   adapter. Reach for JS/TS only when you need stateful logic, external
   delegation, or complex parsing.
   -> See `references/handler-types.md`

3. **Pre-events block, post-events observe.** Pre-events (pre-stop,
   pre-tool-use, pre-command) can halt execution. Post-events (post-tool-use,
   post-file-write) can only inject context or trigger follow-up work.

4. **One hook, one concern.** Separate safety gates, formatting hooks, and
   context injectors into distinct atoms. Composability beats monoliths.

5. **Canonical events only.** Never invent event names. Use the 30+ events
   from the Tank specification. Adapters translate these to platform
   equivalents.
   -> See `references/hook-events-catalog.md`

## Quick-Start: Common Problems

### "Block the agent from stopping until tests pass"

1. Choose event: `pre-stop` (blocking).
2. Choose handler: JS (needs to run tests and parse output).
3. Wire the atom in `tank.json` with `"event": "pre-stop"`.
4. In the handler, call `ctx.continueWithMessage(...)` to block, or return
   to allow.
   -> See `references/worked-examples.md` (Pre-Stop Blocker)

### "Prevent dangerous shell commands"

1. Choose event: `pre-command`.
2. Choose handler: DSL with `block` action and `match` pattern.
3. Add the atom: `{ "kind": "hook", "event": "pre-command", "handler": { "type": "dsl", "actions": [{ "action": "block", "match": "rm -rf /", "reason": "Destructive command" }] } }`
   -> See `references/worked-examples.md` (Pre-Command Safety Gate)

### "Auto-format files after the agent writes them"

1. Choose event: `post-file-write`.
2. Choose handler: JS (needs to detect file type and run formatter).
3. In the handler, inspect the written file path, run the appropriate
   formatter, report results via context injection.
   -> See `references/worked-examples.md` (Post-File-Write Auto-Formatter)

### "Inject project context when a session starts"

1. Choose event: `session-created`.
2. Choose handler: DSL with `injectContext` action, or JS for dynamic context.
3. Provide the context string or file path in the action payload.
   -> See `references/worked-examples.md` (Session-Start Context Injector)

## Decision Trees

### Handler Type Selection

| Signal                                     | Use DSL          | Use JS/TS        |
| ------------------------------------------ | ---------------- | ---------------- |
| Simple string match (block/allow)          | Yes              | Overkill         |
| Static context injection                   | Yes              | Overkill         |
| Need to run shell commands                 | No               | Yes              |
| Need to parse structured output            | No               | Yes              |
| Need to delegate to another agent          | No               | Yes              |
| Need state across multiple invocations     | No               | Yes              |
| Portability across all adapters is critical | Yes              | Risky            |

### Event Category Selection

| Goal                                       | Event Category   | Key Events                        |
| ------------------------------------------ | ---------------- | --------------------------------- |
| Gate agent actions                         | Tool / Shell     | `pre-tool-use`, `pre-command`     |
| Quality checks before completion           | Stop             | `pre-stop`                        |
| React to file changes                      | File             | `post-file-write`, `file-edited`  |
| Inject context at start                    | Session          | `session-created`                 |
| Transform system prompts                   | System prompt    | `system-prompt-transform`         |
| Monitor subagent behavior                  | Subagent         | `subagent-tool-use`               |
| Enforce permissions                        | Permissions      | `permission-asked`                |

### Manifest Wiring

| Component       | Location in tank.json                  |
| --------------- | -------------------------------------- |
| Hook atom       | `atoms[]` with `kind: "hook"`          |
| Event binding   | `event` field on the hook atom         |
| DSL handler     | `handler: { type: "dsl", actions: [] }`|
| JS handler      | `handler: { type: "js", entry: "..." }`|
| Companion agent | Separate atom with `kind: "agent"`     |

## Reference Index

| File                              | Contents                                          |
| --------------------------------- | ------------------------------------------------- |
| `references/hook-events-catalog.md` | All 30+ canonical events with when-to-use guidance |
| `references/handler-types.md`       | DSL vs JS handlers, actions, canonical tool names  |
| `references/worked-examples.md`     | 4+ production hook patterns with full code         |
