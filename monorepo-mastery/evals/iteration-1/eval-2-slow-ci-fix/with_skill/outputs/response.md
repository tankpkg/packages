You can cut this from ~45 minutes to single-digit minutes on most PRs if you change CI in this order.

## 1) Run affected-only Turborepo tasks (biggest win)
Right now your pipeline sounds like the monorepo anti-pattern from the skill refs: running full build/test/lint for every PR.

Use Turborepo’s affected filters against the PR base:

```bash
# Build/test/lint only changed packages + dependents
turbo run build test lint --filter=...[origin/main]

# For push workflows, compare against previous commit
turbo run build test lint --filter=...[HEAD^1]
```

From the references: `...[ref]` means “changed since ref”, and includes downstream dependents.

A good GitHub Actions setup:

```yaml
name: ci

on:
  pull_request:
  merge_group:
    types: [checks_requested]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      docs_only: ${{ steps.filter.outputs.docs_only }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 50
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            docs_only:
              - '**/*.md'
              - 'docs/**'
              - '!package.json'
              - '!pnpm-lock.yaml'
              - '!turbo.json'

  ci:
    needs: changes
    if: needs.changes.outputs.docs_only != 'true'
    runs-on: ubuntu-latest
    env:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 50

      - uses: pnpm/action-setup@v4
        with:
          version: 10

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm

      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run lint test build --filter=...[origin/main]

  docs-fast-path:
    needs: changes
    if: needs.changes.outputs.docs_only == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Docs-only change: skipping heavy CI"
```

Why this is #1: this removes unnecessary work entirely instead of trying to run unnecessary work faster.

## 2) Turn on Turborepo remote cache (usually the next massive drop)
From the skill references, this is core: CI runners are ephemeral, so local cache is mostly wasted. Remote cache lets one run populate outputs and others restore.

Required env:

```yaml
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}
```

Then run turbo normally:

```bash
pnpm turbo run lint test build --filter=...[origin/main]
```

Also verify cache behavior during rollout:

```bash
pnpm turbo run build --filter=[origin/main] --dry-run
```

If cache hit rate is low after setup, inspect task inputs (see #3) and non-hermetic behavior.

## 3) Stop docs/readme edits from invalidating build caches
The scaling reference calls this out explicitly (exclude non-production inputs like docs from invalidation). In Turbo, do the equivalent with task inputs.

`turbo.json` example:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["$TURBO_DEFAULT$", "!**/*.md", "!docs/**"],
      "outputs": ["dist/**", "build/**"]
    },
    "test": {
      "dependsOn": ["^build"],
      "inputs": ["$TURBO_DEFAULT$", "!**/*.md", "!docs/**"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "inputs": ["$TURBO_DEFAULT$", "!**/*.md", "!docs/**"]
    }
  }
}
```

This is what prevents a 1-line README change from fan-out invalidation.

## 4) Optimize Git checkout strategy for affected detection
The scaling reference recommends avoiding `depth=1` (merge-base problems) and using shallow history by default.

Use:
- `fetch-depth: 50` for affected-detection jobs (safe default)
- `fetch-depth: 1` only in jobs that do not compute diffs
- Sparse checkout for narrow deploy jobs

Example sparse checkout in a package-specific deploy job:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 1
    sparse-checkout: |
      apps/web
      packages/shared
      package.json
      pnpm-lock.yaml
      turbo.json
```

## 5) Parallelize independent work and cap appropriately
From CI refs: long sequential pipelines are a major anti-pattern. Split lint/test/build into parallel jobs (or at least run Turbo with explicit concurrency).

Simple parallel workflow shape:

```yaml
jobs:
  lint:
    # same setup steps...
    steps:
      - run: pnpm turbo run lint --filter=...[origin/main]

  test:
    # same setup steps...
    steps:
      - run: pnpm turbo run test --filter=...[origin/main]

  build:
    # same setup steps...
    steps:
      - run: pnpm turbo run build --filter=...[origin/main]
```

Then gate merge on all three.

## 6) Add merge queue once CI is fast/stable
From the references: enable GitHub merge queue and include `merge_group` trigger so combined PR state is validated. This prevents “green PRs, broken main” while keeping throughput.

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]
```

---

## Practical rollout plan (1 week)
1. Day 1: add affected-only Turbo filter + docs-only fast path.
2. Day 2: wire `TURBO_TOKEN`/`TURBO_TEAM` and verify remote cache hits.
3. Day 3: update `turbo.json` inputs to exclude markdown/docs from build/test/lint cache keys.
4. Day 4: split lint/test/build parallel jobs.
5. Day 5: enable merge queue.

## Expected result
For a 30-package pnpm+turborepo repo:
- README-only PRs: from ~45m to ~1-3m (or immediate skip)
- Small code PRs: often ~5-12m with warm remote cache
- Larger cross-cutting PRs: still slower, but materially improved via cache + parallelization

If you want, I can also draft a production-ready `.github/workflows/ci.yml` tailored to your current repo layout (`apps/*`, `packages/*`, deploy jobs, required checks).