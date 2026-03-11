# Cleanup and Lifecycle

Sources: Official Git documentation, production worktree management patterns,
community best practices for worktree hygiene

Covers: The full worktree lifecycle, cleanup protocol, proactive reminder
behavior, pruning strategies, automation aliases, and sprint-end audits.

## The Worktree Lifecycle

Every worktree follows this lifecycle. Deviating from it — especially
skipping cleanup — leads to worktree sprawl.

```
CREATE  →  SETUP  →  WORK  →  RESOLVE  →  CLEANUP
  │          │         │         │           │
  │          │         │         │           ├─ remove worktree
  │          │         │         │           ├─ delete branch
  │          │         │         │           └─ prune metadata
  │          │         │         │
  │          │         │         ├─ push branch
  │          │         │         ├─ open PR
  │          │         │         └─ merge (or close)
  │          │         │
  │          │         └─ normal git add/commit cycle
  │          │
  │          ├─ install dependencies
  │          ├─ init submodules (if needed)
  │          └─ open in editor
  │
  ├─ git fetch origin
  └─ git worktree add ...
```

## Cleanup Protocol

This is the standard cleanup sequence. Run after every resolved worktree task.

### Step 1: Confirm Resolution

Before cleaning up, verify the work is done:

```bash
# Check if branch was merged
git log --oneline main..feature/branch-name
# Empty output = fully merged

# Check if PR is merged (GitHub)
gh pr status
# or
gh pr view <number> --json state -q '.state'
```

### Step 2: Remove the Worktree

```bash
# Safe removal (fails if uncommitted changes exist)
git worktree remove ../myproject-feature

# If uncommitted changes exist and you're sure you want to discard
git worktree remove --force ../myproject-feature
```

### Step 3: Delete the Branch

Only delete branches you own and that have been merged:

```bash
# Safe delete (fails if not merged)
git branch -d feature/branch-name

# Force delete (for unmerged experiments)
git branch -D experiment/approach-a
```

Do NOT delete branches you don't own (e.g., a teammate's PR branch).

### Step 4: Prune Stale Metadata

```bash
git worktree prune
```

This is a safety net — it cleans up metadata for worktrees whose directories
were removed outside of git (e.g., `rm -rf`). Always run after removal.

### Step 5: Verify Clean State

```bash
git worktree list
```

Should show only actively-used worktrees. If stale entries remain, repeat
steps 2-4.

## Proactive Cleanup Behavior

The agent should prompt for cleanup after completing any worktree-based task.
This is the key behavior that prevents worktree sprawl.

### When to Prompt

| Event | Prompt cleanup? |
|-------|----------------|
| Hotfix merged | Yes — remove worktree + delete branch |
| PR review completed | Yes — remove worktree (keep branch) |
| Experiment decided | Yes — remove loser worktree + delete branch |
| Feature branch merged | Yes — remove worktree + delete branch |
| Bisect completed | Yes — remove worktree |
| Tests finished running | Yes — remove worktree |
| User says "done" or "finished" | Yes — offer cleanup |

### Prompt Template

After the task is resolved:

```
The worktree work is complete. To keep your workspace clean:

1. Remove worktree: git worktree remove <path>
2. Delete branch: git branch -d <branch>
3. Prune stale refs: git worktree prune

Want me to run these cleanup commands?
```

Adapt the template based on context — omit "delete branch" if the branch
belongs to someone else (e.g., PR review).

### When NOT to Prompt

- Deployment worktrees (persistent, locked)
- Worktrees the user explicitly said to keep
- Active work still in progress

## Handling Stale Worktrees

When a user has accumulated stale worktrees, help them audit and clean.

### Audit Command

```bash
git worktree list -v
```

For each worktree shown, check:

| Check | How | Action if stale |
|-------|-----|-----------------|
| Directory still exists? | `ls <path>` | `git worktree prune` |
| Branch merged? | `git log --oneline main..<branch>` | Remove + delete branch |
| PR closed? | `gh pr list --head <branch>` | Remove + delete branch |
| Last commit date? | `git log -1 --format=%cr <branch>` | If >2 weeks, flag as stale |
| Any uncommitted changes? | `git -C <path> status --short` | Warn user before removing |

### Bulk Cleanup Script

For users with many stale worktrees:

