# Pitfalls and Troubleshooting

Sources: Official Git documentation, Stack Overflow common issues,
community worktree adoption reports

Covers: Common errors, branch conflicts, submodule issues, stash confusion,
dependency management, IDE integration, and recovery procedures.

## Error: Branch Already Checked Out

The most common worktree error. Git enforces one-branch-per-worktree.

```
fatal: 'feature/auth' is already checked out at '/path/to/existing-worktree'
```

### Solutions

| Approach | When to use | Command |
|----------|-------------|---------|
| Remove existing worktree | Work on that branch is done | `git worktree remove /path/to/existing-worktree` |
| Use a different branch | Need a fresh start | `git worktree add -b feature/auth-v2 ../path main` |
| Check out in place | Want to switch to that worktree | `cd /path/to/existing-worktree` |
| Force (dangerous) | Understand the risks | `git worktree add -f ../path feature/auth` |

Forcing is dangerous — two worktrees on the same branch means changes in one
are invisible to the other until committed, leading to confusing merge conflicts.

## Error: Cannot Delete Branch Checked Out in Worktree

```
error: Cannot delete branch 'feature/auth' checked out at '/path/to/worktree'
```

### Solution

Remove the worktree first, then delete the branch:

```bash
git worktree remove /path/to/worktree
git branch -d feature/auth
```

## Error: Path Already Exists

```
fatal: '/path/to/dir' already exists
```

### Solutions

```bash
# If the directory is from a previously removed worktree
rm -rf /path/to/dir
git worktree prune
git worktree add /path/to/dir branch

# If you want to reuse the path
git worktree add -f /path/to/dir branch
```

## Pitfall: Manually Deleting Worktree Directories

Deleting a worktree directory with `rm -rf` leaves stale metadata in
`.git/worktrees/`. Git still thinks the worktree exists.

```bash
# WRONG
rm -rf ../myproject-hotfix
git worktree list  # still shows the deleted path

# FIX
git worktree prune

# RIGHT (always use git's command)
git worktree remove ../myproject-hotfix
```

## Pitfall: Submodule Initialization

New worktrees do NOT automatically initialize submodules. Submodule
directories will be empty.

```bash
# After creating a worktree
git worktree add ../myproject-feature feature/new-ui
cd ../myproject-feature

# Submodule directories are EMPTY at this point
git submodule update --init --recursive  # REQUIRED

# For repos with many submodules, init only what you need
git submodule update --init frontend backend
```

Each worktree maintains its own submodule state. Updating a submodule in
one worktree does not affect others.

## Pitfall: Stash Confusion

Stashes are shared across all worktrees because they live in the common
`.git` directory. A stash created in worktree A is visible in worktree B.

```bash
# In worktree A
cd ../myproject-feature-a
git stash push -m "WIP on feature A"

# In worktree B — this stash is visible
cd ../myproject-feature-b
git stash list
# stash@{0}: On feature-a: WIP on feature A
```

### Prevention

Always use descriptive stash messages that include the worktree context:

```bash
git stash push -m "worktree:feature-a — WIP auth validation"
```

### Recovery

If you apply the wrong stash, undo with:

```bash
git stash show -p stash@{0}  # preview before applying
git checkout -- .             # discard all working tree changes
```

## Pitfall: Dependency and Build Artifact Isolation

Each worktree has its own working files. Dependencies and build artifacts
are NOT shared.

| Language/Tool | Action needed per worktree |
|--------------|--------------------------|
| Node.js (npm/yarn) | `npm install` or `yarn install` |
| Node.js (pnpm) | `pnpm install` (shares global store — less disk) |
| Python (pip) | `pip install -r requirements.txt` |
| Python (poetry) | `poetry install` |
| Go | `go mod download` |
| Rust | `cargo build` (redownloads dependencies) |
| Java (Maven) | `mvn install` |
| Ruby (Bundler) | `bundle install` |

### Disk Space Impact

With npm, each worktree gets its own `node_modules`. For a project with
200MB of dependencies and 5 worktrees, that's 1GB just for `node_modules`.

**Mitigation**:

```bash
# Use pnpm — shares packages via global content-addressable store
pnpm install  # each worktree's node_modules uses symlinks, ~10MB per worktree

# Use Yarn PnP — no node_modules at all
yarn install  # uses .pnp.cjs for resolution
```

## Pitfall: Locked Worktrees Blocking Operations

Locked worktrees cannot be removed or pruned. If you forget about a lock,
cleanup commands silently skip the locked worktree.

```bash
# Check for locks
git worktree list -v
# /path/to/worktree  abc1234 [feature/old]  locked reason: Sprint work

# Unlock before removing
git worktree unlock ../myproject-feature
git worktree remove ../myproject-feature
```

## Pitfall: Hooks Running in All Worktrees

Hooks live in `.git/hooks/` which is shared. A pre-commit hook runs in
every worktree. This is usually desired, but can cause issues:

