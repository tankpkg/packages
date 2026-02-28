# Related Issue Detection

Sources: GitHub issue management patterns, SWE-bench issue clustering, Sweep.dev deduplication heuristics

Covers: relationship types, detection signals, scanning workflow, handling each relationship type, batch fixing, avoiding false positives.

A single root cause can spawn 3-5 user reports with different symptoms. Fixing
one issue might fix 3 others. Fixing an issue might be BLOCKED by another.
Detecting relationships BEFORE fixing saves time and prevents rework.

## Why Related Issues Matter

| Scenario | Cost of not detecting |
|----------|----------------------|
| 3 issues share one root cause | You fix the same bug 3 times instead of once |
| Issue A is blocked by issue B | You waste iterations on A when B must be fixed first |
| Issue is a duplicate | You write redundant tests and PRs |
| Two issues touch the same code | Independent fixes cause merge conflicts |
| Parent feature is missing | Child issue cannot be fixed without parent |

Always scan for related issues before entering the fix cycle.

## Relationship Types

| Type | Definition | Example | Action |
|------|-----------|---------|--------|
| Duplicate | Same bug, different reporter | "CSV fails on accents" + "Export broken for international names" | Link to original, close duplicate |
| Same root cause | Different symptoms, one underlying bug | "Login slow" + "Dashboard timeout" (both caused by DB connection leak) | Fix root cause once, verify all scenarios |
| Parent-child | One issue depends on another existing first | "Add dark mode" then "Dark mode doesn't persist" | Fix parent first |
| Blocked by | Issue cannot be fixed until another is resolved | "Fix payment flow" blocked by "Update Stripe SDK to v3" | Fix blocker first, then return |
| Related but independent | Touch the same code area, different bugs | "CSV header wrong" + "CSV encoding broken" | Fix one at a time, watch for merge conflicts |

## Detection Signals

### Text Similarity Signals

| Signal | Relationship likely |
|--------|-------------------|
| Same error message in two issues | Duplicate or same root cause |
| Same file or function mentioned | Same root cause or related area |
| Same reporter filed multiple issues in short timeframe | Often different symptoms of one bug |
| Issues created within days of each other | Same root cause, likely triggered by a recent release |
| Same labels applied | Related functional area |
| One issue explicitly references another | Explicitly related (check if duplicate or dependency) |
| Same stack trace, different entry points | Same root cause, different code paths |

### Anti-Signals (Probably NOT Related)

| Signal | Likely not related |
|--------|-------------------|
| Same feature area but different behavior | Independent bugs in same module |
| Same error TYPE but different message | Coincidental, different root causes |
| Same reporter but months apart | Separate issues |
| Similar title but different technical content | Keyword collision, not same bug |

## The Related Issues Scan

Before starting a fix, execute this scan. It takes 2-5 minutes and can save
hours of duplicate work.

### Step 1: Extract Key Terms

From the target issue, extract:
- Error messages (exact strings)
- File names and function names mentioned
- Feature area (export, auth, search, etc.)
- Specific technical terms (encoding, timeout, connection, etc.)

### Step 2: Search Open Issues

```bash
# Search by key terms from the issue
gh issue list --state open --search "CSV encoding" --json number,title,labels

# Search by same labels
gh issue list --state open --label "bug" --label "export" --json number,title

# Search by error message (exact phrase)
gh issue list --state open --search '"PayloadTooLargeError"' --json number,title
```

### Step 3: Search Recently Closed Issues

Closed issues might be duplicates that were already fixed, or related issues
with partial fixes.

```bash
# Search last 30 days of closed issues
gh issue list --state closed --search "CSV" --limit 20 \
  --json number,title,closedAt

# Check if a specific closed issue has a linked PR
gh issue view 38 --json title,body,comments \
  --jq '{title: .title, body: .body[:200]}'
```

### Step 4: Check Cross-References

Look for explicit links between issues.

```bash
# Check if the target issue mentions other issues
gh issue view 42 --json body,comments \
  --jq '[.body, (.comments[].body)] | join("\n")' | grep -iE "related|duplicate|see #|fixes #|blocked|depends"
```

### Step 5: Build the Relationship Map

After scanning, categorize findings:

```
Target: #42 (CSV encoding broken)
  - Duplicate of: none found
  - Same root cause: #38 (CSV export garbles special chars) — LIKELY DUPLICATE
  - Blocked by: none
  - Related: #45 (CSV header row missing) — same module, independent bug
```

## Handling Each Relationship Type

### Duplicate Detected

