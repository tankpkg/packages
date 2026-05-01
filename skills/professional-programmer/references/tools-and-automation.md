# Tools and Automation

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Spinellis on Unix tools and version control; Horstmann on automation; Tank ast-linter-codemod, bdd-e2e-testing, and package-publisher skills

Covers: coding standards, static analysis, command-line fluency, IDE use, version control, builds, deployment, bug trackers, and automation.

## Tool Standard

Tools are part of the system. A professional agent uses tools to make quality repeatable instead of relying on memory and taste.

Choose tools with care. Every tool adds setup, failures, updates, and social cost. Adopt tools that remove more complexity than they add.

## Coding Standards

Automate style rules. Humans should review design, correctness, and tradeoffs, not argue about whitespace.

Use formatters for layout, linters for error-prone patterns, type checks for contracts, and tests for behavior.

| Concern | Preferred Enforcement |
| ------- | --------------------- |
| Formatting | Formatter |
| Import order | Formatter or linter |
| Unsafe API use | Linter or custom rule |
| Repeated migration | Codemod |
| Behavior | Test |
| Security boundary | Security review plus test |

## Static Analysis

Take advantage of code analysis tools, but do not outsource judgment to them.

Treat warnings as work. A build with ignored warnings trains the team to ignore future warnings.

When a warning is false-positive, suppress it narrowly with a reason.

## Command Line and IDE

Know the command line because it composes, scripts, and reproduces workflows.

Know the IDE because it exposes navigation, refactoring, debugging, and feedback loops faster than manual search.

Use both. Do not turn tool preference into identity.

## Version Control

Put everything needed to rebuild, test, and understand the project under version control, excluding generated artifacts, secrets, and local machine state.

Know your next commit before editing widely. A coherent commit has one intent and a reviewable diff.

Commit messages should explain why the change exists, not merely list touched files.

## Build Hygiene

Keep the build clean. Broken builds block teams, hide regressions, and make deployment risky.

Own and refactor the build. Build scripts are production code for the team; keep them readable, tested where practical, and fast enough for feedback.

Prefer one deployable artifact per release path when possible. Multiple artifact variants multiply test and support matrices.

## Deployment

Deploy early and often when safety rails exist. Smaller releases reduce batch risk and make failures easier to diagnose.

For risky changes, use staged rollout, feature flags, migrations with rollback strategy, or compatibility windows.

## Bug Trackers

Use bug trackers to preserve context and decisions, not to bury work.

A useful issue includes observed behavior, expected behavior, reproduction steps, environment, severity, and evidence.

Close the loop by linking commits, tests, and deployment notes.

## Routing

Use `@tank/ast-linter-codemod` for lint rules and codemods.

Use `@tank/bdd-e2e-testing` for CI behavior verification.

Use `git-master` for complex history, commits, blame, bisect, or worktree operations.

## Automation Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Formatting debate | Formatter | Removes review noise |
| Repeated dangerous pattern | Linter rule | Prevents recurrence |
| Bulk API migration | Codemod | Keeps edits consistent |
| Manual release steps | Script/CI job | Improves repeatability |
| Build warnings | Ratchet/fail new warnings | Restores signal |
| Local-only setup | Document/script clean checkout | Supports onboarding |
| Secret config | Template plus secret injection | Avoids leaks |
| Bug report | Repro template | Improves triage |
| Dependency update | Lockfile and CI | Preserves reproducibility |
| Deploy risk | Dry-run/rollback | Reduces blast radius |

## Automation Examples

### Formatter Adoption

A formatter should replace style debate, not become another manual checklist. Add it to the standard command path and make CI enforce the same behavior developers run locally.

### Release Script

A release script needs safe defaults, visible environment, dry-run output, and clear failure messages. Automation that fails mysteriously only moves tribal knowledge into a shell file.

### Custom Lint Rule

Create a custom lint rule when the same risky pattern appears repeatedly and review comments are not enough. Prefer auto-fix when the safe transformation is mechanical.

### Bug Tracker Hygiene

A bug report without reproduction steps is not ready for implementation. Ask for observed behavior, expected behavior, environment, and evidence before guessing at a fix.

## Automation Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Formatter rollout | Run locally and in CI so style disappears from review. |
| Repeated unsafe import | Add lint rule or codemod rather than review reminders. |
| Manual release | Create script with dry-run, environment display, and rollback note. |
| Dirty warnings | Ratchet existing warnings and fail on new ones. |
| Local setup drift | Test setup from a clean checkout. |
| Secret config | Commit template and document secret injection. |
| Bug report gaps | Use template requiring observed, expected, environment, reproduction. |
| Dependency choice | Compare platform support before adding package. |
| Build slowdown | Profile pipeline and cache stable dependencies. |
| Deployment order | Encode compatibility or gate rather than oral sequencing. |