```bash
# List all worktrees except the main one
git worktree list --porcelain | grep "^worktree " | tail -n +2 | sed 's/^worktree //'

# For each, check if it should be removed:
for wt in $(git worktree list --porcelain | grep "^worktree " | tail -n +2 | sed 's/^worktree //'); do
  branch=$(git -C "$wt" branch --show-current 2>/dev/null)
  echo "$wt → $branch"
done
```

Present findings to the user before running any removal commands.

## Automation: Git Aliases

Recommend these aliases for users who work with worktrees regularly:

```ini
# ~/.gitconfig
[alias]
  # Short aliases
  wt = worktree
  wtl = worktree list
  wta = worktree add
  wtr = worktree remove
  wtp = worktree prune

  # Combined operations
  wt-clean = "!git worktree prune && git worktree list"
```

## Automation: Shell Functions

For power users, suggest these shell functions:

```bash
# Create worktree with repo-name prefix
wt-new() {
  local branch="$1"
  local base="${2:-main}"
  local repo
  repo=$(basename "$(git rev-parse --show-toplevel)")
  local dir="../${repo}-${branch//\//-}"
  git fetch origin
  git worktree add -b "$branch" "$dir" "$base"
  echo "Created worktree at $dir on branch $branch"
  echo "Run: cd $dir"
}

# Remove worktree and optionally delete branch
wt-done() {
  local path="${1:-.}"
  local abs_path
  abs_path=$(cd "$path" 2>/dev/null && pwd)
  local branch
  branch=$(git -C "$path" branch --show-current 2>/dev/null)

  # Go to main repo first
  local main_wt
  main_wt=$(git worktree list --porcelain | head -1 | sed 's/^worktree //')
  cd "$main_wt" || return 1

  git worktree remove "$abs_path"
  if [ -n "$branch" ]; then
    echo "Delete branch '$branch'? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
      git branch -d "$branch" 2>/dev/null || git branch -D "$branch"
    fi
  fi
  git worktree prune
  git worktree list
}

# Show status of all worktrees
wt-status() {
  echo "=== Worktrees ==="
  git worktree list
  echo ""
  for dir in $(git worktree list --porcelain | grep "^worktree " | tail -n +2 | sed 's/^worktree //'); do
    echo "--- $dir ---"
    git -C "$dir" status --short 2>/dev/null || echo "  (directory missing)"
    echo ""
  done
}
```

## Sprint-End Audit

At the end of a sprint or work cycle, run a full audit:

```bash
# 1. List all worktrees
git worktree list -v

# 2. For each non-main worktree, check:
#    - Is the branch merged?
#    - Is the PR closed?
#    - When was the last commit?

# 3. Remove all stale worktrees
git worktree remove ../path-1
git worktree remove ../path-2
# ...

# 4. Delete merged branches
git branch -d branch-1
git branch -d branch-2

# 5. Final prune
git worktree prune

# 6. Verify clean state
git worktree list
# Should only show the main worktree (and any active work)
```

## Disk Space Considerations

Each worktree consumes disk for:

| Item | Shared? | Size impact |
|------|---------|-------------|
| Git objects (commits, blobs) | Yes | Zero additional |
| Working files (source code) | No | ~= repo size |
| `node_modules` | No | Can be 200MB+ per worktree |
| Build artifacts (`dist/`, `.next/`) | No | Varies |
| Submodule checkouts | No | Can be large |

### Reducing Disk Impact

```bash
# Use pnpm instead of npm (global package store)
pnpm install  # shares packages across worktrees

# Use sparse checkout for large repos
git -C ../new-worktree sparse-checkout set src/ tests/

# Skip checkout for metadata-only operations
git worktree add --no-checkout ../temp-worktree branch
```

## Lifecycle Decision Tree

| Situation | Correct action |
|-----------|---------------|
| Work is merged, PR closed | Remove worktree + delete branch + prune |
| Work is merged, branch shared | Remove worktree + prune (keep branch) |
| PR rejected, work abandoned | Remove worktree + force-delete branch + prune |
| Work paused, will resume later | Keep worktree (optionally lock it) |
| Worktree directory manually deleted | Run `git worktree prune` |
| Deployment worktree | Lock it, never remove |
| Can't remove — uncommitted changes | Commit, stash, or force-remove |
| Can't remove — worktree is locked | Unlock first, then remove |
