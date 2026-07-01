# Worktree Commands

Sources: Official git-scm.com documentation (v2.53.0, 2026), git man pages

Covers: All git worktree subcommands — add, list, remove, prune, lock,
unlock, move, repair — with full option sets, examples, and edge cases.

## How Worktrees Work Internally

Each linked worktree contains a `.git` FILE (not directory) pointing back
to the main repository:

```
main-repo/
└── .git/
    ├── objects/           ← shared across all worktrees
    ├── refs/              ← shared
    ├── config             ← shared
    └── worktrees/         ← per-worktree metadata
        └── feature-auth/
            ├── HEAD       ← this worktree's checked-out commit
            ├── index      ← this worktree's staging area
            └── gitdir     ← path back to the worktree directory

feature-auth-dir/
├── src/
└── .git                   ← FILE containing: "gitdir: ../main-repo/.git/worktrees/feature-auth"
```

Key internals:

| Variable | Points to | Use in hooks/scripts |
|----------|-----------|---------------------|
| `$GIT_DIR` | Worktree-specific `.git` path | Per-worktree state |
| `$GIT_COMMON_DIR` | Shared `.git` directory | Shared resources |

```bash
git rev-parse --git-dir          # worktree-specific path
git rev-parse --git-common-dir   # shared .git directory
git rev-parse --show-toplevel    # current worktree root
```

## git worktree add

Creates a new linked working tree at `<path>` with `<branch>` checked out.

### Synopsis

```
git worktree add [-f] [--detach] [--checkout] [--lock [--reason <string>]]
                 [--orphan] [(-b | -B) <new-branch>] <path> [<commit-ish>]
```

### Common Usage

```bash
# Check out an existing branch
git worktree add ../myproject-hotfix hotfix/login-fix

# Create a NEW branch from a base and check it out
git worktree add -b hotfix/payment-bug ../myproject-hotfix main

# Create new branch from current HEAD
git worktree add -b experiment/new-parser ../parser-experiment

# Detached HEAD at a tag or commit (no branch)
git worktree add --detach ../release-review v2.4.1
git worktree add --detach ../bisect-test abc1234

# Track a remote branch (auto-creates local tracking branch)
git fetch origin
git worktree add ../review-pr origin/feature/new-dashboard

# Create and immediately lock (prevents accidental pruning)
git worktree add --lock --reason "Sprint work" ../feature-dir feature-branch
```

### Options

| Option | Effect |
|--------|--------|
| `-b <branch>` | Create new branch at `<commit-ish>` (default: HEAD) |
| `-B <branch>` | Create or reset branch (like `checkout -B`) |
| `--detach` | Detached HEAD — no branch, just a commit |
| `--checkout` / `--no-checkout` | Whether to populate working files (default: checkout) |
| `--lock [--reason <str>]` | Lock on creation to prevent pruning |
| `--orphan` | Create orphan branch with no history (Git 2.36+) |
| `-f` / `--force` | Override safety checks (branch already checked out, path exists) |
| `--track` / `--no-track` | Whether new branch tracks remote upstream |
| `-q` / `--quiet` | Suppress feedback |

### Behavior Notes

- If `<commit-ish>` is omitted, defaults to HEAD.
- If `<branch>` matches a remote tracking branch (e.g., `origin/feature`),
  git automatically creates a local branch that tracks it.
- Creating a worktree does NOT `cd` into it — you must change directory manually.
- If the project uses submodules, run `git submodule update --init --recursive`
  inside the new worktree after creation.

## git worktree list

Shows all worktrees associated with the repository.

### Synopsis

```
git worktree list [-v | --porcelain [-z]]
```

### Usage

```bash
# Human-readable
git worktree list
# /home/dev/myproject           a1b2c3d [main]
# /home/dev/myproject-hotfix    e4f5g6h [hotfix/login-fix]
# /home/dev/myproject-review    i7j8k9l (detached HEAD)

# Verbose — shows lock status and prunable state
git worktree list -v

# Machine-readable (for scripting)
git worktree list --porcelain

# NUL-terminated (for paths with spaces)
git worktree list --porcelain -z
```

### Porcelain Output Format

