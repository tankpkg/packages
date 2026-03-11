# Advanced Patterns

Sources: Official Git documentation, ChristopherA's workspace patterns,
production CI/CD worktree deployments, community bare repo conventions

Covers: Bare repo setup, CI/CD patterns, directory layout conventions,
naming strategies, comparison with alternatives, and editor configuration.

## Bare Repo + Worktrees Pattern

The cleanest approach for developers who use worktrees as their primary
workflow. Instead of a regular clone with a main worktree, use a bare repo
as the central store and create named worktrees for each branch.

### Why Bare Repos?

| Aspect | Regular clone | Bare + worktrees |
|--------|--------------|-----------------|
| Accidental checkout in root | Disrupts work | Impossible (no working files) |
| Directory organization | Siblings scatter | All under one parent |
| `git status` in root | Shows main branch files | Nothing (bare has no working tree) |
| `git fetch` scope | Updates local refs | Updates all worktrees' refs |

### Setup from Scratch

```bash
# 1. Create container directory
mkdir myproject && cd myproject

# 2. Clone as bare repo into hidden directory
git clone --bare https://github.com/user/repo.git .bare

# 3. Create a .git file that points to the bare repo
echo "gitdir: ./.bare" > .git

# 4. Configure remote fetch (critical for bare repos)
git config remote.origin.fetch "+refs/heads/*:refs/heads/*"
git fetch origin

# 5. Create worktrees for each branch you need
git worktree add main main
git worktree add develop develop
```

Result:

```
myproject/
├── .bare/              ← bare git repo (object store, refs)
├── .git                ← file: "gitdir: ./.bare"
├── main/               ← main branch worktree
├── develop/            ← develop branch worktree
└── feature-auth/       ← feature branch worktree (created later)
```

### Setup from Existing Clone

```bash
# 1. From existing clone, create bare copy
cd ~/projects
git clone --bare myproject myproject-new/.bare
cd myproject-new

# 2. Set up .git file
echo "gitdir: ./.bare" > .git

# 3. Configure fetch and create worktrees
git config remote.origin.fetch "+refs/heads/*:refs/heads/*"
git fetch origin
git worktree add main main
```

### Working with Bare Repos

```bash
cd myproject

# Create a new feature worktree
git worktree add feature-login -b feature/login main

# List all worktrees
git worktree list

# Remove a completed feature
git worktree remove feature-login
git branch -d feature/login
```

### Shell Function for Bare Repo Clone

```bash
wt-clone() {
  local url="$1"
  local name="${2:-$(basename "$url" .git)}"
  mkdir "$name" && cd "$name"
  git clone --bare "$url" .bare
  echo "gitdir: ./.bare" > .git
  git config remote.origin.fetch "+refs/heads/*:refs/heads/*"
  git fetch origin
  git worktree add main main
  cd main
  echo "Bare repo + main worktree ready in $name/"
}
```

## Directory Layout Conventions

### Pattern 1: Sibling Directories

Simple, works for occasional worktree use:

```
~/projects/
├── myproject/               ← main worktree
├── myproject-hotfix/        ← hotfix worktree
├── myproject-review-pr-42/  ← PR review
└── myproject-experiment/    ← experiment
```

**Naming convention**: `{repo}-{purpose-or-branch}` with slashes converted
to hyphens.

### Pattern 2: Bare Repo Parent

Recommended for regular worktree use:

```
~/projects/myproject/
├── .bare/
├── .git
├── main/
├── develop/
├── feature-auth/
└── hotfix-payment/
```

**Naming convention**: Short directory names matching the branch's last
segment. The parent directory provides the repo context.

### Pattern 3: Workspace Organization

For developers managing many repositories:

```
~/workspace/
├── github.com/
│   ├── myorg/
│   │   ├── frontend/
│   │   │   ├── .bare/
│   │   │   ├── main/
│   │   │   └── feature-nav/
│   │   └── backend/
│   │       ├── .bare/
│   │       ├── main/
│   │       └── hotfix-api/
│   └── personal/
│       └── dotfiles/
│           ├── .bare/
│           └── main/
```

### Naming Best Practices

| Element | Convention | Example |
|---------|-----------|---------|
| Worktree directory | Kebab-case, no slashes | `feature-user-auth` |
| Branch name | Standard git convention | `feature/user-auth` |
| Sibling pattern | `{repo}-{branch-slug}` | `myapp-hotfix-login` |
| Bare repo pattern | Branch last segment | `hotfix-login` |
| Ticket reference | Include ticket ID | `myapp-JIRA-456` |
| AI agent worktree | `agent-{task}` | `agent-auth-refactor` |

## CI/CD Patterns

### Parallel Test Runs

Run tests on multiple branches simultaneously:

```bash
# In CI script
git fetch origin
git worktree add /tmp/test-main main
git worktree add /tmp/test-feature "$BRANCH_NAME"

# Run tests in parallel
(cd /tmp/test-main && npm ci && npm test) &
(cd /tmp/test-feature && npm ci && npm test) &
wait

# Cleanup
git worktree remove /tmp/test-main
git worktree remove /tmp/test-feature
git worktree prune
```

