---
name: "@tank/github-actions-mastery"
description: |
  GitHub Actions workflow authoring, optimization, and security for any project.
  Covers workflow syntax (triggers, jobs, steps, expressions, contexts), reusable
  workflows and composite actions, matrix strategies (static and dynamic), caching
  (actions/cache, setup-* built-in), secrets and environment management (OIDC,
  deployment protection rules), self-hosted runners (ARC, labels, auto-scaling),
  security hardening (SHA pinning, least-privilege permissions, supply chain),
  monorepo patterns (path filtering, affected detection, conditional jobs),
  concurrency control, and CI/CD recipes (test, lint, deploy, release, Docker
  multi-platform build/push).

  Synthesizes GitHub Actions official documentation (2026), GitHub Security
  Hardening guide, actions/cache and actions/runner-controller docs, Docker
  Build/Push Actions docs, and production CI/CD patterns.

  Trigger phrases: "github actions", "github actions workflow", "github actions
  best practices", "github actions monorepo", "github actions cache",
  "github actions secrets", "github actions matrix", "github actions reusable
  workflow", "github actions composite action", "github actions self-hosted
  runner", "github actions security", "github actions deploy", "github actions
  docker", "github actions OIDC", "github actions permissions",
  "github actions concurrency", "workflow_dispatch", "act local testing",
  "github actions cheat sheet", "CI/CD pipeline github"
---

# GitHub Actions Mastery

## Core Philosophy

1. **Minimal permissions by default** — Set top-level `permissions: {}` and grant per-job. GITHUB_TOKEN with broad access is the most common vulnerability in public repos.
2. **Pin everything to SHA** — Tags are mutable. A compromised action tag silently injects malicious code. Pin third-party actions to full commit SHA and use Dependabot or Renovate to update.
3. **Cache aggressively, invalidate precisely** — CI minutes are money. Cache dependencies, build artifacts, and tool installations. Use `hashFiles()` for cache keys to auto-bust on lockfile changes.
4. **Run only what changed** — In monorepos, path filters and affected detection skip irrelevant jobs. Every skipped job saves minutes and reduces flaky test noise.
5. **Fail fast, debug locally** — Use `fail-fast: true` in matrices, `continue-on-error` only when intentional. Test workflows locally with `act` before pushing.

## Quick-Start: Common Problems

### "My workflow runs on every push but should only run for certain files"

1. Add `paths` filter to `on.push` and `on.pull_request`
2. For monorepo per-package CI, use `dorny/paths-filter` for multi-path detection
3. Combine with `if:` conditions on jobs for granular control
-> See `references/triggers-and-events.md`

### "CI is slow and expensive"

1. Enable dependency caching — `actions/cache` or `setup-node` with `cache: 'npm'`
2. Use matrix `fail-fast: true` to abort on first failure
3. Add `concurrency` groups to cancel superseded runs on same branch
4. Split test suites with matrix sharding
-> See `references/caching-and-performance.md`

### "I need to share workflow logic across repos"

1. Reusable workflow for full job orchestration (called with `uses:`)
2. Composite action for reusable step sequences (called as a step)
3. JavaScript/Docker action for complex logic with inputs/outputs
-> See `references/reusable-workflows-and-actions.md`

### "How do I deploy securely to AWS/GCP/Azure?"

1. Configure OIDC trust between GitHub and cloud provider — no long-lived secrets
2. Set `permissions: { id-token: write }` on the deployment job
3. Use environment protection rules (required reviewers, wait timers) for production
-> See `references/secrets-environments-oidc.md`

### "I'm worried about supply chain attacks on Actions"

1. Pin all third-party actions to full SHA
2. Set `permissions: {}` at workflow level, grant minimum per job
3. Audit action sources — prefer `actions/*` (GitHub-maintained) and verified creators
4. Enable Dependabot for Actions version updates
-> See `references/security-hardening.md`

## Decision Trees

### Trigger Selection

| Scenario | Trigger |
|----------|---------|
| Run on code push to main | `on: push: branches: [main]` |
| Run on PR (safe for forks) | `on: pull_request` |
| Run on PR with write access | `on: pull_request_target` (caution: runs in base context) |
| Manual trigger with inputs | `on: workflow_dispatch` |
| Scheduled job (cron) | `on: schedule` |
| Cross-repo trigger | `on: repository_dispatch` |
| After another workflow completes | `on: workflow_run` |

### Action Type Selection

| Need | Type |
|------|------|
| Reuse a full CI job across repos | Reusable workflow |
| Reuse a sequence of steps | Composite action |
| Complex logic with npm ecosystem | JavaScript action |
| Isolated environment or non-JS toolchain | Docker action |

### Matrix vs Sequential

| Signal | Approach |
|--------|----------|
| Test across multiple OS/versions | Matrix strategy |
| Build artifacts that depend on each other | Sequential jobs with `needs:` |
| Dynamic set of targets (monorepo packages) | Dynamic matrix with `fromJSON()` |
| One failure should stop all | `fail-fast: true` (default) |

## Reference Index

| File | Contents |
|------|----------|
| `references/workflow-syntax.md` | Workflow YAML anatomy, jobs, steps, expressions, contexts, functions, conditionals, outputs, environment variables |
| `references/triggers-and-events.md` | All trigger types (push, PR, schedule, dispatch, workflow_run), activity filters, path/branch filters, fork security |
| `references/matrix-and-concurrency.md` | Static/dynamic matrices, include/exclude, fail-fast, concurrency groups, cancel-in-progress |
| `references/caching-and-performance.md` | actions/cache patterns, setup-* built-in caching, cache keys/restore-keys, artifact management, job sharding |
| `references/reusable-workflows-and-actions.md` | Reusable workflows (inputs/outputs/secrets), composite actions, JavaScript actions, Docker actions, versioning |
| `references/secrets-environments-oidc.md` | Secrets hierarchy, GITHUB_TOKEN, environment protection rules, OIDC federation (AWS/GCP/Azure), deployment workflows |
| `references/security-hardening.md` | SHA pinning, permissions lockdown, supply chain attacks (tj-actions incident), Dependabot, artifact attestations, fork safety |
| `references/monorepo-patterns.md` | Path filtering, dorny/paths-filter, dynamic matrices from changed packages, Nx/Turbo integration, conditional job graphs |
| `references/cicd-recipes.md` | Test/lint, semantic release, Docker multi-platform build/push, deploy to cloud, self-hosted runners, local testing with act |
