# Worked Examples

Sources: Tank specification (AGENTS.md), production rule bundle patterns, OPA policy
examples, AWS SCP examples

Covers: four complete rule examples with full `tank.json` context -- a safety rule
blocking destructive commands, a code-style rule warning on bad patterns, an allow-list
rule restricting tool access, and a combined rule+instruction bundle.

## Example 1: Safety Rule -- Block Destructive Commands

### Problem

An agent running shell commands could accidentally delete critical files, force-push
to main, or drop database tables. These operations are irreversible.

### Design decisions

- **Event**: `pre-command` -- intercept before the command executes
- **Policy**: `block` -- irreversible harm justifies hard stop
- **Match**: target specific dangerous patterns, not broad categories
- **Reason**: explain the risk and suggest an alternative

### tank.json

```json
{
  "name": "@tank/safety-net",
  "version": "1.0.0",
  "description": "Block destructive shell commands. Prevents rm -rf, force push to main, and database drops.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "rule",
      "name": "no-rm-rf",
      "event": "pre-command",
      "policy": "block",
      "match": "rm -rf",
      "reason": "Recursive forced deletion is irreversible. Use trash-cli (`trash <path>`) for safe deletion, or remove specific files with `rm <file>` (no -rf)."
    },
    {
      "kind": "rule",
      "name": "no-force-push-main",
      "event": "pre-command",
      "policy": "block",
      "match": "push --force origin main",
      "reason": "Force-pushing to main rewrites shared history. Use `git push --force-with-lease` on feature branches only."
    },
    {
      "kind": "rule",
      "name": "no-drop-table",
      "event": "pre-command",
      "policy": "block",
      "match": "DROP TABLE",
      "reason": "Dropping tables is irreversible in production. Use migrations with rollback support instead."
    },
    {
      "kind": "rule",
      "name": "no-chmod-777",
      "event": "pre-command",
      "policy": "block",
      "match": "chmod 777",
      "reason": "World-writable permissions are a security vulnerability. Use specific permissions: chmod 755 for directories, chmod 644 for files."
    }
  ]
}
```

### Supporting SKILL.md (excerpt)

```markdown
# Safety Net

This bundle blocks destructive shell commands that could cause irreversible harm.

## Blocked Operations

| Command pattern      | Risk                        | Safe alternative              |
| -------------------- | --------------------------- | ----------------------------- |
| `rm -rf`             | Recursive deletion          | `trash <path>` (trash-cli)    |
| `push --force main`  | History rewrite on main     | `push --force-with-lease`     |
| `DROP TABLE`         | Permanent data loss         | Migration with rollback       |
| `chmod 777`          | World-writable permissions  | `chmod 755` or `chmod 644`    |

## Approved File Operations

- Delete single files: `rm <file>` (without -rf)
- Delete directories safely: `trash <directory>`
- Remove empty directories: `rmdir <directory>`
```

### Key takeaways

- Each rule targets one specific pattern -- not a broad category
- Reasons include the *why* (risk) and the *what instead* (alternative)
- The instruction atom provides a complete reference the agent can consult
- Four rules compose into a coherent safety policy

## Example 2: Code Style Rule -- Warn on `as any`

### Problem

A TypeScript project enforces strict typing. The agent should avoid `as any`
casts, but occasionally they are justified (e.g., third-party library gaps).
A block would be too aggressive; a warning educates without halting.

### Design decisions

- **Event**: `post-file-write` -- check content after the file is saved
- **Policy**: `warn` -- typing shortcuts are suboptimal but not dangerous
- **Match**: `as any` -- the specific TypeScript anti-pattern
- **Reason**: explain why it matters and what to do instead

### tank.json