1. Compare the two issues side by side. Is it truly the same bug?
2. Pick the canonical issue (more detailed, or older with more discussion).
3. Comment on the duplicate:

```bash
gh issue comment 42 --body "Duplicate of #38. Both report CSV encoding \
issues with special characters. Tracking the fix in #38."

gh issue close 42 --reason "not planned"
```

4. Fix the canonical issue (#38), not the duplicate.

### Same Root Cause Detected

When 2-3 issues have different symptoms but one underlying cause:

1. Write Gherkin scenarios for ALL affected issues, not just one.
2. Tag each scenario with its issue number:
```gherkin
@issue-38
Scenario: CSV export preserves accented characters
  ...

@issue-42
Scenario: CSV export preserves CJK characters
  ...

@issue-44
Scenario: CSV export preserves emoji
  ...
```
3. Fix the root cause once.
4. Run ALL tagged scenarios to verify.
5. Create ONE PR referencing all issues:

```bash
gh pr create \
  --title "fix: use explicit UTF-8 encoding in CSV serializer (#38, #42, #44)" \
  --body "$(cat <<'EOF'
Fixes #38, Fixes #42, Fixes #44

### Root Cause
The CSV serializer used system default encoding instead of UTF-8.
All three issues are different symptoms of this single bug.
EOF
)"
```

### Blocked-By Detected

When fixing issue A requires issue B to be resolved first:

1. Comment on the blocked issue:

```bash
gh issue comment 42 --body "Blocked by #40 (Stripe SDK upgrade required). \
Fixing #40 first, then returning to this issue."
```

2. Fix the blocker (#40) through the full cycle (triage, Gherkin, RED-GREEN,
   verify, PR).
3. After the blocker is merged, return to the original issue (#42).
4. Check if the blocker fix also resolved the original issue. If yes, close
   it. If no, proceed with the fix cycle.

### Parent-Child Detected

When an issue depends on a parent feature:

1. Fix the parent issue first.
2. After the parent is merged, check if the child issue is automatically
   resolved (sometimes it is).
3. If the child still fails, fix it separately.

### Related But Independent

When issues touch the same code area but have different bugs:

1. Fix them one at a time.
2. Fix the simpler one first (less risk of breaking the other).
3. After fixing the first, pull latest before starting the second.
4. Watch for merge conflicts — they indicate tighter coupling than expected.

## Batch Fixing (Same Root Cause)

When multiple issues share a root cause, batch them.

### Batch Workflow

1. Identify all issues with the same root cause (the scan above).
2. Write Gherkin for ALL of them before fixing anything.
3. Run ALL scenarios — they should ALL be RED (confirming they share the bug).
4. Fix the root cause once.
5. Run ALL scenarios — they should ALL be GREEN.
6. Create one PR referencing all issues.
7. Document findings/resolutions for each issue individually.

### Batch PR Title Format

```
fix: {root cause description} (#{n1}, #{n2}, #{n3})
```

### Batch Commit Structure

Same 3-commit structure, but commit 1 includes multiple feature files:

```bash
# Commit 1: All the tests
git add .bdd/features/export/csv-encoding.feature
git add .bdd/features/export/csv-cjk.feature
git add .bdd/features/export/csv-emoji.feature
git commit -m "test: add BDD scenarios for #38, #42, #44"

# Commit 2: The single root cause fix
git add src/export/csv-writer.ts
git commit -m "fix: use explicit UTF-8 in CSV serializer (#38, #42, #44)"

# Commit 3: Documentation for all issues
git add .bdd/qa/
git commit -m "docs: add QA findings for #38, #42, #44"
```

## Avoiding False Positives

Not every similarly-worded issue is related. Be skeptical.

| Trap | Reality |
|------|---------|
| Same feature area mentioned | Different bugs in the same module happen all the time |
| Same error TYPE (e.g., both are TypeErrors) | TypeError is generic — the causes are usually unrelated |
| Same reporter | Prolific reporters file many independent issues |
| Similar title | "Export broken" and "Export slow" are completely different bugs |
| Same code file mentioned | A file with many responsibilities has many independent bugs |

### When Uncertain

If you are not sure two issues are related:

1. Treat them as independent.
2. Note the potential relationship in the PR body:
   ```
   Note: This issue may share a root cause with #38. If #38 persists
   after this fix merges, investigate the CSV serializer encoding path.
   ```
3. Do not delay fixing one while investigating the relationship.

The cost of treating related issues as independent is duplicate work.
The cost of treating independent issues as related is scope creep and
a fix that tries to solve too many problems at once. When in doubt,
keep the scope small.
