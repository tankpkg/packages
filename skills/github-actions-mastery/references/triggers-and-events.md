# Triggers and Events

Sources: GitHub Actions events documentation (2026), GitHub security hardening guide, GitHub webhook events reference

Covers: all workflow trigger types, activity filters, branch and path filtering, manual dispatch inputs, cross-workflow and cross-repo triggers, fork security, and trigger selection guidance.

## Trigger Syntax

Triggers are defined under the `on:` key. Use a single trigger, a list, or a map with filters:

```yaml
# Single trigger
on: push

# Multiple triggers (no filters)
on: [push, pull_request]

# Triggers with filters (map form)
on:
  push:
    branches: [main, release/*]
    paths: ['src/**', 'package.json']
  pull_request:
    branches: [main]
```

## Core Trigger Types

### push

Runs when commits are pushed to matching branches or tags.

```yaml
on:
  push:
    branches:
      - main
      - 'release/**'
    tags:
      - 'v*'
    paths:
      - 'src/**'
      - '!src/**/*.test.ts'    # Exclude test files
    paths-ignore:
      - 'docs/**'
      - '*.md'
```

| Filter | Purpose |
|--------|---------|
| `branches` / `branches-ignore` | Limit to specific branches (glob patterns) |
| `tags` / `tags-ignore` | Limit to specific tags |
| `paths` / `paths-ignore` | Limit to file path changes |

`paths` and `paths-ignore` are mutually exclusive. Same for `branches` and `branches-ignore`. Prefix a pattern with `!` inside `paths` to negate individual entries.

### pull_request

Runs when a pull request targets matching branches. Safe for forks — runs in the context of the PR merge commit with read-only `GITHUB_TOKEN`.

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]    # Default types
    paths:
      - 'src/**'
```

| Activity Type | When |
|--------------|------|
| `opened` | PR created |
| `synchronize` | New commits pushed to PR branch |
| `reopened` | PR reopened after closing |
| `closed` | PR closed (check `github.event.pull_request.merged`) |
| `labeled` | Label added |
| `review_requested` | Review requested |
| `ready_for_review` | PR moved from draft to ready |

Default types if none specified: `opened`, `synchronize`, `reopened`.

### pull_request_target

Runs in the context of the **base** branch (not the PR branch). Has write access to the base repo and access to base repo secrets. Dangerous for fork PRs.

```yaml
on:
  pull_request_target:
    types: [labeled]
```

**Security rule**: Never check out PR code (`actions/checkout` with `ref: ${{ github.event.pull_request.head.sha }}`) and run it in a `pull_request_target` workflow. This gives untrusted PR code access to secrets and write permissions. If labeling is needed, use a two-workflow pattern: `pull_request` for testing, `pull_request_target` only for labeling/commenting without running PR code.

### schedule

Runs on a cron schedule. Always runs on the default branch.

```yaml
on:
  schedule:
    - cron: '30 5 * * 1-5'    # 5:30 UTC, Mon-Fri
```

| Field | Values |
|-------|--------|
| Minute | 0-59 |
| Hour | 0-23 |
| Day of month | 1-31 |
| Month | 1-12 |
| Day of week | 0-6 (Sun=0) or 1-7 (Mon=1) |

Common patterns:

| Schedule | Cron |
|----------|------|
| Daily at midnight UTC | `0 0 * * *` |
| Every 6 hours | `0 */6 * * *` |
| Weekdays at 9am UTC | `0 9 * * 1-5` |
| Weekly Sunday midnight | `0 0 * * 0` |
| First of month at noon | `0 12 1 * *` |

**Caveats**: Scheduled workflows can be delayed during periods of high load. GitHub may disable scheduled workflows on repos with no activity for 60 days. Minimum interval is every 5 minutes, but GitHub recommends no more frequently than every 15 minutes.

### workflow_dispatch

Manual trigger from the GitHub UI, CLI, or API. Supports typed inputs.

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment target'
        required: true
        type: choice
        options: [staging, production]
        default: staging
      version:
        description: 'Version to deploy'
        required: true
        type: string
      dry_run:
        description: 'Dry run only'
        required: false
        type: boolean
        default: false
```

| Input Type | UI Control |
|-----------|------------|
| `string` | Text input |
| `boolean` | Checkbox |
| `choice` | Dropdown |
| `environment` | Environment selector |