```json
{
  "name": "@tank/typescript-strict",
  "version": "1.0.0",
  "description": "Warn on TypeScript anti-patterns in written files. Catches as-any casts, eslint-disable comments, and bare catch blocks.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "rule",
      "name": "no-as-any",
      "event": "post-file-write",
      "policy": "warn",
      "match": "as any",
      "reason": "Avoid `as any` -- it disables TypeScript safety. Use a proper type, generic, or `unknown` with a type guard. If unavoidable, add a // eslint-disable-next-line comment with justification."
    },
    {
      "kind": "rule",
      "name": "no-eslint-disable-blanket",
      "event": "post-file-write",
      "policy": "warn",
      "match": "eslint-disable ",
      "reason": "Blanket eslint-disable disables all rules for the file. Use eslint-disable-next-line with a specific rule name instead."
    },
    {
      "kind": "rule",
      "name": "no-bare-catch",
      "event": "post-file-write",
      "policy": "warn",
      "match": "catch (e) {}",
      "reason": "Empty catch blocks silently swallow errors. Log the error, rethrow, or handle it explicitly."
    }
  ]
}
```

### Key takeaways

- `warn` policy is appropriate because these are quality concerns, not safety risks
- Matching `post-file-write` catches the pattern after the agent writes code
- Each reason suggests a concrete alternative
- The match `eslint-disable ` (with trailing space) avoids matching `eslint-disable-next-line`

## Example 3: Allow-List Rule -- Restrict Tool Access

### Problem

A read-only audit agent should only use `read`, `grep`, and `glob`. All other
tools -- especially `write`, `edit`, `bash` -- must be blocked. This requires
an allow-list pattern with a default-deny.

### Design decisions

- **Event**: `pre-tool-use` -- intercept before any tool invocation
- **Policy**: `allow` for approved tools, `block` as catch-all deny
- **Match**: canonical tool names from the Tank spec
- **Reason**: explain the audit-only restriction

### tank.json

```json
{
  "name": "@tank/audit-only",
  "version": "1.0.0",
  "description": "Restrict agent to read-only tools. Blocks write, edit, bash, and all other tools except read, grep, and glob.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "rule",
      "name": "allow-read",
      "event": "pre-tool-use",
      "policy": "allow",
      "match": "read",
      "reason": "Read is approved for audit operations"
    },
    {
      "kind": "rule",
      "name": "allow-grep",
      "event": "pre-tool-use",
      "policy": "allow",
      "match": "grep",
      "reason": "Grep is approved for audit operations"
    },
    {
      "kind": "rule",
      "name": "allow-glob",
      "event": "pre-tool-use",
      "policy": "allow",
      "match": "glob",
      "reason": "Glob is approved for audit operations"
    },
    {
      "kind": "rule",
      "name": "allow-lsp",
      "event": "pre-tool-use",
      "policy": "allow",
      "match": "lsp",
      "reason": "LSP is approved for code navigation during audit"
    },
    {
      "kind": "rule",
      "name": "deny-all-other-tools",
      "event": "pre-tool-use",
      "policy": "block",
      "reason": "This agent operates in audit-only mode. Only read, grep, glob, and lsp tools are permitted. Do not attempt to modify files, run commands, or use other tools."
    }
  ]
}
```

### How the allow-list works

1. Agent invokes `read` -- matches `allow-read` rule, operation proceeds
2. Agent invokes `bash` -- no allow rule matches, hits `deny-all-other-tools`, blocked
3. Agent invokes `write` -- no allow rule matches, hits catch-all block, blocked

The catch-all block rule has no `match` field, so it fires for every `pre-tool-use`
event. The specific allow rules override it for approved tools because they have
more specific matches.

### Key takeaways

- Allow-list requires explicit allow rules + a catch-all block
- The catch-all block has no `match` -- it catches everything
- Allow rules use canonical tool names from the Tank spec
- The catch-all reason explains the restriction and sets expectations

## Example 4: Combined Bundle -- Safety + Style + Education

### Problem

A team wants a comprehensive policy for their Node.js project:
- Block dangerous operations (safety)
- Warn on code quality issues (style)
- Educate the agent about project conventions (instruction)

