# Worked Hook Examples

Sources: Tank specification (AGENTS.md), quality-gate reference implementation (bundles/quality-gate/hooks/quality-gate.ts), production adapter patterns

Covers: four complete hook implementations with full tank.json wiring, handler code, and rationale. Each example targets a different event category and handler type.

## Example 1: Pre-Stop Quality Blocker (JS Handler)

### Problem

The agent finishes work but leaves behind bugs, missing error handling, or
security issues. There is no checkpoint before completion.

### Solution

A `pre-stop` hook that delegates to a code-reviewer subagent, parses the
review output, and blocks the stop if critical or high issues exist.

### tank.json

```json
{
  "name": "@tank/quality-gate",
  "version": "1.0.0",
  "description": "Blocks agent completion until code review passes.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "hook",
      "name": "quality-gate",
      "event": "pre-stop",
      "handler": {
        "type": "js",
        "entry": "./hooks/quality-gate.ts"
      }
    },
    {
      "kind": "agent",
      "name": "code-reviewer",
      "role": "Senior code reviewer. Review ONLY the modified files/hunks. Categorize every issue as critical, high, medium, or low.",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    }
  ]
}
```

### Handler: hooks/quality-gate.ts

Key architectural decisions:

1. **Filter changed files.** Only review code files that were actually
   modified. Ignore config, docs, and excluded paths.
2. **Delegate to a named subagent.** The `code-reviewer` agent is declared
   as a companion atom and invoked via `ctx.delegateToAgent`.
3. **Parse structured output.** The reviewer outputs one line per issue in
   `[SEVERITY] - file:line - description` format. The handler parses this
   into typed `ReviewIssue` objects.
4. **Block on critical/high.** Call `ctx.continueWithMessage(...)` with
   the formatted issue list. The agent receives this as a new prompt and
   must fix the issues before trying to stop again.
5. **Track re-runs.** A module-level `Map` counts how many times the gate
   has run per session. On re-runs, the prompt asks the agent to verify
   previous fixes rather than do a full review.

```typescript
const CODE_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx", ".py", ".go"]);

interface FileChange {
  path: string;
  hunks?: string;
}

interface ReviewIssue {
  file: string;
  line?: number;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
}

function hasCodeChanges(files: FileChange[]): boolean {
  return files.some((f) => {
    const ext = f.path.slice(f.path.lastIndexOf("."));
    return CODE_EXTENSIONS.has(ext);
  });
}

function parseReviewOutput(output: string): ReviewIssue[] {
  const issues: ReviewIssue[] = [];
  for (const line of output.split("\n")) {
    const match = line.match(
      /^\[?(critical|high|medium|low)\]?\s*[-:]\s*(?:(.+?):(\d+)\s*[-:]\s*)?(.+)/i,
    );
    if (match) {
      issues.push({
        severity: match[1].toLowerCase() as ReviewIssue["severity"],
        file: match[2] ?? "unknown",
        line: match[3] ? parseInt(match[3], 10) : undefined,
        message: match[4].trim(),
      });
    }
  }
  return issues;
}

const _runCount = new Map<string, number>();

export default async function handler(event, ctx): Promise<void> {
  const sessionId = event.properties?.sessionID as string;
  if (!sessionId) return;

  // Gather changed files
  let changedFiles: FileChange[] = [];
  try {
    const output = await ctx.$`git diff --name-only HEAD`.text();
    changedFiles = output.split("\n").filter(Boolean).map((p) => ({ path: p }));
  } catch {
    return;
  }

  if (!hasCodeChanges(changedFiles)) return;

  const run = (_runCount.get(sessionId) ?? 0) + 1;
  _runCount.set(sessionId, run);

  // Build review prompt
  const fileList = changedFiles.map((f) => `- ${f.path}`).join("\n");
  const prompt = run === 1
    ? `Review these files for bugs and security issues:\n${fileList}`
    : `Re-check #${run}: are previous critical/high issues fixed? ${fileList}`;

  // Delegate to subagent via session prompt
  await ctx.client.session.prompt({
    path: { id: sessionId },
    body: { parts: [{ type: "text", text: prompt }] },
  });
}
```

The full production implementation is at
`bundles/quality-gate/hooks/quality-gate.ts` (277 lines) with additional
features: excluded path filtering, diff content in first-run prompts, and
formatted issue reporting with blocking/non-blocking categorization.

## Example 2: Post-File-Write Auto-Formatter (JS Handler)

### Problem

The agent writes TypeScript or CSS files but does not run the project's
formatter. Code style drifts from the team standard.

### Solution

A `post-file-write` hook that detects the file type and runs the appropriate
formatter.

### tank.json

```json
{
  "name": "@tank/auto-format",
  "version": "1.0.0",
  "description": "Auto-formats files after the agent writes them.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": true
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "hook",
      "name": "auto-format",
      "event": "post-file-write",
      "handler": {
        "type": "js",
        "entry": "./hooks/auto-format.ts"
      }
    }
  ]
}
```

Note: `subprocess: true` because the hook runs external formatters.

### Handler: hooks/auto-format.ts

```typescript
const FORMATTERS: Record<string, string> = {
  ".ts": "npx prettier --write",
  ".tsx": "npx prettier --write",
  ".js": "npx prettier --write",
  ".jsx": "npx prettier --write",
  ".css": "npx prettier --write",
  ".scss": "npx prettier --write",
  ".json": "npx prettier --write",
  ".md": "npx prettier --write",
  ".py": "python3 -m black",
  ".go": "gofmt -w",
  ".rs": "rustfmt",
};

