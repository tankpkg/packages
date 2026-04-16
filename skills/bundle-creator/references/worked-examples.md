# Worked Bundle Examples

Sources: Tank Contributing Standard (AGENTS.md), @tank/quality-gate bundle
(canonical reference), Tank registry conventions (2025-2026).

Covers: three complete bundle walkthroughs that demonstrate atom interplay,
handler wiring, permission scoping, and directory layout. Each example
includes the full tank.json, rationale for atom choices, and the data
flow between atoms.

## Example 1: Quality Gate (Hook + Agent + Instruction)

This is the canonical Tank bundle at `bundles/quality-gate/`. It
automatically reviews code before the agent stops and blocks on critical
or high severity issues.

### Directory Layout

```
bundles/quality-gate/
  tank.json
  SKILL.md
  hooks/quality-gate.ts
  references/review-criteria.md
```

### tank.json

```json
{
  "name": "@tank/quality-gate",
  "version": "1.0.0",
  "description": "Automatic code review before the agent stops...",
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
      "handler": { "type": "js", "entry": "./hooks/quality-gate.ts" }
    },
    {
      "kind": "agent",
      "name": "code-reviewer",
      "role": "Senior code reviewer. Review ONLY the modified files/hunks provided. Categorize every issue as critical, high, medium, or low. Focus on bugs, security, correctness, and maintainability. Do NOT review style/formatting. Be concise: one line per issue with file, line, severity, and what's wrong.",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Why These Atoms

**Hook (pre-stop):** The agent is about to finish. The hook intercepts
this moment to check if code files were modified. If yes, it delegates
to the reviewer. If the reviewer finds blocking issues, the hook calls
`continueWithMessage()` to force the agent to keep working.

**Agent (code-reviewer):** A constrained sub-agent with readonly access.
It receives the file list and diff from the hook, reviews changes, and
outputs one line per issue in a structured format. The `fast` model tier
keeps review time low. The `readonly: true` flag prevents the reviewer
from modifying files — it only observes.

**Instruction (SKILL.md):** Provides severity definitions (what counts
as critical vs high vs medium vs low), the list of code file extensions
that trigger review, and the flow diagram. Without this, the agent
would not know the severity taxonomy.

### Data Flow

```
1. Agent finishes work
2. pre-stop event fires
3. Hook handler executes:
   a. Runs `git diff --name-only` to get changed files
   b. Filters for code extensions (.ts, .py, .go, etc.)
   c. If no code files changed -> allow stop
   d. If code files changed -> build review prompt with diff
   e. Delegate to "code-reviewer" agent with the prompt
4. code-reviewer agent:
   a. Reads modified files using its tools (read, grep, glob, lsp)
   b. Outputs structured issues: [SEVERITY] file:line - description
5. Hook parses the output:
   a. If critical/high found -> block stop, inject fix instructions
   b. If only medium/low -> allow stop, report for awareness
6. If blocked, agent fixes issues, then pre-stop fires again (loop)
```

### Permission Rationale

- **Network:** No external calls needed. Review is local.
- **Filesystem read:** `["**/*"]` because the reviewer needs to read any
  project file.
- **Filesystem write:** `[]` because the reviewer is readonly. Fixes are
  done by the main agent, not by the bundle.
- **Subprocess:** `false` because git commands run through the agent's
  existing shell capabilities, not through the hook spawning processes.

## Example 2: Guardrails (Rule + Instruction)

A lightweight safety bundle that blocks dangerous shell commands without
any custom code.

### Directory Layout

```
bundles/guardrails/
  tank.json
  SKILL.md
