---
name: "@tank/github-issues"
description: |
  Expert management of GitHub Issues via the gh CLI. Covers the full
  issue lifecycle: creating, triaging, editing, closing, and linking
  issues to PRs. Includes issue templates (.md and YAML forms), search,
  label taxonomy, milestones, Projects v2, gh api bulk operations,
  GitHub Actions automation (stale, labeler, auto-assign), and
  issue-driven development. Synthesizes GitHub CLI docs, the GitHub
  REST/GraphQL API reference, and production OSS issue management.

  Trigger phrases: "github issue", "gh issue", "create issue",
  "close issue", "issue template", "issue form", "ISSUE_TEMPLATE",
  "triage issue", "label issue", "milestone", "stale issues",
  "bulk close issues", "search issues", "gh search issues",
  "issue automation", "config.yml blank issues", "issue-driven",
  "sub-issues", "gh issue develop", "gh label", "issue workflow",
  "gh api issues", "bulk operations issues", "issue forms yaml",
  "closing keywords fixes closes resolves"
---

# GitHub Issues

## Core Philosophy

1. **Issues are the unit of work** -- Every code change traces back to an
   issue. No issue, no PR. This creates accountability and traceability.
2. **Triage within 48 hours** -- Every new issue gets classified, labeled,
   and either accepted, closed, or flagged for more info within 2 days.
3. **Structure beats freedom** -- Use Issue Forms (.yml) over classic
   templates. Enforce required fields. Disable blank issues. Structured
   input produces actionable issues.
4. **Automate the boring parts** -- Labeling, staleness, assignment, and
   project routing belong in GitHub Actions, not human checklists.
5. **gh CLI is the primary interface** -- Every issue operation is faster
   from the terminal. Master `gh issue`, `gh search issues`, and `gh api`.

## Quick-Start: What Do You Need?

| Task | Start Here |
|------|-----------|
| Create, view, edit, close an issue | See `references/gh-issue-commands.md` |
| Find issues matching specific criteria | See `references/search-and-filter.md` |
| Set up issue templates for a repo | See `references/issue-templates.md` |
| Design label taxonomy, manage milestones/projects | See `references/labels-milestones-projects.md` |
| Bulk operations, API scripting, CSV export | See `references/api-and-scripting.md` |
| Set up GitHub Actions for issue automation | See `references/automation-actions.md` |
| Issue-driven development, triage, linking patterns | See `references/workflows-and-patterns.md` |

## Command Routing Table

| Intent | Command |
|--------|---------|
| List open issues | `gh issue list` |
| List with filters | `gh issue list -l bug -a @me -s open` |
| Create an issue | `gh issue create -t "Title" -b "Body" -l bug` |
| View issue details | `gh issue view 123` |
| Edit issue metadata | `gh issue edit 123 --add-label "priority/high"` |
| Close with reason | `gh issue close 123 -r completed -c "Fixed in #456"` |
| Reopen an issue | `gh issue reopen 123` |
| Comment on issue | `gh issue comment 123 -b "Thanks for reporting"` |
| Create branch from issue | `gh issue develop 123 --checkout` |
| Search across repos | `gh search issues "bug" --owner myorg --state open` |
| Transfer to another repo | `gh issue transfer 123 owner/other-repo` |
| Pin important issue | `gh issue pin 123` |
| Lock conversation | `gh issue lock 123 -r resolved` |
| Delete issue | `gh issue delete 123 --yes` |
| Bulk close by label | `gh issue list -l stale --json number -q '.[].number' \| xargs -I{} gh issue close {}` |

## Decision Trees

### Issue Template Format

| Signal | Use |
|--------|-----|
| Need structured fields with validation | Issue Form (.yml) |
| Need free-form markdown body | Classic template (.md) |
| Need to enforce required fields | Issue Form (.yml) |
| Need code input with syntax highlighting | Issue Form with `render` attribute |
| Migrating from existing .md templates | Convert to .yml for better UX |

### Close or Keep Open?

| Signal | Decision |
|--------|----------|
| Fixed by merged PR | Close with `--reason completed` |
| Won't implement, by design | Close with `--reason "not planned"` |
| Duplicate of existing issue | Close, comment with link to original |
| Can't reproduce, no response in 14 days | Close with `--reason "not planned"` |
| Needs more info, reporter active | Keep open, add `status/needs-info` label |
| Valid but low priority | Keep open, add to Backlog milestone |
| Security vulnerability | Do NOT use public issue. Use security advisory. |

### When to Use Sub-Issues vs Task Lists

| Signal | Use |
|--------|-----|
| Multiple distinct work items, separate assignees | Sub-issues |
| Simple checklist within one person's work | Task list (markdown checkboxes) |
| Cross-repo breakdown of an epic | Sub-issues (same org) |
| Progress tracking visible in Projects | Sub-issues |
| Quick TODO within an issue body | Task list |

## Issue Lifecycle Keywords

Auto-close an issue when a PR merges to the default branch:

```
Fixes #42        Closes #42        Resolves #42
fixes #42        closes #42        resolves #42
Fixed #42        Closed #42        Resolved #42
```

Multiple issues: `Fixes #42, closes #43, resolves #100`

Cross-repo: `Fixes owner/other-repo#42`

## Anti-Patterns

| Do Not | Do Instead |
|--------|-----------|
| Report security bugs as public issues | Use private vulnerability reporting |
| Close issues without explanation | Always add closing comment with reason |
| Create labels without descriptions | Add description to every label |
| Assign 5+ people to one issue | Max 1-2 assignees; mention teams in comments |
| Use blank issues when templates exist | Set `blank_issues_enabled: false` in config.yml |
| Manually add issues to projects | Use auto-add project workflows |
| Create one giant issue for a feature | Break into sub-issues with parent epic |
| Use closing keywords in non-default branch PRs | Keywords only auto-close from default branch |

## Reference Files

| File | Contents |
|------|----------|
| `references/gh-issue-commands.md` | Complete `gh issue` subcommand reference: status, list, create, view, edit, close, reopen, comment, delete, transfer, lock, unlock, pin, unpin, develop — all flags, JSON fields, examples |
| `references/search-and-filter.md` | `gh search issues` and `gh issue list --search` — all qualifiers, cross-repo search, common search recipes, JSON/JQ extraction |
| `references/issue-templates.md` | Classic templates (.md) and Issue Forms (.yml) — all YAML fields, form element types, config.yml, URL pre-filling, validation errors, production examples |
| `references/labels-milestones-projects.md` | Label taxonomy design, `gh label` commands, milestone strategies, Projects v2 integration, custom fields, issue types, hierarchy view |
| `references/api-and-scripting.md` | `gh api` REST and GraphQL patterns, pagination, JQ recipes, bulk operations, CSV export, aliases, authentication, rate limits |
| `references/automation-actions.md` | GitHub Actions workflows: auto-label, stale management, auto-assign, welcome bot, lock threads, add-to-project, template validation — complete YAML |
| `references/workflows-and-patterns.md` | Issue-Driven Development lifecycle, triage workflow, cross-referencing, sub-issues, Discussion-to-Issue, security advisories, monorepo patterns, anti-patterns |
