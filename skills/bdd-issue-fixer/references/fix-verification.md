# Fix Verification

Sources: Smart/Molak (BDD in Action), Khorikov (Unit Testing Principles), SWE-bench verification patterns

Covers: post-fix verification suite, regression detection, findings/resolution documentation, verification checklist.

The fix is not done when the target test passes. It is done when the target
test passes, the existing suite still passes, the build succeeds, and the
fix is documented. Verification is proof, not hope.

## The Verification Suite

After the RED-GREEN fix cycle produces a GREEN result, execute this verification
sequence in order. Do not skip steps.

| Step | Command | Pass criteria |
|------|---------|---------------|
| 1. Target scenario | `[test-runner] --grep "@issue-{N}"` | Scenario PASSES |
| 2. Full test suite | `[test-runner]` | Same pass count as before fix (no regressions) |
| 3. Linter | `[linter]` | No new errors in changed files |
| 4. Type checker | `[type-checker]` | No new type errors in changed files |
| 5. Build | `[build-command]` | Exit code 0 |

### Step 1: Run Target Scenario in Isolation

Confirm the fix works for the specific issue.

```bash
# Run only the tagged scenario
[test-runner] --grep "@issue-42"
```

If this fails, you are still in the RED-GREEN fix cycle. Go back to
`red-green-fix-cycle.md`.

### Step 2: Run the Full Test Suite

This catches regressions. The fix may have broken something else.

```bash
# Run the entire test suite
[test-runner]

# Record the results
# Before fix: 142/145 passed (3 pre-existing failures)
# After fix:  143/145 passed (same 2 pre-existing failures + new issue test)
```

Compare the before-fix and after-fix results. The pass count should be
equal or higher (the new test adds one more pass). The fail count should
be equal or lower.

### Step 3-5: Linter, Type Checker, Build

Run each on the changed files. Fix any issues introduced by the fix.

**Non-negotiable rules:**
- Never use `@ts-ignore`, `@ts-expect-error`, or `as any` to suppress type errors
- Never disable a lint rule with `// eslint-disable` or equivalent
- Never skip the build step for "small changes"

If linting or type checking fails on unchanged files, those are pre-existing
issues. Note them but do not fix them (unless the fix caused them).

## Handling Regressions

When the full suite reveals failures that did not exist before the fix:

| Regression type | Diagnosis | Action |
|----------------|-----------|--------|
| Unrelated test fails, was passing before | Your fix changed shared state or a shared dependency. | Investigate the connection. Adjust fix to preserve both behaviors. |
| Related test fails (same feature area) | Your fix changed behavior that another test depends on. | Adjust fix to satisfy BOTH the target scenario and the related test. |
| Flaky test fails intermittently | Run 3 times. If it passes 2/3, it is a pre-existing flake. | Note the flake in findings. Not caused by your fix. Move on. |
| Type error in changed file | Your fix has a type issue. | Fix the type error properly. No type suppression. |
| Lint error in changed file | Your fix violates a lint rule. | Fix the lint violation. Do not disable the rule. |
| Build fails | Your fix broke compilation or bundling. | Fix the build error. Check imports, exports, and module resolution. |

### The Regression Fix Protocol

1. Do NOT revert and give up.
2. Understand what the regression reveals. Maybe the fix needs broader scope.
3. Adjust the fix to satisfy BOTH the target scenario AND the regressed test.
4. If the regression is in a genuinely unrelated area, investigate if there is
   a shared dependency (shared module, global state, database fixture).
5. After fixing the regression, run the FULL verification suite again.
6. Repeat until clean.

## Documenting Findings

After the fix cycle completes (whether successful or escalated), document
what happened. Create or update a findings file in `.bdd/qa/findings/`.

### Findings File Format

```markdown
# {Issue Title} Findings

Issue: #{issue_number}
Date: {ISO date}
Branch: fix/issue-{number}-{short-slug}

## Scenario: {Scenario name from .feature file}
- Status: PASSED (after {N} iterations)
- Iterations required: {N}
- Final fix: {One-line description of the change}

## Regression Check
- Full suite: {X}/{Y} passed (same as baseline)
- New failures: none
- Pre-existing failures: {list if any, or "none"}
- Flaky tests noted: {list if any, or "none"}

## Evidence
- Test output: {inline or path to log}
- Changed files: {list of files modified}
```

### File Naming

- File name: `{domain}-{slug}.md` matching the feature file
- Example: `export-csv-encoding.md` for `features/export/csv-encoding.feature`
- One findings file per issue

## Documenting Resolutions

Create a resolution file in `.bdd/qa/resolutions/` that explains the fix.
This is the audit trail.

### Resolution File Format

```markdown
# Resolution: {Issue Title}

Issue: #{issue_number}
Date: {ISO date}

## Root Cause
{What was actually broken and why. Be specific: "The CSV serializer used
the system default encoding (Latin-1 on Windows) instead of explicitly
specifying UTF-8. The encoding parameter was missing from the
`createWriteStream` call in `src/export/csv-writer.ts:47`."}

## Fix Applied
{What was changed. Reference specific files and functions.}

## Iteration History
1. {Attempt 1}: {What was tried}. Result: {Why it failed}.
2. {Attempt 2}: {What was tried}. Result: {Why it failed}.
3. {Attempt 3}: {What was tried}. Result: PASSED.

## Verification
- Target scenario: PASSED
- Full suite: {X}/{Y} passed, no regressions
- Build: PASSED
- Lint: Clean on changed files
- Type check: Clean on changed files
```

### When the Fix Was Escalated

If the fix cycle ended in escalation (5 failed iterations), the resolution
file documents the attempts:

```markdown
# Resolution: {Issue Title} (ESCALATED)

Issue: #{issue_number}
Date: {ISO date}
Status: ESCALATED - needs human review

## Root Cause Hypothesis
{Best understanding of what is broken, even though the fix failed}

## Attempted Fixes
1. {Attempt 1}: {strategy, change, result}
2. {Attempt 2}: {strategy, change, result}
3. {Attempt 3}: {strategy, change, result}
4. {Attempt 4}: {strategy, change, result}
5. {Attempt 5}: {strategy, change, result}

## Why It Resists Fixing
{Analysis of why 5 approaches failed. What makes this bug hard?}

## Suggested Next Steps
{Recommendations for a human reviewer}
```

## Verification Checklist

Before proceeding to PR creation (see `pr-and-git-workflow.md`), every item
must be checked.

| # | Check | Status |
|---|-------|--------|
| 1 | Target scenario GREEN | Required |
| 2 | Full test suite: no new failures | Required |
| 3 | Build succeeds | Required |
| 4 | Linter clean on changed files | Required |
| 5 | Type checker clean on changed files | Required |
| 6 | Findings file created in `.bdd/qa/findings/` | Required |
| 7 | Resolution file created in `.bdd/qa/resolutions/` | Required |

All 7 checks must pass before creating a PR. If any check fails, fix it
before proceeding. Do not create a PR with known issues and hope reviewers
will not notice.

## When Verification Reveals a Deeper Problem

Sometimes verification uncovers something unexpected:
- The fix works but reveals that the test infrastructure is brittle
- The fix works but another feature silently depends on the old broken behavior
- The fix works but performance degrades significantly

In these cases:
1. Complete the current fix (it fixes the reported issue)
2. File NEW issues for the discovered problems
3. Reference the new issues in the PR body
4. Do not scope-creep the current fix to address everything