### GitHub Actions Integration

```yaml
jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history needed for worktrees

      - name: Create comparison worktree
        run: |
          git worktree add /tmp/baseline main

      - name: Run tests on both branches
        run: |
          npm ci && npm test &
          (cd /tmp/baseline && npm ci && npm test) &
          wait

      - name: Cleanup
        if: always()
        run: |
          git worktree remove /tmp/baseline || true
          git worktree prune
```

### Server Deployment Pattern

Keep multiple environments as persistent worktrees:

```bash
# Initial setup on server
cd /srv/repos
git clone --bare https://github.com/org/app.git app.git
cd app.git

# Create environment worktrees
git worktree add /var/www/production main
git worktree add /var/www/staging staging
git worktree add /var/www/preview preview

# Lock production
git worktree lock --reason "Production deployment" /var/www/production

# Deploy script
deploy() {
  local env="$1"
  cd "/var/www/$env"
  git pull origin "$env"
  npm ci --production
  npm run build
  pm2 restart "$env"
}
```

## Worktrees vs Alternatives

### vs git stash

| Factor | `git stash` | `git worktree` |
|--------|------------|----------------|
| Speed | Instant | Seconds (+ dependency install) |
| Parallel work | No — sequential | Yes — true parallel |
| Risk | Medium — stash can be dropped | Low — full working copy |
| Context loss | High — mental context switch | None — separate directory |
| Disk usage | Minimal | Working copy per worktree |
| Best for | Quick 1-file fixes | Multi-file, multi-hour work |

### vs git clone

| Factor | `git clone` | `git worktree` |
|--------|------------|----------------|
| Disk usage | Full repo copy | Shared object store |
| Sync | Manual `git pull` each | `git fetch` syncs all |
| History | Independent copy | Shared history |
| Setup time | Slow (full download) | Fast (local refs) |
| Best for | Full isolation (CI, configs) | Same-repo parallel work |

### vs git branch + checkout

| Factor | `checkout` | `worktree` |
|--------|-----------|------------|
| Working directory | Shared (one at a time) | Separate (parallel) |
| Build cache | Lost on switch | Preserved per worktree |
| Editor state | Disrupted | Preserved per window |
| Mental context | Lost on switch | Preserved per terminal |
| Best for | Linear, sequential work | Parallel, interleaved work |

## Git Configuration for Worktrees

### Worktree-Specific Config

Git 2.20+ supports per-worktree configuration:

```bash
# Set config only for the current worktree
git config --worktree core.sparseCheckout true
git config --worktree receive.denyCurrentBranch ignore
```

Per-worktree config is stored in `.git/worktrees/<name>/config.worktree`.

### Recommended Global Config

```ini
# ~/.gitconfig
[alias]
  wt = worktree
  wtl = worktree list
  wta = worktree add
  wtr = worktree remove
  wtp = worktree prune
  wt-clean = "!git worktree prune && git worktree list"

[worktree]
  # Enable per-worktree config (Git 2.20+)
  guessRemote = true
```

The `worktree.guessRemote` option makes `git worktree add` automatically
set up tracking for remote branches without explicit `origin/` prefix.

## Sparse Checkout with Worktrees

For large monorepos, combine sparse checkout with worktrees to reduce
disk usage and checkout time:

```bash
# Create worktree without populating files
git worktree add --no-checkout ../myproject-feature feature/auth

# Configure sparse checkout in the new worktree
cd ../myproject-feature
git sparse-checkout init --cone
git sparse-checkout set packages/auth packages/shared

# Only the specified directories are checked out
git checkout  # populates the sparse set
```

This is useful for monorepos where each worktree only needs a subset
of the codebase.

## Multi-Agent Development Pattern

When multiple AI agents work on the same repository simultaneously, each
agent needs isolation to prevent file conflicts. Worktrees provide this
without the overhead of separate clones.

### Architecture

```
myproject/
├── .bare/                        ← shared object store
├── .git
├── main/                         ← human development
├── agent-auth/                   ← Agent 1: auth feature
├── agent-tests/                  ← Agent 2: test coverage
└── agent-perf/                   ← Agent 3: performance optimization
```

### Merge Strategy

Merge agents' work sequentially to catch conflicts early:

```bash
cd main
git merge agent/auth-feature       # merge first agent's work
# resolve any conflicts
git worktree remove ../agent-auth
git branch -d agent/auth-feature

git merge agent/test-suite         # merge second
git worktree remove ../agent-tests
git branch -d agent/test-suite

git merge agent/perf-optimization  # merge third
git worktree remove ../agent-perf
git branch -d agent/perf-optimization

git worktree prune
```

### Coordination Rules

- Each agent works on a distinct directory/module to minimize conflicts
- Agents should fetch and rebase periodically to stay current
- Merge in dependency order (shared code first, dependent code second)
- Always clean up worktrees after merging each agent's work