| Issue | Cause | Fix |
|-------|-------|-----|
| Hook fails in new worktree | Hook references absolute paths | Use `$(git rev-parse --show-toplevel)` |
| Hook references wrong `.git` | Uses `$GIT_DIR` directly | Use `$(git rev-parse --git-common-dir)` for shared resources |
| Hook installs dependencies | Runs `npm install` in pre-commit | Add `node_modules` check before install |
| Husky hooks missing | Husky needs `.husky/` in worktree root | Run `npx husky install` in new worktree |

### Portable Hook Pattern

```bash
#!/bin/sh
# Use relative paths in hooks
REPO_ROOT=$(git rev-parse --show-toplevel)
COMMON_DIR=$(git rev-parse --git-common-dir)

# For worktree-specific paths (e.g., check staged files)
cd "$REPO_ROOT"

# For shared resources (e.g., config files in .git/)
cat "$COMMON_DIR/config"
```

## Pitfall: Moving Repos Without Repair

If the main repository or a worktree directory is moved with `mv` instead
of `git worktree move`, the internal links break.

```bash
# Moved main repo
mv ~/projects/myproject ~/code/myproject

# Worktrees now have broken links
cd ~/code/myproject
git worktree list  # shows old paths

# Fix
git worktree repair
```

```bash
# Moved a worktree directory
mv ~/projects/myproject-feature ~/elsewhere/myproject-feature

# Fix from main repo
cd ~/code/myproject
git worktree repair ~/elsewhere/myproject-feature
```

## Pitfall: Bare Repo Remote Tracking

Bare repos created with `git clone --bare` don't set up remote tracking
correctly by default.

```bash
# After cloning bare
git clone --bare https://github.com/user/repo.git .bare

# New worktrees won't track remote branches
git worktree add ../feature feature-branch
cd ../feature
git pull  # error: no tracking information

# Fix: configure fetch refspec
git config remote.origin.fetch "+refs/heads/*:refs/heads/*"
git fetch origin

# Set upstream for existing worktree branch
git branch -u origin/feature-branch
```

Always configure the fetch refspec immediately after creating a bare clone.

## IDE and Editor Integration

### VS Code

VS Code works well with worktrees — open each as a separate window:

```bash
code ../myproject-feature
```

**Known issues**:
- Extensions may conflict if both windows use the same global state
- File watchers can strain CPU with many worktrees open
- Git extension shows only the current worktree's branch

**Recommendation**: One VS Code window per worktree. Close windows for
removed worktrees.

### JetBrains IDEs

Native worktree support via **Git > Manage Worktrees** menu.

**Known issues**:
- IDE indexes each worktree separately (CPU/RAM cost)
- Project settings are per-directory, not per-worktree
- Opening multiple worktrees of the same project requires multiple IDE
  instances

### Neovim

The `git-worktree.nvim` plugin by ThePrimeagen adds telescope integration:

```lua
-- Quick switch between worktrees
require("telescope").extensions.git_worktree.git_worktrees()

-- Create new worktree from telescope
require("telescope").extensions.git_worktree.create_git_worktree()
```

### Terminal Multiplexers (tmux, zellij)

Pair each worktree with its own tmux session or pane:

```bash
# Create worktree + tmux session
wt-tmux() {
  local branch="$1"
  local base="${2:-main}"
  local repo=$(basename "$(git rev-parse --show-toplevel)")
  local dir="../${repo}-${branch//\//-}"
  local session="${repo}-${branch//\//-}"

  git worktree add -b "$branch" "$dir" "$base"
  tmux new-session -d -s "$session" -c "$dir"
  tmux switch-client -t "$session"
}
```

## Recovery Procedures

### Recovering Work from a Force-Removed Worktree

If you force-removed a worktree with uncommitted changes:

```bash
# The branch still exists with its last commit
git log --oneline feature/branch-name

# Uncommitted changes are GONE (force-remove discarded them)
# If you had staged changes, they might be in git's reflog
git fsck --lost-found
# Check .git/lost-found/other/ for recovered blobs
```

### Recovering from Corrupted Worktree State

If `git worktree list` shows incorrect information:

```bash
# Nuclear option: prune everything and re-verify
git worktree prune
git worktree list

# If still broken, manually clean .git/worktrees/
ls .git/worktrees/
# Remove directories for worktrees that no longer exist
rm -rf .git/worktrees/stale-worktree-name
```

### Fixing "Not a git repository" in Worktree

If a worktree's `.git` file is corrupted:

```bash
# Check the .git file contents
cat ../myproject-feature/.git
# Should contain: gitdir: /path/to/main/.git/worktrees/feature-name

# If missing or wrong, recreate it
echo "gitdir: /path/to/main/.git/worktrees/feature-name" > ../myproject-feature/.git

# Then repair from main repo
cd /path/to/main
git worktree repair
```