Access inputs: `${{ inputs.environment }}`, `${{ inputs.dry_run }}`.

Trigger from CLI: `gh workflow run deploy.yml -f environment=staging -f version=1.2.3`.

### repository_dispatch

External event trigger via API. Useful for cross-repo workflows or external system integration.

```yaml
on:
  repository_dispatch:
    types: [deploy-request, run-tests]
```

Trigger via API:

```bash
gh api repos/{owner}/{repo}/dispatches \
  -f event_type=deploy-request \
  -f client_payload='{"version":"1.2.3","env":"production"}'
```

Access payload: `${{ github.event.client_payload.version }}`.

### workflow_run

Runs after another workflow completes. Useful for workflows that need artifacts or results from a prior workflow.

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]
```

| Type | When |
|------|------|
| `completed` | After workflow finishes (regardless of result) |
| `requested` | When workflow is requested (queued) |

Check the triggering workflow's conclusion:

```yaml
jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
```

### workflow_call

Makes a workflow reusable — called by other workflows. See `references/reusable-workflows-and-actions.md`.

```yaml
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
    secrets:
      NPM_TOKEN:
        required: true
```

## Branch and Path Filtering

### Glob Patterns

| Pattern | Matches |
|---------|---------|
| `main` | Exact branch name |
| `release/*` | `release/1.0` but not `release/1.0/hotfix` |
| `release/**` | `release/1.0` and `release/1.0/hotfix` |
| `!release/beta*` | Negation — exclude beta releases |
| `feature-[abc]` | Character set — `feature-a`, `feature-b`, `feature-c` |

### Combining Branch and Path Filters

When both `branches` and `paths` are specified, the workflow runs only when BOTH conditions match. A push to `main` that only changes `docs/` is skipped if `paths` requires `src/**`.

### Path Filtering Limitations

Path filters compare the current push to the previous commit on that branch. Force pushes or initial branch pushes may trigger unexpectedly. For complex monorepo path logic, use `dorny/paths-filter` in a job instead. See `references/monorepo-patterns.md`.

## Fork Security

| Trigger | Fork PR Context | Secrets Access | Write Access |
|---------|----------------|----------------|--------------|
| `pull_request` | Merge commit | No (read-only token) | No |
| `pull_request_target` | Base branch | Yes (base repo secrets) | Yes |

**Safe pattern for fork PRs**: Use `pull_request` for CI (build, test, lint). Use `pull_request_target` only for non-code tasks (labeling, commenting) and never checkout fork code in that context.

## Event Payload Access

Every trigger populates `github.event` with the full webhook payload:

```yaml
# Push event
github.event.head_commit.message     # Commit message
github.event.commits                  # Array of commits
github.event.compare                  # Diff URL

# Pull request event
github.event.pull_request.number      # PR number
github.event.pull_request.head.sha    # Head commit SHA
github.event.pull_request.labels      # Array of labels
github.event.pull_request.draft       # Is PR a draft?

# workflow_dispatch
github.event.inputs.environment       # Input value (also available as inputs.environment)
```

## Trigger Selection Guide

| Goal | Trigger | Notes |
|------|---------|-------|
| CI on every push | `push` + `pull_request` | Cover both direct pushes and PRs |
| Deploy on merge to main | `push: branches: [main]` | Runs after merge commit |
| Release on tag | `push: tags: ['v*']` | Semantic version tags |
| Manual deploy | `workflow_dispatch` | With environment input |
| Nightly tests | `schedule: cron` | Run comprehensive suite |
| After CI passes | `workflow_run` | Chain deploy after CI |
| External trigger | `repository_dispatch` | API/webhook integration |
| PR label automation | `pull_request: types: [labeled]` | Auto-assign, auto-merge |
| Issue triage | `issues: types: [opened]` | Auto-label, auto-assign |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No `paths` filter on monorepo | Every push triggers all workflows | Add `paths:` per package |
| Using `pull_request_target` + checkout | Fork PRs get secrets access | Use `pull_request` for CI |
| Cron without activity | GitHub disables after 60 days | Add manual trigger as fallback |
| Missing `types:` on PR trigger | Only default types fire | Specify `ready_for_review` if needed |
| `paths-ignore` + `paths` together | YAML error — mutually exclusive | Pick one approach |
