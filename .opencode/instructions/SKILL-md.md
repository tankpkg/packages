# Quality Gate

## Core Philosophy

1. **No code ships without review.** Every time the agent is about to stop
   after modifying code, a reviewer checks the changes. This is automatic —
   the developer doesn't need to remember to ask for a review.

2. **Only block on what matters.** Issues are categorized as critical, high,
   medium, or low. Only critical and high block the agent from stopping.
   Medium and low are reported but don't prevent completion.

3. **Review only what changed.** The reviewer looks at modified files only,
   not the entire codebase. This keeps reviews fast and focused.

4. **The loop is self-healing.** When the agent fixes critical/high issues,
   the hook runs again automatically. The loop continues until no blocking
   issues remain.

5. **Non-code changes pass through.** If the agent only modified markdown,
   config, or other non-code files, the gate opens without review.

## How It Works

```
Agent finishes work
        │
        ▼
  [pre-stop hook fires]
        │
        ▼
  Were code files modified?
   ├── No  → agent stops normally
   └── Yes → delegate to code-reviewer agent
                    │
                    ▼
              Review modified hunks
              Categorize issues: critical/high/medium/low
                    │
                    ▼
              Any critical or high issues?
               ├── No  → agent stops (medium/low reported)
               └── Yes → block stop, force agent to fix
                              │
                              ▼
                         Agent fixes issues
                              │
                              ▼
                         [pre-stop hook fires again]
                              (loop until clean)
```

## Severity Definitions

| Severity | Blocks | Examples                                                                      |
| -------- | ------ | ----------------------------------------------------------------------------- |
| Critical | Yes    | Security vulnerabilities, data loss, crashes, broken auth                     |
| High     | Yes    | Logic errors, missing error handling, race conditions, type safety violations |
| Medium   | No     | Code duplication, poor naming, missing edge cases                             |
| Low      | No     | Style preferences, minor readability improvements                             |

## What Gets Reviewed

Code file extensions that trigger the review gate:

`.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`, `.rs`, `.java`, `.rb`, `.c`,
`.cpp`, `.h`, `.hpp`, `.cs`, `.swift`, `.kt`, `.scala`, `.sh`, `.bash`

Non-code files that are skipped:

`.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`, `.xml`, `.csv`,
`.env`, `.gitignore`, `.editorconfig`, images, fonts, lockfiles

## Reference Index

| File                            | Contents                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| `references/review-criteria.md` | Detailed review criteria by severity level, common patterns to flag, and examples of each category |
