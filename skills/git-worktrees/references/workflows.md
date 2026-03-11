# Workflows

Sources: Official Git documentation, production worktree patterns, multi-agent
development workflows (2025-2026)

Covers: Step-by-step workflows for hotfix, PR review, parallel development,
bisect, long-running tests, and AI agent isolation.

## Workflow 1: Hotfix While Working on a Feature

The most common worktree use case. You're deep in feature work, a production
bug is reported, and you need to fix it without losing context.

```bash
# 1. From your main repo (you're on feature/new-dashboard)
git fetch origin

# 2. Create hotfix worktree from main
git worktree add -b hotfix/payment-timeout ../myproject-hotfix main

# 3. Switch terminal to the hotfix
cd ../myproject-hotfix

# 4. Install dependencies (not shared between worktrees)
npm install  # or pip install, go mod download, etc.

# 5. Fix the bug
# ... edit files ...
git add -A
git commit -m "fix: resolve payment processing timeout"

# 6. Push and open PR
git push -u origin hotfix/payment-timeout
# Open PR, get review, merge

# 7. CLEANUP (after merge)
cd ../myproject  # back to main repo
git worktree remove ../myproject-hotfix
git branch -d hotfix/payment-timeout
git worktree prune
```

Your feature branch is exactly as you left it. No stashing, no lost context.

## Workflow 2: PR Review Without Context Switching

Review a teammate's PR in an isolated environment without disrupting your work.

```bash
# 1. Fetch latest remote state
git fetch origin

# 2. Create review worktree from the PR branch
git worktree add ../myproject-review origin/feature/user-auth

# 3. Open in editor and review
cd ../myproject-review
code .  # or your preferred editor

# 4. Install dependencies and run tests
npm install
npm test

# 5. Leave review comments on the PR

# 6. CLEANUP (after review is complete)
cd ../myproject
git worktree remove ../myproject-review
git worktree prune
```

The branch belongs to the PR author, so don't delete it — only remove the
worktree.

## Workflow 3: Parallel Feature Development

Work on two features simultaneously, running tests on one while coding on
the other.

```bash
# 1. Create worktrees for both features
git worktree add -b feature/auth ../myproject-auth main
git worktree add -b feature/payments ../myproject-payments main

# 2. Work on auth in one terminal
cd ../myproject-auth
npm install
# ... develop ...

# 3. Work on payments in another terminal
cd ../myproject-payments
npm install
# ... develop ...

# 4. CLEANUP (as each feature completes)
cd ../myproject
git worktree remove ../myproject-auth
git branch -d feature/auth  # after merge
git worktree remove ../myproject-payments
git branch -d feature/payments  # after merge
git worktree prune
```

## Workflow 4: A/B Experiment Comparison

Try two different approaches to the same problem, benchmark, pick a winner.

```bash
# 1. Create both experiment worktrees
git worktree add -b experiment/approach-a ../myproject-approach-a main
git worktree add -b experiment/approach-b ../myproject-approach-b main

# 2. Implement approach A
cd ../myproject-approach-a
# ... implement ...

# 3. Implement approach B
cd ../myproject-approach-b
# ... implement ...

# 4. Compare, benchmark, decide

# 5. CLEANUP — remove loser, keep winner
cd ../myproject
git worktree remove ../myproject-approach-a
git branch -D experiment/approach-a  # force delete, never merged

# Continue with approach-b or merge it
git merge experiment/approach-b
git worktree remove ../myproject-approach-b
git branch -d experiment/approach-b
git worktree prune
```

## Workflow 5: Bisect in Isolation

Run `git bisect` without disturbing your current working tree.

```bash
# 1. Create detached worktree for bisecting
git worktree add --detach ../myproject-bisect HEAD

# 2. Run bisect
cd ../myproject-bisect
git bisect start
git bisect bad HEAD
git bisect good v2.0.0
# ... git bisect marks commits good/bad ...
# ... until the culprit commit is found ...
git bisect reset

# 3. CLEANUP
cd ../myproject
git worktree remove ../myproject-bisect
git worktree prune
```

## Workflow 6: Long-Running Tests on Another Branch

Run a full test suite on main while continuing to develop.

```bash
# 1. Create test worktree
git worktree add ../myproject-tests main

# 2. Run tests in background terminal
cd ../myproject-tests
npm install
npm test -- --watchAll  # long-running test suite

# 3. Continue development in your main worktree
cd ../myproject
# ... code, commit, etc ...

# 4. CLEANUP (when tests are done)
cd ../myproject
git worktree remove ../myproject-tests
git worktree prune
```

## Workflow 7: AI Agent Isolation

Give each AI coding agent its own isolated worktree to prevent file
conflicts when agents work in parallel.

```bash
# 1. Create worktrees for each agent task
git worktree add -b agent/auth-feature ../myproject-agent-auth main
git worktree add -b agent/test-suite ../myproject-agent-tests main
git worktree add -b agent/api-refactor ../myproject-agent-api main

# 2. Point each agent at its worktree directory
# Claude Code, Cursor, or other AI tools operate in each directory

# 3. Merge results one at a time
cd ../myproject
git merge agent/auth-feature
git worktree remove ../myproject-agent-auth
git branch -d agent/auth-feature

git merge agent/test-suite
git worktree remove ../myproject-agent-tests
git branch -d agent/test-suite

git merge agent/api-refactor
git worktree remove ../myproject-agent-api
git branch -d agent/api-refactor

# 4. Final cleanup
git worktree prune
```

## Workflow 8: Staging + Production Deployment

Keep multiple environments checked out simultaneously on a server.

```bash
# 1. Set up deployment worktrees
git worktree add /var/www/staging staging
git worktree add /var/www/production main

# Lock production to prevent accidental removal
git worktree lock --reason "Production deployment" /var/www/production

# 2. Deploy to staging
cd /var/www/staging
git pull origin staging
npm run build && pm2 restart staging

# 3. Deploy to production
cd /var/www/production
git pull origin main
npm run build && pm2 restart production
```

These worktrees are persistent — do NOT clean them up.

## Workflow Comparison Table

| Workflow | Worktree type | Branch type | Cleanup timing |
|----------|--------------|-------------|----------------|
| Hotfix | Linked, new branch | `hotfix/*` | After PR merge |
| PR review | Linked, remote tracking | Remote branch | After review |
| Parallel features | Linked, new branches | `feature/*` | After each merge |
| A/B experiment | Linked, new branches | `experiment/*` | After decision |
| Bisect | Detached HEAD | None | After bisect reset |
| Long-running tests | Linked, existing branch | `main` or target | After tests done |
| AI agents | Linked, new branches | `agent/*` | After each merge |
| Deployment | Linked, existing branches | `main`, `staging` | Never (persistent) |

## Post-Workflow Cleanup Checklist

After any workflow completes:

1. **Remove the worktree**: `git worktree remove ../path`
2. **Delete the branch** (if you own it and it's merged): `git branch -d branch-name`
3. **Prune stale metadata**: `git worktree prune`
4. **Verify**: `git worktree list` — only active worktrees should remain

If the branch wasn't merged and you want to force-delete:

```bash
git branch -D branch-name  # uppercase -D forces deletion
```

If the worktree has uncommitted changes and you want to force-remove:

```bash
git worktree remove --force ../path
```
