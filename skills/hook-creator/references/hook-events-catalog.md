# Hook Events Catalog

Sources: Tank specification (AGENTS.md), adapter translation patterns, quality-gate reference implementation

Covers: every canonical Tank hook event organized by category, with timing semantics, blocking behavior, and when-to-use guidance.

## Event Timing Model

Every hook event fires at a specific point in the agent lifecycle. The naming
convention signals timing:

| Prefix/Suffix  | Timing                        | Can Block? |
| -------------- | ----------------------------- | ---------- |
| `pre-*`        | Before the action executes    | Yes        |
| `post-*`       | After the action completes    | No         |
| No prefix      | At the moment the event fires | Varies     |

Pre-events receive the proposed action and can block, rewrite, or allow it.
Post-events receive the completed result and can only observe or inject
follow-up context.

## Complete Event Reference

### Tool Events

| Event           | Blocks? | Context                            | Use When                                         |
| --------------- | ------- | ---------------------------------- | ------------------------------------------------ |
| `pre-tool-use`  | Yes     | Tool name, arguments, target paths | Restricting tool access, blocking dangerous tools |
| `post-tool-use` | No      | Tool name, arguments, result       | Auditing usage, triggering follow-up actions      |

`pre-tool-use` is the broadest gate — it fires for every tool invocation
(read, write, edit, grep, glob, lsp, etc.). Use canonical tool names in match
patterns. Block the agent from using `write` on production configs, or
restrict `bash` to a safe allowlist.

`post-tool-use` cannot block. Use it to log results, inject summaries of
findings into context, or update state for later hooks.

### File Events

| Event                  | Blocks? | Context                                | Use When                                   |
| ---------------------- | ------- | -------------------------------------- | ------------------------------------------ |
| `pre-file-read`        | Yes     | File path, read options                | Preventing access to sensitive files       |
| `post-file-read`       | No      | File path, file contents               | Redacting secrets, logging access          |
| `pre-file-write`       | Yes     | File path, proposed content            | Protecting files/directories from writes   |
| `post-file-write`      | No      | File path, written content             | Auto-formatting, triggering builds         |
| `file-edited`          | No      | File path, edit diff/hunks             | Tracking incremental changes, running lint |
| `file-watcher-updated` | No      | Changed paths, change type (add/mod/del)| Reacting to external changes (user edits) |

`pre-file-read` and `pre-file-write` are security boundaries. Block reads of
`.env`, secrets, or credentials. Block writes to `package-lock.json`,
`generated/`, or `dist/`.

`post-file-write` is the auto-formatter hook point. Detect file extension,
run the appropriate formatter. See `references/worked-examples.md`.

`file-watcher-updated` fires for changes made outside the agent (user saves
in their editor, another process modifies files). Use it to refresh context
or re-run validation.

### Shell Events

| Event          | Blocks? | Context                              | Use When                                      |
| -------------- | ------- | ------------------------------------ | --------------------------------------------- |
| `pre-command`  | Yes     | Command string, working directory    | Blocking dangerous commands, enforcing lists   |
| `post-command` | No      | Command, exit code, stdout, stderr   | Capturing test results, detecting failures     |

`pre-command` is the primary safety gate for shell execution. Use DSL
handlers for simple blocklists/allowlists. See `references/worked-examples.md`
for the Pre-Command Safety Gate pattern.

`post-command` captures output. Parse test results, detect failures, inject
error context for the agent's next decision.

### MCP Events

| Event              | Blocks? | Context                            | Use When                                    |
| ------------------ | ------- | ---------------------------------- | ------------------------------------------- |
| `pre-mcp-tool-use` | Yes     | MCP server name, tool, arguments   | Restricting MCP tool access, auditing calls |
| `post-mcp-tool-use`| No      | MCP server name, tool, result      | Processing responses, caching results       |

MCP events mirror tool events but apply specifically to MCP server
invocations. Use `pre-mcp-tool-use` to block external API calls or restrict
which MCP tools the agent can invoke.

### Session Events

| Event             | Blocks? | Context                        | Use When                                     |
| ----------------- | ------- | ------------------------------ | -------------------------------------------- |
| `session-created` | No      | Session ID, initial config     | Injecting startup context, initializing state |
| `session-updated` | No      | Session ID, updated properties | Tracking session evolution, syncing state     |
| `session-idle`    | No      | Session ID, idle duration      | Cleanup, auto-save, resource management      |
| `session-error`   | No      | Session ID, error details      | Error recovery, alerting, retry logic        |
| `session-deleted` | No      | Session ID                     | Final cleanup, persisting state              |

`session-created` is the bootstrap hook. Inject project rules, persona
context, or environment-specific configuration at session start. See
`references/worked-examples.md` for the Session-Start Context Injector.

`session-idle` fires after a platform-defined idle threshold. Use for
auto-saving progress or releasing resources.

### Stop Events

