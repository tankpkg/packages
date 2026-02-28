# PR and Git Workflow

Sources: GitHub CLI documentation, conventional commits, Sweep.dev PR patterns, SWE-bench submission format

Covers: branch strategy, 3-commit structure, PR title/body template, gh CLI commands, auto-close keywords, handling non-fix outcomes.

## Branch Strategy

Every issue fix gets its own branch. One branch per issue. Never combine
multiple issue fixes in one branch.

### Branch Naming

Format: `fix/issue-{number}-{short-slug}`

```bash
# Examples
fix/issue-42-csv-encoding
fix/issue-87-large-file-upload
fix/issue-103-search-results
feat/issue-55-dark-mode
```

Use `fix/` for bug fixes and `feat/` for feature requests.

### Creating the Branch

Always branch from the default branch with the latest changes.

```bash
# Ensure you are on the default branch with latest
git checkout main && git pull origin main

# Create the fix branch
git checkout -b fix/issue-42-csv-encoding
```

If the project uses a branch other than `main` (e.g., `master`, `develop`),
use that instead.

## Commit Strategy

Three atomic commits per fix. This structure makes it easy for reviewers to
see the before/after and verify the fix methodology.

### Commit 1: The Test (RED)

Add the Gherkin scenario and any supporting step definitions. On this commit,
the test SHOULD fail — it captures the broken behavior.

```bash
git add .bdd/features/ .bdd/steps/ .bdd/interactions/ .bdd/support/
git commit -m "test: add BDD scenario for #42"
```

### Commit 2: The Fix (GREEN)

Add the code change that makes the test pass. Only application code goes in
this commit.

```bash
git add src/
# Or whatever the project's source directory is
git commit -m "fix: handle UTF-8 encoding in CSV export (#42)"
```

For feature requests, use `feat:` instead of `fix:`:
```bash
git commit -m "feat: add dark mode toggle in settings (#55)"
```

### Commit 3: The Documentation

Add the QA findings and resolution files.

```bash
git add .bdd/qa/
git commit -m "docs: add QA findings and resolution for #42"
```

### Why Three Commits

| Commit | Purpose for reviewers |
|--------|----------------------|
| 1 (test) | "Here is the behavior that was broken. You can check out this commit and see it fail." |
| 2 (fix) | "Here is the minimal change that makes it pass." |
| 3 (docs) | "Here is the evidence trail: what was found, what was tried, what worked." |

Do not squash these into one commit. The separation is intentional.

## PR Title and Body

The PR is proof that the fix works. It must include evidence.

### PR Title Format

```
fix: {short description} (#{issue_number})
```

Examples:
```
fix: handle UTF-8 encoding in CSV export (#42)
feat: add dark mode toggle in settings (#55)
fix: accept file uploads up to documented 100MB limit (#87)
```

### PR Body Template

```markdown
## Fixes #{issue_number}

### Problem
{One paragraph describing the bug from the issue. What was broken and
what the user experienced.}

### Solution
{One paragraph describing the fix. What was changed and why this
approach was chosen.}

### BDD Scenario
```gherkin
{The full Gherkin scenario. Copy-paste from the .feature file.}
```

### Verification
- Target scenario: PASSED
- Full test suite: {X}/{Y} passed (no regressions)
- Build: PASSED
- Lint: Clean
- Type check: Clean

### Iterations
{N} iteration(s) required.
1. {Brief description of attempt 1 and result}
2. {Brief description of attempt 2 and result}
3. {Brief description of attempt 3 — PASSED}

### Files Changed
- `src/export/csv-writer.ts` — Added explicit UTF-8 encoding parameter
- `.bdd/features/export/csv-encoding.feature` — New BDD scenario
- `.bdd/qa/findings/export-csv-encoding.md` — Test findings
- `.bdd/qa/resolutions/export-csv-encoding.md` — Fix documentation
```

## Creating the PR with gh CLI

### Push and Create

```bash
# Push the branch
git push -u origin fix/issue-42-csv-encoding

# Create the PR
gh pr create \
  --title "fix: handle UTF-8 encoding in CSV export (#42)" \
  --body-file .bdd/qa/pr-body.md
```

For simpler PRs, use inline body with heredoc:

