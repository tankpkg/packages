# Monorepo Patterns

Sources: GitHub Actions documentation (2026), dorny/paths-filter, WarpBuild monorepo guide, Nx and Turborepo CI documentation, production monorepo CI patterns

Covers: path filtering strategies, dorny/paths-filter for multi-package detection, dynamic matrix generation from changed packages, Nx/Turbo integration, conditional job graphs, and monorepo CI architecture.

## The Monorepo Problem

In a monorepo, a single push may change one package out of fifty. Running all workflows wastes CI minutes, increases flaky test exposure, and delays feedback. The solution: detect what changed and run only the relevant jobs.

## Native Path Filtering

### Built-in `paths` Filter

```yaml
on:
  push:
    paths:
      - 'packages/api/**'
      - 'shared/**'
```

**Limitations**:

| Issue | Detail |
|-------|--------|
| One workflow per filter | Cannot run different jobs for different path changes in the same workflow |
| No OR logic across paths | Cannot say "run job A for path X, job B for path Y" in one workflow |
| Push comparison | Compares to previous commit on same branch — force pushes or new branches may over-trigger |
| No outputs | Cannot use the matched paths as data for downstream jobs |

Native `paths` works for simple cases (one package per workflow file). For multi-package monorepos, use `dorny/paths-filter`.

## dorny/paths-filter