| Event      | Blocks? | Context                                     | Use When                                     |
| ---------- | ------- | ------------------------------------------- | -------------------------------------------- |
| `pre-stop` | Yes     | Session ID, modified files, session history  | Quality gates, completion checklists, reviews |

`pre-stop` is the most powerful blocking event. It fires when the agent
attempts to finish. Call `ctx.continueWithMessage(...)` to block the stop and
send the agent back to work with instructions on what to fix.

The canonical implementation is `bundles/quality-gate/hooks/quality-gate.ts`:
it delegates to a code-reviewer subagent, parses review output by severity,
and blocks if critical or high issues exist. The hook re-runs automatically
after fixes. See `references/worked-examples.md`.

### Task Events

| Event           | Blocks? | Context                          | Use When                                        |
| --------------- | ------- | -------------------------------- | ----------------------------------------------- |
| `task-start`    | No      | Task ID, description             | Initializing task state, logging                |
| `task-resume`   | No      | Task ID, previous state          | Restoring context after interruption            |
| `task-complete` | No      | Task ID, status, artifacts       | Aggregating results, triggering downstream tasks |
| `task-cancel`   | No      | Task ID, cancellation reason     | Cleanup, rollback, logging                      |

Task events track the lifecycle of individual tasks within a session. Use
`task-start` to set up task-specific state. Use `task-complete` to trigger
CI, update project boards, or aggregate results.

### Conversation Events

| Event             | Blocks? | Context                      | Use When                                       |
| ----------------- | ------- | ---------------------------- | ---------------------------------------------- |
| `pre-user-prompt` | Yes     | User message text            | Input validation, prompt rewriting              |
| `post-response`   | No      | Agent response text          | Response auditing, logging, analytics           |
| `message-updated` | No      | Message ID, old/new content  | Tracking edits, maintaining conversation state  |
| `message-removed` | No      | Message ID, removed content  | Cleanup, redaction tracking                     |

`pre-user-prompt` can rewrite user input before the agent processes it.
Sanitize input, expand abbreviations, or inject additional hints.

`post-response` is the audit point. Log responses, check for sensitive output
leakage, or trigger analytics.

### System Prompt Events

| Event                    | Blocks? | Context                  | Use When                                 |
| ------------------------ | ------- | ------------------------ | ---------------------------------------- |
| `system-prompt-transform`| No*     | Current system prompt    | Injecting dynamic rules, persona switches |

*Cannot block, but can rewrite the system prompt content.

Use to append project-specific rules, modify agent tone, or inject dynamic
constraints based on branch, framework, or session state.

### Context Events

| Event                  | Blocks? | Context                           | Use When                                      |
| ---------------------- | ------- | --------------------------------- | --------------------------------------------- |
| `pre-context-compact`  | Yes     | Context size, compaction strategy  | Preserving critical context from being removed |
| `post-context-compact` | No      | New size, what was removed        | Re-injecting key facts that were lost          |

Context compaction happens when the context window fills up. Use
`pre-context-compact` to mark sections as non-compactable. Use
`post-context-compact` to re-inject critical information.

### Permission Events

| Event               | Blocks? | Context                           | Use When                                 |
| ------------------- | ------- | --------------------------------- | ---------------------------------------- |
| `permission-asked`  | Yes     | Permission type, resource, reason | Auto-approving known-safe permissions    |
| `permission-replied`| No      | Permission type, user decision    | Logging decisions, adapting behavior     |

Use `permission-asked` to auto-allow safe patterns (e.g., always allow
reading test files) or auto-block risky requests without bothering the user.

### IDE/LSP Events

| Event             | Blocks? | Context                             | Use When                                   |
| ----------------- | ------- | ----------------------------------- | ------------------------------------------ |
| `lsp-diagnostics` | No      | File path, diagnostics, severity    | Auto-fixing lint errors, injecting context |
| `lsp-updated`     | No      | Updated scope, indexing status      | Waiting for LSP readiness before checks    |

`lsp-diagnostics` fires when the language server reports new errors or
warnings. Use it to inject error context or trigger auto-fix passes.

### Subagent Events

| Event              | Blocks? | Context                            | Use When                                   |
| ------------------ | ------- | ---------------------------------- | ------------------------------------------ |
| `subagent-start`   | No      | Subagent name, role, prompt        | Auditing delegation, logging usage         |
| `subagent-complete` | No     | Subagent name, output, duration    | Aggregating results, quality checks        |
| `subagent-tool-use` | Yes    | Subagent name, tool, arguments     | Restricting subagent tool access           |

`subagent-tool-use` is a security boundary. Block write tools for read-only
subagents. Ensure reviewer agents cannot modify code.

### Environment Events

| Event       | Blocks? | Context                                  | Use When                                    |
| ----------- | ------- | ---------------------------------------- | ------------------------------------------- |
| `shell-env` | No      | Environment variables, shell, working dir | Detecting project context, setting up env   |