```bash
gh pr create \
  --title "fix: handle UTF-8 encoding in CSV export (#42)" \
  --body "$(cat <<'EOF'
## Fixes #42

### Problem
CSV export corrupts special characters (accented names appear as mojibake).

### Solution
Added explicit UTF-8 encoding to the CSV write stream. The serializer was
using the system default encoding (Latin-1) instead of UTF-8.

### Verification
- Target scenario: PASSED
- Full test suite: 143/145 passed (no regressions)
- Build: PASSED
EOF
)"
```

### Adding Labels

```bash
gh pr edit --add-label "bug-fix"
```

### Requesting Review

```bash
gh pr edit --add-reviewer username
```

## Auto-Close Keywords

GitHub automatically closes the linked issue when the PR merges. Use these
keywords in the PR BODY (not just the title — title keywords are unreliable).

| Keyword | Example |
|---------|---------|
| `Fixes` | `Fixes #42` |
| `Closes` | `Closes #42` |
| `Resolves` | `Resolves #42` |

Always use `Fixes #{number}` as the first line of the PR body.

For multiple issues (same root cause):
```markdown
Fixes #42, Fixes #43, Fixes #44
```

## Non-Fix Outcomes

Not every issue results in a code change. Handle these with comments, not PRs.

### Issue is Invalid / Not a Bug

```bash
gh issue comment 42 --body "$(cat <<'EOF'
## Triage Result: Not a Bug

**Investigation:** Reproduced the reported behavior. This is working as
designed — the CSV export uses the system locale encoding, which is
documented in the README under "Export Configuration."

**Evidence:** Tested with locale set to UTF-8; export produces correct
output. The issue is a configuration problem, not a code bug.

**Recommendation:** Set the `LANG` environment variable to `en_US.UTF-8`
before running the export.
EOF
)"

gh issue close 42 --reason "not planned"
```

### Issue Needs More Information

```bash
gh issue comment 42 --body "$(cat <<'EOF'
## Needs More Information

I attempted to reproduce this but need additional details:

1. **What operating system are you using?** (encoding defaults vary by OS)
2. **What is the output of `locale` in your terminal?**
3. **Can you attach a sample CSV file showing the corruption?**

Adding the `needs-info` label. Will investigate further once details are provided.
EOF
)"

gh issue edit 42 --add-label "needs-info"
```

### Issue is a Duplicate

```bash
gh issue comment 42 --body "Duplicate of #38. The root cause is the same \
(system encoding not explicitly set in CSV serializer). Fix is being \
tracked in #38."

gh issue close 42 --reason "not planned"
```

### Fix Was Escalated

```bash
gh issue comment 42 --body "$(cat <<'EOF'
## Automated Fix Attempted — Escalated

5 fix iterations were attempted. The issue resists automated fixing due to
the complexity of the serialization pipeline. See detailed analysis below.

[Paste escalation summary from red-green-fix-cycle.md]

Adding `needs-human-review` label for maintainer attention.
EOF
)"

gh issue edit 42 --add-label "needs-human-review"
```

## Responding to PR Review Comments

When a PR receives review feedback:

1. Read ALL comments before responding to any.
2. For each comment, either:
   - Make the requested code change, OR
   - Explain why the current approach is correct (with evidence)
3. Push changes as a NEW commit (do not force-push during review).
4. Reply to each review comment with what was done.

```bash
# After addressing review feedback
git add .
git commit -m "fix: address review feedback on #42"
git push
```

Do not amend or squash during review. Reviewers need to see what changed
between rounds.

## Complete Workflow Summary

```bash
# 1. Branch
git checkout main && git pull
git checkout -b fix/issue-42-csv-encoding

# 2. Write test (commit 1)
# ... create .bdd/features/export/csv-encoding.feature
git add .bdd/
git commit -m "test: add BDD scenario for #42"

# 3. Fix code (commit 2)
# ... fix src/export/csv-writer.ts
git add src/
git commit -m "fix: handle UTF-8 encoding in CSV export (#42)"

# 4. Document (commit 3)
# ... create .bdd/qa/findings/ and .bdd/qa/resolutions/
git add .bdd/qa/
git commit -m "docs: add QA findings and resolution for #42"

# 5. Push and PR
git push -u origin fix/issue-42-csv-encoding
gh pr create --title "fix: handle UTF-8 encoding in CSV export (#42)" \
  --body-file .bdd/qa/pr-body.md
```