The `dorny/paths-filter` action runs inside a job and outputs boolean flags for each path group. This enables conditional job execution within a single workflow.

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.filter.outputs.api }}
      web: ${{ steps.filter.outputs.web }}
      shared: ${{ steps.filter.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            api:
              - 'packages/api/**'
              - 'shared/**'
            web:
              - 'packages/web/**'
              - 'shared/**'
            infra:
              - 'infra/**'
              - 'terraform/**'

  test-api:
    needs: detect
    if: needs.detect.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace packages/api

  test-web:
    needs: detect
    if: needs.detect.outputs.web == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace packages/web
```

### Configuration Options

```yaml
- uses: dorny/paths-filter@v3
  with:
    filters: |
      api:
        - 'packages/api/**'
    # Which files to compare against
    base: main                    # Compare against this branch (default: merge base)
    # For push events, compare against the previous commit
    # For pull_request events, compare against the base branch
```

### Dependency-Aware Filters

When `shared/` changes, both `api` and `web` need testing. Include shared paths in each filter:

```yaml
filters: |
  api:
    - 'packages/api/**'
    - 'packages/shared/**'       # Shared dependency
    - 'package.json'             # Root dependency changes
  web:
    - 'packages/web/**'
    - 'packages/shared/**'
    - 'package.json'
```

## Dynamic Matrix from Changes

For monorepos with many packages, generate a matrix dynamically from changed paths:

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.find.outputs.packages }}
      has_changes: ${{ steps.find.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: find
        run: |
          # Get changed files between HEAD and merge base
          BASE=$(git merge-base origin/main HEAD)
          CHANGED=$(git diff --name-only "$BASE" HEAD)

          # Extract unique package directories
          PACKAGES=$(echo "$CHANGED" | grep '^packages/' | cut -d/ -f2 | sort -u | jq -R -s -c 'split("\n") | map(select(. != ""))')

          echo "packages=$PACKAGES" >> "$GITHUB_OUTPUT"
          if [ "$PACKAGES" = "[]" ]; then
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
          else
            echo "has_changes=true" >> "$GITHUB_OUTPUT"
          fi

  test:
    needs: detect
    if: needs.detect.outputs.has_changes == 'true'
    strategy:
      matrix:
        package: ${{ fromJSON(needs.detect.outputs.packages) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace packages/${{ matrix.package }}
```

### Handling Empty Matrix

A matrix with zero entries fails. Always guard with an `if:` condition on the job, or provide a fallback default matrix.

## Nx Integration

Nx provides built-in affected detection based on its dependency graph:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx nx affected -t test --base=origin/main --head=HEAD
      - run: npx nx affected -t build --base=origin/main --head=HEAD
      - run: npx nx affected -t lint --base=origin/main --head=HEAD
```

### Nx with Dynamic Matrix

Generate a matrix of affected projects for parallel execution:

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.affected.outputs.matrix }}
      has_affected: ${{ steps.affected.outputs.has_affected }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: npm ci
      - id: affected
        run: |
          PROJECTS=$(npx nx show projects --affected --base=origin/main --head=HEAD --json)
          echo "matrix={\"project\":$PROJECTS}" >> "$GITHUB_OUTPUT"
          if [ "$PROJECTS" = "[]" ]; then
            echo "has_affected=false" >> "$GITHUB_OUTPUT"
          else
            echo "has_affected=true" >> "$GITHUB_OUTPUT"
          fi

  test:
    needs: detect
    if: needs.detect.outputs.has_affected == 'true'
    strategy:
      matrix: ${{ fromJSON(needs.detect.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx nx test ${{ matrix.project }}
```

### Nx Remote Cache

```yaml
- run: npx nx affected -t test --base=origin/main
  env:
    NX_CLOUD_ACCESS_TOKEN: ${{ secrets.NX_CLOUD_TOKEN }}
```

Nx Cloud caches task results. If a task was run with identical inputs before (any branch, any CI run), the cached result is reused instantly.

## Turborepo Integration

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run test lint build --filter='...[origin/main...HEAD]'
```

The `--filter='...[origin/main...HEAD]'` flag runs tasks only for packages changed since `origin/main`, including their dependents.

### Turbo Remote Cache

```yaml
- run: pnpm turbo run build --filter='...[origin/main...HEAD]'
  env:
    TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
    TURBO_TEAM: ${{ vars.TURBO_TEAM }}
```

## Conditional Job Graphs

Build complex dependency graphs where jobs run only when their package changed:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.f.outputs.api }}
      web: ${{ steps.f.outputs.web }}
      shared: ${{ steps.f.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: f
        with:
          filters: |
            api:
              - 'packages/api/**'
            web:
              - 'packages/web/**'
            shared:
              - 'packages/shared/**'

  test-shared:
    needs: changes
    if: needs.changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: npm test --workspace packages/shared

  test-api:
    needs: [changes, test-shared]
    if: |
      always() &&
      (needs.changes.outputs.api == 'true' || needs.changes.outputs.shared == 'true') &&
      (needs.test-shared.result == 'success' || needs.test-shared.result == 'skipped')
    runs-on: ubuntu-latest
    steps:
      - run: npm test --workspace packages/api

  deploy-api:
    needs: [changes, test-api]
    if: |
      github.ref == 'refs/heads/main' &&
      needs.test-api.result == 'success'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: deploy-api.sh
```

### Handling Skipped Dependencies

When a `needs` job is skipped (its `if:` was false), dependent jobs also skip by default. Use `always()` and check `needs.*.result` explicitly to run a job even when its dependency was skipped:

```yaml
if: |
  always() &&
  (needs.test.result == 'success' || needs.test.result == 'skipped')
```

## Monorepo CI Architecture Patterns

| Pattern | Best For | Complexity |
|---------|----------|-----------|
| One workflow per package | Small monorepos (2-5 packages) | Low |
| Single workflow + dorny/paths-filter | Medium monorepos (5-20 packages) | Medium |
| Dynamic matrix from changed packages | Large monorepos (20+ packages) | Medium |
| Nx/Turbo affected + remote cache | Any size with build orchestrator | Low (tooling handles complexity) |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No path filtering | Every push runs all packages | Add `dorny/paths-filter` |
| Missing shared dependency in filters | Shared changes do not trigger dependent packages | Include shared paths in each filter |
| `fetch-depth: 1` with git diff | Cannot compare against base branch | Use `fetch-depth: 0` for affected detection |
| Dynamic matrix without empty guard | Job fails when no packages changed | Add `if: has_changes == 'true'` |
| Testing affected without dependents | Packages depending on changed code are not tested | Use Nx/Turbo affected (includes dependents) |