Fires when the shell environment initializes or changes. Use to detect the
project framework, inject framework-specific rules, or configure the agent's
working environment.

### Workflow Events

| Event                  | Blocks? | Context                             | Use When                                    |
| ---------------------- | ------- | ----------------------------------- | ------------------------------------------- |
| `todo-updated`         | No      | Updated todo items, changes         | Tracking progress, syncing external tools   |
| `installation-updated` | No      | Package changes, install operations | Auditing deps, running security scans       |

`installation-updated` fires when dependencies change. Use it to run
`npm audit`, check for known vulnerabilities, or log dependency changes.

## Quick-Reference: All Events by Blocking Capability

### Blocking Events (can halt execution)

| Event                  | Category     | Primary Use Case                        |
| ---------------------- | ------------ | --------------------------------------- |
| `pre-tool-use`         | Tool         | Restrict which tools the agent can use  |
| `pre-file-read`        | File         | Prevent access to sensitive files       |
| `pre-file-write`       | File         | Protect directories from modification   |
| `pre-command`          | Shell        | Block dangerous shell commands          |
| `pre-mcp-tool-use`     | MCP          | Restrict external MCP tool access       |
| `pre-stop`             | Stop         | Quality gates before completion         |
| `pre-user-prompt`      | Conversation | Input validation and rewriting          |
| `pre-context-compact`  | Context      | Preserve critical context from removal  |
| `permission-asked`     | Permissions  | Auto-approve or auto-deny permissions   |
| `subagent-tool-use`    | Subagent     | Restrict subagent tool access           |

### Non-Blocking Events (observe and react only)

| Event                  | Category      | Primary Use Case                        |
| ---------------------- | ------------- | --------------------------------------- |
| `post-tool-use`        | Tool          | Audit tool usage, inject follow-up      |
| `post-file-read`       | File          | Redact secrets, log file access         |
| `post-file-write`      | File          | Auto-format, trigger builds             |
| `file-edited`          | File          | Track incremental changes               |
| `file-watcher-updated` | File          | React to external file changes          |
| `post-command`         | Shell         | Parse test results, detect failures     |
| `post-mcp-tool-use`    | MCP           | Process MCP responses, cache results    |
| `session-created`      | Session       | Inject startup context                  |
| `session-updated`      | Session       | Track session state changes             |
| `session-idle`         | Session       | Auto-save, resource cleanup             |
| `session-error`        | Session       | Error recovery, alerting                |
| `session-deleted`      | Session       | Final cleanup, persist state            |
| `task-start`           | Task          | Initialize task state                   |
| `task-resume`          | Task          | Restore context after interruption      |
| `task-complete`        | Task          | Aggregate results, trigger downstream   |
| `task-cancel`          | Task          | Cleanup, rollback                       |
| `post-response`        | Conversation  | Audit responses, analytics              |
| `message-updated`      | Conversation  | Track edits, maintain state             |
| `message-removed`      | Conversation  | Cleanup, redaction tracking             |
| `system-prompt-transform`| System prompt| Dynamic rules, persona switches        |
| `post-context-compact` | Context       | Re-inject lost critical context         |
| `permission-replied`   | Permissions   | Log decisions, adapt behavior           |
| `lsp-diagnostics`      | IDE/LSP       | Auto-fix errors, inject context         |
| `lsp-updated`          | IDE/LSP       | Wait for LSP readiness                  |
| `subagent-start`       | Subagent      | Audit delegation, log usage             |
| `subagent-complete`    | Subagent      | Aggregate subagent results              |
| `shell-env`            | Environment   | Detect project type, configure env      |
| `todo-updated`         | Workflow      | Track progress, sync tools              |
| `installation-updated` | Workflow      | Audit dependencies, security scans      |

## Event Composition Patterns

### Layered Security

Combine multiple blocking events to create defense in depth:

1. `pre-command` — block dangerous shell commands at the command level.
2. `pre-file-write` — block writes to protected directories as a backup.
3. `pre-stop` — run a final review to catch anything that slipped through.

### Observe-Then-Act

Chain a post-event with state that a pre-event reads later:

1. `post-file-write` — record which files were written.
2. `pre-stop` — use the recorded file list to scope the quality review.

This is the pattern used by `bundles/quality-gate/hooks/quality-gate.ts`.

### Bootstrap-and-Monitor

Combine session lifecycle events:

1. `session-created` — inject project context and rules.
2. `lsp-diagnostics` — auto-fix type errors during the session.
3. `pre-stop` — verify no regressions before allowing completion.

### Subagent Sandboxing

Restrict subagent capabilities:

1. `subagent-tool-use` — block `write`, `edit`, and `bash` for reviewer
   agents. Allow only `read`, `grep`, `glob`, and `lsp`.
2. `subagent-complete` — validate subagent output format before injecting
   into parent context.