```

No hooks directory needed — rules are declarative.

### tank.json

```json
{
  "name": "@tank/guardrails",
  "version": "1.0.0",
  "description": "Block dangerous shell commands and file operations.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "rule",
      "event": "pre-command",
      "policy": "block",
      "reason": "Destructive commands are prohibited in this workspace"
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Why These Atoms

**Rule (pre-command, block):** Declaratively blocks dangerous commands
before they execute. No code to write, test, or maintain. The runtime
evaluates the rule whenever a shell command is about to run.

**Instruction (SKILL.md):** Explains to the agent which commands are
considered dangerous and why, so it can self-correct before hitting the
rule. The instruction includes the rationale (e.g., "force push to main
destroys shared history") so the agent understands the constraint instead
of just being blocked.

### Why Not a Hook

A hook could achieve the same result but requires:
- A TypeScript file in `hooks/`
- Pattern matching logic
- Error handling
- Testing

The rule achieves the same outcome declaratively. Prefer rules when the
logic is a simple match-and-block without conditional branching.

### When Rules Are Not Enough

Rules become insufficient when you need:
- Conditional blocking (block only on main branch, allow on feature branches)
- Analysis before blocking (run a linter, check test coverage)
- Delegation to a sub-agent for nuanced judgment

In those cases, upgrade to a hook or the hook + agent + instruction
pattern.

### Data Flow

```
1. Agent is about to run a shell command
2. pre-command event fires
3. Runtime evaluates the rule:
   a. Does the command match the rule's criteria? -> block
   b. Otherwise -> allow
4. If blocked, agent receives the reason string
5. Agent reads the instruction to understand why and adjusts
```

## Example 3: Docs Enforcer (Hook + Agent + Prompt + Instruction)

A bundle that ensures documentation stays in sync with code changes.
When code files are modified, a sub-agent checks if related documentation
needs updating. A prompt atom provides a structured template for the
documentation review.

### Directory Layout

```
bundles/docs-enforcer/
  tank.json
  SKILL.md
  hooks/docs-check.ts
```

### tank.json

```json
{
  "name": "@tank/docs-enforcer",
  "version": "1.0.0",
  "description": "Ensure documentation stays in sync with code changes.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "hook",
      "name": "docs-check",
      "event": "pre-stop",
      "handler": { "type": "js", "entry": "./hooks/docs-check.ts" }
    },
    {
      "kind": "agent",
      "name": "docs-reviewer",
      "role": "Documentation reviewer. Given a list of modified code files, identify which documentation files (README, API docs, inline comments, JSDoc) need updating. Output one line per stale doc: [STALE] doc-file - reason.",
      "tools": ["read", "grep", "glob"],
      "model": "fast",
      "readonly": true
    },
    {
      "kind": "prompt",
      "name": "docs-review",
      "template": "Review documentation for {{files}}. Check: API signatures match, examples compile, links resolve, changelog updated."
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Why These Atoms

**Hook (pre-stop):** Same interception pattern as quality-gate. When the
agent finishes, the hook checks if code files were modified and whether
corresponding documentation exists.

**Agent (docs-reviewer):** A readonly sub-agent that analyzes code changes
against existing documentation. It uses `read` and `grep` to cross-
reference function signatures with JSDoc/README content.

**Prompt (docs-review):** A structured template the hook can use when
delegating to the agent. The template standardizes what the reviewer
checks: API signatures, examples, links, and changelog. This is reusable
— the same prompt works regardless of which files changed.

**Instruction (SKILL.md):** Defines what counts as "stale documentation,"
which file pairings to check (e.g., `src/api.ts` -> `docs/api.md`), and
the severity of different staleness types.

### How the Prompt Atom Helps

Without the prompt atom, the hook handler would embed the review criteria
as a string literal. This has problems:
- Changing the criteria requires editing TypeScript code
- The template is not discoverable or reusable
- Users cannot invoke the review manually

With the prompt atom, the template is declared in the manifest. The hook
references it, but users can also invoke it directly as a slash command.

### Data Flow

```
1. Agent finishes work
2. pre-stop event fires
3. Hook handler executes:
   a. Gets list of modified code files
   b. Renders the "docs-review" prompt template with file list
   c. Delegates rendered prompt to "docs-reviewer" agent
4. docs-reviewer agent:
   a. Reads each modified code file
   b. Greps for corresponding doc files (README, API docs, JSDoc)
   c. Compares signatures, examples, and links
   d. Outputs stale docs: [STALE] file - reason
5. Hook evaluates output:
   a. If stale docs found -> block stop, inject update instructions
   b. If all docs current -> allow stop
```

### Permission Rationale

- **Network:** No external calls. All analysis is local.
- **Filesystem read:** `["**/*"]` because the agent needs to cross-
  reference code with docs anywhere in the project.
- **Filesystem write:** `[]` because the docs-reviewer is readonly.
  The main agent handles the actual doc updates.
- **Subprocess:** `false` for the same reason as quality-gate.

## Pattern Comparison

| Aspect              | Quality Gate       | Guardrails      | Docs Enforcer      |
| ------------------- | ------------------ | --------------- | ------------------ |
| Atom count          | 3                  | 2               | 4                  |
| Has hook            | Yes (JS)           | No              | Yes (JS)           |
| Has agent           | Yes (code-reviewer)| No              | Yes (docs-reviewer)|
| Has rule            | No                 | Yes (block)     | No                 |
| Has prompt          | No                 | No              | Yes (template)     |
| Has instruction     | Yes                | Yes             | Yes                |
| Complexity          | Medium             | Low             | Medium-High        |
| Custom code         | ~150 lines TS      | 0               | ~80 lines TS       |
| Permission scope    | Read-only          | Read-only       | Read-only          |

## Key Takeaways

1. **Start with the simplest pattern that works.** If a rule suffices,
   do not write a hook. If instruction-only works, do not create a bundle.

2. **The hook is the orchestrator.** In hook+agent patterns, the hook
   decides when to delegate, parses the agent's output, and decides the
   outcome (block/continue/inject).

3. **Agents are specialists, not generalists.** Constrain tools, set
   readonly when possible, use the fastest model tier that works.

4. **Prompts are reusable templates.** Extract review criteria into
   prompt atoms when the same check applies across different contexts.

5. **Instructions are the glue.** Every bundle needs behavioral context.
   Without an instruction atom, the agent does not know the bundle's
   purpose or severity taxonomy.

See `references/tank-json-anatomy.md` for the full schema of each atom.
See `references/bundle-composition.md` for composition patterns and
anti-patterns.