```
worktree /home/dev/myproject
HEAD a1b2c3d4e5f6789012345678abcdef1234567890
branch refs/heads/main

worktree /home/dev/myproject-hotfix
HEAD e4f5g6h7i8j9012345678901234567890abcdef
branch refs/heads/hotfix/login-fix
locked reason: Sprint work
```

## git worktree remove

Removes a linked worktree directory and its metadata.

### Synopsis

```
git worktree remove [-f] <worktree>
```

### Usage

```bash
# Safe removal (fails if uncommitted changes or untracked files exist)
git worktree remove ../myproject-hotfix

# Force removal (ignores uncommitted changes)
git worktree remove --force ../myproject-hotfix
```

### Behavior Notes

- Does NOT delete the branch. The branch remains in the repository.
- Cannot remove the main worktree (the original checkout).
- Cannot remove a locked worktree — unlock first.
- Deletes the worktree directory from disk and cleans metadata from
  `.git/worktrees/`.

## git worktree prune

Cleans up stale worktree metadata left behind when directories are manually
deleted (e.g., `rm -rf`).

### Synopsis

```
git worktree prune [-n] [-v] [--expire <expire>]
```

### Usage

```bash
# Prune all stale references
git worktree prune

# Dry run — show what would be pruned without doing it
git worktree prune -n
git worktree prune --dry-run

# Verbose output
git worktree prune -v

# Prune worktrees older than a specific time
git worktree prune --expire 2.weeks.ago
```

### When to Use

- After manually deleting a worktree directory with `rm -rf`
- As part of regular maintenance
- The command is safe — it only removes metadata for worktrees whose
  directories no longer exist. It never deletes branches or commits.

## git worktree lock / unlock

Prevents a worktree from being pruned. Useful for worktrees on removable
media, network drives, or long-running work.

### Synopsis

```
git worktree lock [--reason <string>] <worktree>
git worktree unlock <worktree>
```

### Usage

```bash
# Lock with a reason
git worktree lock --reason "Active sprint, do not prune" ../myproject-feature

# Lock without reason
git worktree lock ../myproject-feature

# Check lock status
git worktree list -v
# Shows "locked" or "locked reason: ..." next to locked worktrees

# Unlock
git worktree unlock ../myproject-feature
```

### Behavior Notes

- Locked worktrees are never removed by `git worktree prune`.
- `git worktree remove` also refuses to remove locked worktrees.
- Unlock before removing: `git worktree unlock ../path && git worktree remove ../path`

## git worktree move

Relocates a linked worktree to a new filesystem path.

### Synopsis

```
git worktree move <worktree> <new-path>
```

### Usage

```bash
git worktree move ../old-location ../new-location
```

### Constraints

- Cannot move the main worktree.
- Cannot move a locked worktree (unlock first).
- Prefer `move` over manual `mv` + `repair` — it updates all internal
  references atomically.

## git worktree repair

Fixes broken links between the main repository and worktrees after manual
filesystem moves.

### Synopsis

```
git worktree repair [<path>...]
```

### Usage

```bash
# Repair all worktree links (run from main repo)
git worktree repair

# Repair specific paths
git worktree repair /new/path/to/worktree1 /new/path/to/worktree2
```

### When to Use

- After moving the main repository directory manually
- After moving a worktree directory with `mv` instead of `git worktree move`
- After symlink changes affecting `.git` paths

## Shared vs Per-Worktree State

Understanding what is shared prevents subtle bugs.

| Resource | Shared? | Notes |
|----------|---------|-------|
| Object database (commits, blobs) | Yes | All history is shared |
| Branch refs | Yes | Creating/deleting branches visible everywhere |
| Tags | Yes | All worktrees see all tags |
| Stash | Yes | Stash from worktree A visible in worktree B |
| Hooks | Yes | Pre-commit runs in all worktrees |
| `.git/config` | Yes | Config changes affect all worktrees |
| HEAD | No | Each worktree has its own checked-out branch |
| Index (staging area) | No | Each worktree stages independently |
| Working files | No | Each worktree has its own file state |
| Submodule checkouts | No | Must `git submodule update` per worktree |
| `node_modules`, build cache | No | Must install dependencies per worktree |
