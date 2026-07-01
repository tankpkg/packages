# Review Criteria

Sources: Martin (Clean Code), Ousterhout (A Philosophy of Software Design),
OWASP Top 10 (2021), CWE Top 25 (2023).

Covers: detailed review criteria by severity level with examples.

## Critical — Security and Data Integrity

Issues that can cause security breaches, data loss, or system crashes.

| Pattern                                   | Example                                         | Why critical          |
| ----------------------------------------- | ----------------------------------------------- | --------------------- |
| Hardcoded secrets                         | `const API_KEY = "sk-..."`                      | Credential exposure   |
| SQL injection                             | `query("SELECT * FROM users WHERE id = " + id)` | Data breach           |
| Path traversal                            | `fs.readFile(userInput)` without sanitization   | Arbitrary file access |
| Missing auth check                        | Route handler without authentication middleware | Unauthorized access   |
| Unhandled null/undefined on critical path | `user.account.balance` without null check       | Runtime crash         |
| Infinite loop without exit condition      | `while (true)` without break or return          | Process hang          |
| Race condition on shared state            | Concurrent writes without locking               | Data corruption       |

## High — Logic and Correctness

Issues that produce wrong results or miss failure modes.

| Pattern                              | Example                                                   | Why high                  |
| ------------------------------------ | --------------------------------------------------------- | ------------------------- |
| Wrong comparison operator            | `if (status = 'active')` (assignment, not comparison)     | Silent bug                |
| Missing error handling               | `await fetch(url)` without try/catch or .catch()          | Unhandled rejection       |
| Off-by-one in loop bounds            | `for (i = 0; i <= arr.length)`                            | Index out of bounds       |
| Type coercion bug                    | `if (count == "0")` in TypeScript                         | Wrong branch taken        |
| Missing return in conditional        | Early return missing, falls through to wrong code         | Wrong result              |
| Async without await                  | `const data = asyncFunction()` (gets Promise, not value)  | Silent incorrect behavior |
| Missing validation on external input | API handler that trusts request body without schema check | Garbage in, garbage out   |
| Resource leak                        | Opened file/connection never closed on error path         | Memory/handle leak        |

## Medium — Maintainability

Issues that make code harder to understand or change safely.

| Pattern                  | Example                                          | Why medium                  |
| ------------------------ | ------------------------------------------------ | --------------------------- |
| Function over 40 lines   | Large function doing multiple things             | Hard to test and modify     |
| Deep nesting (4+ levels) | Nested if/for/try blocks                         | Cognitive overload          |
| Duplicated logic         | Same 10-line block in 3 places                   | Change in one misses others |
| Poor variable naming     | `const d = new Date()` in business logic         | Reader must decode          |
| Missing edge case        | No handling for empty array input                | Fragile                     |
| Magic numbers            | `if (retries > 3)` without named constant        | Meaning unclear             |
| Catch-all error handler  | `catch (e) { console.log(e) }` swallowing errors | Hidden failures             |

## Low — Style and Readability

Issues that don't affect correctness but could improve code quality.
These are reported but never block the agent.

| Pattern                            | Example                                         | Why low           |
| ---------------------------------- | ----------------------------------------------- | ----------------- |
| Inconsistent naming convention     | `getUserData` vs `fetch_user_info` in same file | Inconsistency     |
| Unnecessary else after return      | `if (x) return a; else return b;`               | Minor readability |
| TODO/FIXME without issue reference | `// TODO: fix this later`                       | Untracked debt    |
| Overly verbose code                | Explicit loop where `.map()` suffices           | Preference        |
| Import ordering                    | Unsorted imports                                | Style preference  |

## What NOT to Flag

The reviewer should skip these entirely — they belong to linters and formatters:

- Indentation and whitespace
- Semicolons
- Quote style (single vs double)
- Trailing commas
- Line length
- Bracket placement
- Import sorting (unless semantically wrong)