export default async function handler(event, ctx): Promise<void> {
  const filePath = event.properties?.filePath as string;
  if (!filePath) return;

  const ext = filePath.slice(filePath.lastIndexOf("."));
  const formatter = FORMATTERS[ext];
  if (!formatter) return;

  try {
    await ctx.$`${formatter} ${filePath}`.text();
  } catch {
    // Formatter not installed or failed — do not block the agent.
    // Post-events cannot block, so this is purely best-effort.
  }
}
```

Key points:
- Post-events cannot block. If the formatter fails, the agent continues.
- The hook runs the project's formatter, not its own. It respects
  `.prettierrc`, `pyproject.toml`, etc.
- Add more extensions and formatters as needed.

## Example 3: Pre-Command Safety Gate (DSL Handler)

### Problem

The agent runs shell commands that could be destructive (deleting files,
force-pushing, modifying system state).

### Solution

A `pre-command` hook using a DSL handler with an allowlist pattern.

### tank.json

```json
{
  "name": "@tank/command-safety",
  "version": "1.0.0",
  "description": "Blocks dangerous shell commands, allows safe ones.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "hook",
      "event": "pre-command",
      "handler": {
        "type": "dsl",
        "actions": [
          { "action": "block", "match": "rm -rf /", "reason": "Cannot delete root filesystem" },
          { "action": "block", "match": "rm -rf ~", "reason": "Cannot delete home directory" },
          { "action": "block", "match": "sudo", "reason": "Elevated privileges not permitted" },
          { "action": "block", "match": "git push --force", "reason": "Force push blocked. Use --force-with-lease instead" },
          { "action": "block", "match": "chmod 777", "reason": "World-writable permissions not allowed" },
          { "action": "block", "match": "curl | sh", "reason": "Pipe-to-shell execution blocked" },
          { "action": "block", "match": "curl | bash", "reason": "Pipe-to-shell execution blocked" },
          { "action": "rewrite", "match": "python ", "to": "python3 " }
        ]
      }
    }
  ]
}
```

Key points:
- No JS needed. Pure declarative safety rules.
- Actions evaluate top-to-bottom. First match wins.
- The `rewrite` action silently transforms `python` to `python3`.
- Unmatched commands are allowed by default.
- Portable across all adapters — no runtime dependency.

### Strict Allowlist Variant

For high-security environments, invert the pattern — allow only known-safe
commands and block everything else:

```json
{
  "actions": [
    { "action": "allow", "match": "npm test" },
    { "action": "allow", "match": "npm run lint" },
    { "action": "allow", "match": "npm run build" },
    { "action": "allow", "match": "npm run typecheck" },
    { "action": "allow", "match": "git status" },
    { "action": "allow", "match": "git diff" },
    { "action": "allow", "match": "git log" },
    { "action": "allow", "match": "git add" },
    { "action": "allow", "match": "git commit" },
    { "action": "block", "match": "*", "reason": "Command not in allowlist. Only npm scripts and safe git commands permitted." }
  ]
}
```

The wildcard `*` at the end catches everything not explicitly allowed.

## Example 4: Session-Start Context Injector (DSL Handler)

### Problem

The agent starts a session without knowledge of the project's conventions,
architecture decisions, or team rules.

### Solution

A `session-created` hook that injects project context at session start.

### tank.json

```json
{
  "name": "@tank/project-context",
  "version": "1.0.0",
  "description": "Injects project rules and context when a session starts.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "hook",
      "event": "session-created",
      "handler": {
        "type": "dsl",
        "actions": [
          {
            "action": "injectContext",
            "content": "Project rules:\n- Use TypeScript strict mode.\n- All functions must have JSDoc comments.\n- No default exports — use named exports only.\n- Test files colocated with source: `foo.ts` -> `foo.test.ts`.\n- Use pnpm, not npm or yarn.\n- Commit messages follow Conventional Commits.\n- Never modify files in `generated/` — they are auto-generated."
          }
        ]
      }
    }
  ]
}
```

Key points:
- DSL is sufficient for static context injection.
- The `content` field supports multi-line strings.
- The injected context becomes part of the agent's working knowledge for the
  entire session.
- Combine with `system-prompt-transform` for dynamic context that adapts
  based on the session state.

### Dynamic Variant (JS Handler)

When context depends on the project state (detected framework, branch name,
recent changes), use a JS handler:

```typescript
export default async function handler(event, ctx): Promise<void> {
  // Detect project type
  let framework = "unknown";
  try {
    const pkg = await ctx.$`cat package.json 2>/dev/null`.text();
    if (pkg.includes("next")) framework = "Next.js";
    else if (pkg.includes("angular")) framework = "Angular";
    else if (pkg.includes("vue")) framework = "Vue";
  } catch {}

  // Detect branch
  let branch = "unknown";
  try {
    branch = (await ctx.$`git branch --show-current`.text()).trim();
  } catch {}

  // Build dynamic context
  const context = [
    `Detected framework: ${framework}`,
    `Current branch: ${branch}`,
    branch.startsWith("hotfix/")
      ? "HOTFIX BRANCH: Focus on minimal, targeted changes only."
      : "Standard branch: normal development rules apply.",
  ].join("\n");

  // Inject via session prompt
  const sessionId = event.properties?.sessionID as string;
  if (sessionId) {
    await ctx.client.session.prompt({
      path: { id: sessionId },
      body: { parts: [{ type: "text", text: context }] },
    });
  }
}
```

## Wiring Patterns Summary

| Example                  | Event            | Handler | Companion Atoms | Subprocess |
| ------------------------ | ---------------- | ------- | --------------- | ---------- |
| Pre-Stop Quality Blocker | `pre-stop`       | JS      | `agent`         | No         |
| Post-File-Write Formatter| `post-file-write`| JS      | None            | Yes        |
| Pre-Command Safety Gate  | `pre-command`     | DSL     | None            | No         |
| Session-Start Injector   | `session-created`| DSL     | None            | No         |

## Common Mistakes

### Blocking in post-events

Post-events (`post-tool-use`, `post-file-write`, `post-command`) cannot block.
Calling `ctx.continueWithMessage` in a post-event handler is a no-op. If you
need to block, use the corresponding pre-event.

### Missing companion agent atom

If a JS handler calls `ctx.delegateToAgent("reviewer", ...)` but no
`kind: "agent"` atom named `"reviewer"` exists in the same `tank.json`, the
delegation fails silently. Always declare companion agents.

### Over-broad match patterns

A DSL action with `"match": "rm"` blocks `rm file.txt`, `npm run dev`
(contains "rm" in "run"), and `git format-patch`. Use specific patterns:
`"match": "rm -rf"` or regex `"match": "/^rm\\s/"`.

### Forgetting subprocess permission

JS handlers that run shell commands via `ctx.$` require
`"subprocess": true` in the package permissions. Without it, the adapter
may reject the command.

### Stateful DSL expectations

DSL handlers are stateless. Each invocation evaluates actions independently.
If you need to track state (e.g., "block after 3 failures"), migrate to a
JS handler.

### Inventing event names

Only use canonical event names from the Tank specification. Custom event names
are not supported. If you need a custom trigger, use a combination of
existing events with conditional logic in a JS handler.
See `references/hook-events-catalog.md` for the complete list.