This example demonstrates the layered defense pattern.

### tank.json

```json
{
  "name": "@tank/node-project-policy",
  "version": "1.0.0",
  "description": "Comprehensive policy for Node.js projects. Blocks dangerous commands, warns on code quality issues, and educates the agent on project conventions.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "rule",
      "name": "no-rm-rf",
      "event": "pre-command",
      "policy": "block",
      "match": "rm -rf",
      "reason": "Use trash-cli for safe deletion"
    },
    {
      "kind": "rule",
      "name": "no-npm-install-global",
      "event": "pre-command",
      "policy": "block",
      "match": "npm install -g",
      "reason": "Global installs pollute the system. Use npx for one-off tools or add to devDependencies."
    },
    {
      "kind": "rule",
      "name": "no-force-push",
      "event": "pre-command",
      "policy": "block",
      "match": "push --force",
      "reason": "Use --force-with-lease to prevent overwriting others' work"
    },
    {
      "kind": "rule",
      "name": "warn-console-log",
      "event": "post-file-write",
      "policy": "warn",
      "match": "console.log(",
      "reason": "Remove console.log before committing. Use the project logger (src/lib/logger.ts) for production logging."
    },
    {
      "kind": "rule",
      "name": "warn-todo-comment",
      "event": "post-file-write",
      "policy": "warn",
      "match": "// TODO",
      "reason": "TODO comments indicate unfinished work. Complete the task or create a GitHub issue and reference it: // TODO(#123): description"
    },
    {
      "kind": "rule",
      "name": "warn-any-cast",
      "event": "post-file-write",
      "policy": "warn",
      "match": "as any",
      "reason": "Avoid `as any` -- use proper types or `unknown` with type guards"
    },
    {
      "kind": "rule",
      "name": "warn-env-direct",
      "event": "post-file-write",
      "policy": "warn",
      "match": "process.env.",
      "reason": "Access environment variables through src/config.ts, not directly via process.env. This centralizes validation and provides type safety."
    }
  ]
}
```

### Supporting SKILL.md (full example)

```markdown
# Node.js Project Policy

This bundle enforces safety constraints and quality standards for this project.

## Safety Rules (Enforced -- agent is blocked)

- No `rm -rf` -- use trash-cli
- No global npm installs -- use npx or devDependencies
- No force push -- use --force-with-lease

## Quality Rules (Advisory -- agent is warned)

- No `console.log` -- use src/lib/logger.ts
- No bare TODO comments -- link to GitHub issues
- No `as any` -- use proper types
- No direct process.env access -- use src/config.ts

## Project Conventions

- Package manager: pnpm (not npm or yarn)
- Test runner: vitest
- Linter: biome (not eslint)
- Logger: src/lib/logger.ts (pino-based)
- Config: src/config.ts (zod-validated env vars)
```

### Key takeaways

- Three block rules for safety, four warn rules for quality
- The instruction atom documents both the rules and broader project conventions
- The agent gets education (instruction) and enforcement (rules) together
- Block reasons suggest specific alternatives; warn reasons explain the project pattern
- Rules are named for easy identification in logs and debugging

## Summary: Rule Design Checklist

| Step | Action                                                       |
| ---- | ------------------------------------------------------------ |
| 1    | Identify the constraint (what must not / should not happen)  |
| 2    | Choose the event (when in the lifecycle to check)            |
| 3    | Choose the policy (block for danger, warn for quality)       |
| 4    | Write the match pattern (narrow, specific, portable)         |
| 5    | Write the reason (explain risk + suggest alternative)        |
| 6    | Add an instruction atom (educate the agent on the policy)    |
| 7    | Place rules in a `bundles/` directory with `atoms` array     |
| 8    | Test each rule by deliberately triggering its condition      |
| 9    | Review for false positives and over-restriction              |
| 10   | Ship as warn first, escalate to block after validation       |
