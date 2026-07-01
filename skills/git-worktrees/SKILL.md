---
name: "@tank/git-worktrees"
description: |
  Git worktree lifecycle management — create, work, resolve, clean up. Covers
  all git worktree subcommands (add, list, remove, prune, lock, unlock, move,
  repair), common workflows (hotfix while on feature, PR review, parallel
  development, AI agent isolation), directory layout conventions, bare repo
  patterns, and proactive cleanup to prevent worktree sprawl. Synthesizes
  official Git documentation (v2.53+), production worktree patterns, and
  multi-agent development workflows.

  Trigger phrases: "git worktree", "worktree", "worktrees", "git worktree add",
  "git worktree remove", "git worktree list", "git worktree prune",
  "parallel branches", "work on two branches", "hotfix while on feature",
  "review PR without switching", "multiple working directories",
  "branch already checked out", "clean up worktrees", "remove worktree",
  "bare repo worktrees", "worktree cleanup", "too many worktrees",
  "context switch without stash", "isolated working directory"
---

# Git Worktrees

Manage the full worktree lifecycle: create → work → resolve → clean up.

## Core Philosophy

1. **Worktrees are temporary.** Create for a task, remove when done. Lingering
   worktrees waste disk and create confusion.
2. **One branch, one worktree.** Git enforces this — a branch can only be
   checked out in one worktree at a time.
3. **Always clean up.** After merging or closing a PR, ask the user to remove
   the worktree and delete the branch. Never leave stale worktrees behind.
4. **Fetch before creating.** Run `git fetch origin` before `git worktree add`
   to ensure you have current remote state.
5. **Dependencies are per-worktree.** Each worktree needs its own `npm install`,
   `pip install`, etc. — build artifacts are not shared.

## Lifecycle

```
1. CREATE  →  git worktree add (new directory, new or existing branch)
     ↓
2. WORK    →  normal git workflow inside the worktree
     ↓
3. RESOLVE →  push, open PR, merge
     ↓
4. CLEANUP →  git worktree remove + git branch -d + git worktree prune
```

After step 3, prompt the user:

> The worktree task is complete. Want me to clean up?
> - Remove worktree: `git worktree remove <path>`
> - Delete branch: `git branch -d <branch>`
> - Prune stale refs: `git worktree prune`

See `references/cleanup-and-lifecycle.md` for the full cleanup protocol.

## Quick-Start

### "I need to fix a bug without losing my current work"

```bash
git fetch origin
git worktree add -b hotfix/issue-123 ../myproject-hotfix main
cd ../myproject-hotfix
# ... fix, commit, push, open PR ...
```

After merge → clean up. See `references/workflows.md`.

### "I want to review a PR without switching branches"

```bash
git fetch origin
git worktree add ../myproject-review origin/feature/their-branch
cd ../myproject-review
# ... review, run tests ...
```

After review → clean up. See `references/workflows.md`.

### "Branch already checked out" error

A branch can only live in one worktree. Either remove the existing worktree
or create a new branch:

```bash
git worktree remove /path/to/existing-worktree
# or
git worktree add -b new-branch-name ../path main
```

See `references/pitfalls-and-troubleshooting.md`.

### "I have too many old worktrees"

```bash
git worktree list              # audit what exists
git worktree remove ../stale   # remove each stale one
git worktree prune             # clean up broken references
```

See `references/cleanup-and-lifecycle.md`.

## Decision Trees

### When to use a worktree vs alternatives

| Scenario | Use | Why |
|----------|-----|-----|
| Quick hotfix while on a feature | Worktree | No stash/context loss |
| Review a PR | Worktree | Isolated test environment |
| Parallel development on 2+ features | Worktree | True parallel work |
| Quick one-file fix on same branch | `git stash` | Faster for trivial changes |
| Full project isolation (CI, different configs) | `git clone` | Separate git history |
| Experiment you might throw away | Worktree (detached) | Easy cleanup |

### Directory layout

| Team size | Pattern | Setup |
|-----------|---------|-------|
| Solo / small | Sibling directories | `../myproject-hotfix` next to `../myproject` |
| Power users / teams | Bare repo + subdirectories | All worktrees under one parent |

See `references/advanced-patterns.md` for bare repo setup.

### Cleanup timing

| Event | Action |
|-------|--------|
| PR merged | Remove worktree + delete branch + prune |
| PR closed without merge | Remove worktree + delete branch + prune |
| Review complete | Remove worktree (branch belongs to author) |
| Experiment abandoned | Remove worktree + force-delete branch |
| End of sprint | Audit `git worktree list`, remove all stale |

## Command Quick Reference

```bash
# Create
git worktree add ../path branch              # existing branch
git worktree add -b new-branch ../path main  # new branch from base
git worktree add --detach ../path v1.0.0     # detached HEAD at tag/commit

# Inspect
git worktree list                            # list all worktrees
git worktree list -v                         # verbose (shows locks)

# Remove
git worktree remove ../path                  # safe remove
git worktree remove -f ../path               # force (discards changes)

# Maintain
git worktree prune                           # clean stale metadata
git worktree lock ../path                    # prevent accidental prune
git worktree unlock ../path                  # allow prune again
git worktree move ../old ../new              # relocate worktree
git worktree repair                          # fix broken links
```

Full command reference in `references/worktree-commands.md`.

## Cleanup Behavior

After completing any worktree-based task, follow this protocol:

1. Confirm the work is merged or no longer needed.
2. Offer to run cleanup commands for the user.
3. List remaining worktrees so the user can audit.

This prevents worktree sprawl — the #1 problem with worktree adoption.

See `references/cleanup-and-lifecycle.md` for automation and aliases.

## Reference Files

| File | Contents |
|------|----------|
| `references/worktree-commands.md` | Complete command reference for all subcommands with options, examples, and edge cases |
| `references/workflows.md` | Step-by-step workflows: hotfix, PR review, parallel development, bisect, AI agent isolation |
| `references/cleanup-and-lifecycle.md` | Cleanup protocol, proactive reminders, pruning, aliases, automation, sprint-end audit |
| `references/pitfalls-and-troubleshooting.md` | Common errors, branch conflicts, submodule issues, stash confusion, IDE integration |
| `references/advanced-patterns.md` | Bare repo setup, CI/CD patterns, directory conventions, naming, editor integration |
