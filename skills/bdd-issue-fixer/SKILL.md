---
name: bdd-issue-fixer
description: |
  Resolve GitHub issues using BDD — read the issue, write a behavioral test,
  confirm it fails (RED), fix the code, confirm it passes (GREEN), open a PR
  with test + fix as proof. Covers issue triage (bug vs feature vs invalid vs
  duplicate), issue-to-Gherkin translation, the relentless RED-GREEN fix cycle,
  fix verification, PR submission with evidence, and related issue detection.
  Synthesizes Smart/Molak (BDD in Action), Beck (TDD By Example), Nicieja
  (Writing Great Specifications), SWE-bench (Princeton NLP), and Sweep.dev
  patterns.

  Trigger phrases: "fix this issue", "resolve issue", "fix GitHub issue",
  "BDD fix", "issue to test", "write test for issue", "red green fix",
  "triage issue", "duplicate issue", "related issues", "fix and PR",
  "issue fixer", "auto-fix issue", "resolve bug report"
---

# BDD Issue Fixer

## Hard Rules

These are non-negotiable. Violating any of these means the work is wrong.

1. **Never weaken a test.** When a test fails, the CODE is wrong. Fix the
   code, not the test. Never skip, mock, or reduce assertion precision.

2. **Test behavior, not implementation.** The Gherkin scenario captures what
   the user expects. Write declarative scenarios from the user's perspective,
   never imperative UI scripts.

3. **Iterate until fixed.** Try up to 5 different fix strategies. If approach
   1 fails, analyze why and try approach 2. Never give up after one attempt.
   Escalate only after 5 genuine attempts.

4. **Not every issue deserves a fix.** Triage first. Duplicates, questions,
   invalid reports, and vague wishlists are not fixable issues. Classify
   before coding.

5. **Document everything.** Every fix produces findings, resolutions, and a
   PR with evidence. The BDD scenario in the PR IS the proof.

## Core Workflow

This is the mandatory sequence. Execute in order. Do not skip steps.

```
1. TRIAGE  →  Read issue, classify, check for duplicates/related
     ↓
2. GHERKIN →  Translate fixable issue into behavioral test
     ↓
3. RED     →  Run test, confirm it fails (bug exists)
     ↓
4. FIX     →  Implement minimal code change
     ↓
5. GREEN?  →  Run test again
     ↓ YES         ↓ NO
6. VERIFY      Back to step 4 (max 5 iterations)
     ↓
7. PR      →  Create PR with test + fix + evidence
```

## Quick-Start

### "I have a GitHub issue to fix"

| Step | Action |
|------|--------|
| 1. Read issue | `gh issue view {N} --json title,body,labels,comments` |
| 2. Triage | Classify: bug / feature / question / invalid / duplicate. See `references/issue-triage.md` |
| 3. Check related | Search for duplicates and same-root-cause issues. See `references/related-issues.md` |
| 4. Write Gherkin | Translate issue into `.bdd/features/{domain}/{slug}.feature`. See `references/issue-to-gherkin.md` |
| 5. RED-GREEN cycle | Run test → fix code → run test → repeat until GREEN. See `references/red-green-fix-cycle.md` |
| 6. Verify | Full suite, no regressions, document findings. See `references/fix-verification.md` |
| 7. PR | Branch, commit (test, fix, docs), push, create PR. See `references/pr-and-git-workflow.md` |

### "The issue seems invalid or incomplete"

| Signal | Action | Reference |
|--------|--------|-----------|
| Can't reproduce | Ask for clarification with template | `references/issue-triage.md` |
| User confusion, not a bug | Answer the question, close | `references/issue-triage.md` |
| Same as existing issue | Link to original, close as duplicate | `references/related-issues.md` |
| Vague wishlist, no criteria | Label "needs-discussion", don't fix | `references/issue-triage.md` |
| Requires breaking changes | Escalate to maintainer | `references/issue-triage.md` |

### "My fix broke other tests"

| Symptom | Fix | Reference |
|---------|-----|-----------|
| Target test passes but other tests fail | Adjust fix to satisfy both behaviors | `references/fix-verification.md` |
| Flaky test fails intermittently | Run 3x — if pre-existing flake, note and move on | `references/fix-verification.md` |
| Type/lint errors in changed files | Fix them — never suppress with ts-ignore or rule disabling | `references/fix-verification.md` |

### "Multiple issues seem related"

| Relationship | Action | Reference |
|-------------|--------|-----------|
| Duplicate (same bug) | Close duplicate, fix canonical | `references/related-issues.md` |
| Same root cause | Write Gherkin for ALL, fix root cause once | `references/related-issues.md` |
| Blocked by another issue | Fix blocker first | `references/related-issues.md` |
| Parent-child | Fix parent, check if child resolves | `references/related-issues.md` |

## Decision Trees

### Should I fix this issue?

| Signal | Decision |
|--------|----------|
| Clear bug with repro steps | Fix it |
| Feature request with acceptance criteria | Fix it |
| Vague report, can infer expected behavior | Fix it, note assumptions |
| No expected behavior, can't infer | Ask for clarification |
| User error or confusion | Answer and close |
| Duplicate of existing issue | Close, link to original |
| Requires architectural changes | Escalate, label "needs-design" |
| Security vulnerability | Private disclosure, do not fix in public PR |

### Which fix iteration strategy?

| Iteration | Strategy |
|-----------|----------|
| 1 | Direct fix — most obvious change |
| 2 | Root cause analysis — trace the stack trace deeper |
| 3 | Broader context — read surrounding code, understand data flow |
| 4 | Alternative approach — different algorithm or code path |
| 5 | Minimal viable — simplest possible code that makes it work |
| After 5 | Escalate — document all attempts, label "needs-human-review" |

## Commit and PR Structure

Three atomic commits per fix:

| Commit | Content | Message format |
|--------|---------|----------------|
| 1 | Gherkin scenario (the failing test) | `test: add BDD scenario for #{N}` |
| 2 | Code fix | `fix: {description} (#{N})` |
| 3 | QA documentation (findings + resolution) | `docs: add QA findings for #{N}` |

PR body must include: the Gherkin scenario, verification results, iteration
count, and `Fixes #{N}` for auto-close. See `references/pr-and-git-workflow.md`.

## Reference Files

| File | Contents |
|------|----------|
| `references/issue-triage.md` | Issue classification, extraction protocol, gh CLI commands, when NOT to fix, clarification templates, priority signals |
| `references/issue-to-gherkin.md` | Translating issues into Gherkin scenarios, bug-to-Gherkin, feature-to-Gherkin, handling vague issues, file placement, quality rules |
| `references/red-green-fix-cycle.md` | The relentless fix loop: RED confirmation, fix strategies per iteration, failure analysis, never-weaken rule, escalation protocol |
| `references/fix-verification.md` | Post-fix verification suite, regression handling, findings/resolution documentation format, verification checklist |
| `references/pr-and-git-workflow.md` | Branch strategy, 3-commit structure, PR title/body template, gh CLI commands, auto-close keywords, non-fix outcomes |
| `references/related-issues.md` | Duplicate detection, same-root-cause clustering, blocked-by chains, batch fixing, gh CLI search patterns |
