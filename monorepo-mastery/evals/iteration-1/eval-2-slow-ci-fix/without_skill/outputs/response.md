You can usually cut a 45-minute monorepo CI to ~8-15 minutes with a few structural changes. Biggest wins first:

## 1) Run CI only for affected packages (not whole repo) 

Right now a README-only PR should not trigger full build/test/lint across 30 packages.

### What to do
- Use Turborepo's affected graph with `--filter=...[origin/main]` (or merge-base SHA).
- Skip workflow entirely for docs-only changes with GitHub `paths` filters.

### GitHub Actions trigger (skip docs-only)
```yaml
name: ci

on:
  pull_request:
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - '.changeset/**'
  push:
    branches: [main]
```

### Turborepo affected commands
```bash
# For PR jobs (compare against main)
pnpm turbo run lint test build --filter=...[origin/main]

# Optional: if main isn't fetched in shallow clones, ensure enough history
git fetch origin main --depth=100
```

### Why this is #1
This directly eliminates unnecessary work for the majority of PRs.

---

## 2) Turn on remote cache for Turborepo (shared across CI + dev machines)

Without remote cache, every CI run recomputes identical tasks.

### What to do
- Configure Turborepo remote cache (Vercel Remote Cache or self-hosted compatible).
- Ensure deterministic task inputs/outputs in `turbo.json`.

### Example `turbo.json`
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"],
      "cache": true
    },
    "lint": {
      "outputs": [],
      "cache": true
    },
    "typecheck": {
      "outputs": [],
      "cache": true
    }
  }
}
```

### CI env vars (example)
```yaml
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: your-team-slug
```

### Why this is #2
Even when affected scope is non-trivial, cache hits can turn many minutes into seconds.

---

## 3) Split CI into fast required checks vs heavy optional/post-merge checks

Most teams block PRs on too many expensive jobs.

### Recommended PR required checks
- `lint` (affected only)
- `typecheck` (affected only)
- `unit test` (affected only)
- maybe one smoke build

### Move to post-merge/nightly
- full e2e matrix
- full integration suite
- full workspace build
- security scans that are not merge-blocking

This preserves quality while dramatically improving PR cycle time.

---

## 4) Use pnpm + setup-node caching correctly (store + lockfile key)

A lot of CI time is dependency install churn.

### Baseline setup
```yaml
jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: |
            pnpm-lock.yaml

      - uses: pnpm/action-setup@v4
        with:
          version: 9
          run_install: false

      - name: Install
        run: pnpm install --frozen-lockfile
```

### Additional improvement: cache pnpm store path explicitly
```yaml
      - name: Get pnpm store directory
        id: pnpm-cache
        shell: bash
        run: echo "STORE_PATH=$(pnpm store path --silent)" >> $GITHUB_OUTPUT

      - uses: actions/cache@v4
        with:
          path: ${{ steps.pnpm-cache.outputs.STORE_PATH }}
          key: ${{ runner.os }}-pnpm-store-${{ hashFiles('pnpm-lock.yaml') }}
          restore-keys: |
            ${{ runner.os }}-pnpm-store-
```

---

## 5) Add concurrency cancellation to stop wasting minutes on superseded commits

When a PR gets multiple pushes, you should cancel in-flight older runs.

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This alone can save huge runner time and shorten perceived wait.

---

## 6) Parallelize by concern, not by duplicate setup

Run independent jobs in parallel, but avoid each job reinstalling from scratch if not needed.

### Pattern
- `changes` job computes affected scope once.
- Downstream `lint`, `typecheck`, `test` jobs run in parallel using same filter.
- Keep each job lean.

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      filter: ${{ steps.set-filter.outputs.filter }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - id: set-filter
        run: echo "filter=...[origin/main]" >> "$GITHUB_OUTPUT"

  lint:
    needs: changes
    runs-on: ubuntu-latest
    steps:
      # checkout/setup/install...
      - run: pnpm turbo run lint --filter="${{ needs.changes.outputs.filter }}"

  typecheck:
    needs: changes
    runs-on: ubuntu-latest
    steps:
      - run: pnpm turbo run typecheck --filter="${{ needs.changes.outputs.filter }}"

  test:
    needs: changes
    runs-on: ubuntu-latest
    steps:
      - run: pnpm turbo run test --filter="${{ needs.changes.outputs.filter }}"
```

---

## 7) Make task caching actually deterministic (common hidden killer)

If cache hit rate is low, check these:
- task outputs are declared correctly in `turbo.json`
- tasks do not write nondeterministic files into outputs (timestamps, random ids)
- env vars that should affect outputs are listed in `env`/`globalEnv`
- lockfile changes are the main dependency key, not volatile files

Also avoid accidentally invalidating cache with broad globs.

---

## 8) Reduce test/build scope further with package-level heuristics

For 30 packages, treat them differently:
- leaf libs: test/build only when changed
- core/shared libs: run dependents via `dependsOn` graph
- apps: smoke build on PR, full build nightly

For big integration tests, shard in parallel:
```bash
# Example with vitest -- adapt to your runner
pnpm vitest run --shard=1/3
pnpm vitest run --shard=2/3
pnpm vitest run --shard=3/3
```

---

## 9) Add a tiny “no-op/docs-only” fast lane

Even with `paths-ignore`, some non-code files may still trigger CI.
Add an early guard step to exit quickly when no relevant package changed.

```bash
# Example guard in a script
CHANGED=$(git diff --name-only origin/main...HEAD)
if ! echo "$CHANGED" | grep -Eq '^(packages/|apps/|pnpm-lock.yaml|turbo.json)'; then
  echo "No runtime-impacting changes; exiting early."
  exit 0
fi
```

---

## 10) Instrument and enforce CI budgets

You cannot optimize what you don't measure.

Track per-job timings for 2 weeks:
- install time
- turbo cache hit rate
- longest test suite
- p95 PR CI duration

Set targets:
- p50 PR CI < 10 min
- p95 PR CI < 15 min
- docs-only PR CI < 2 min (or skipped)

---

## A practical rollout plan (1 week)

1. Day 1: add `paths-ignore`, `concurrency.cancel-in-progress`, affected filters.
2. Day 2: enable/verify Turborepo remote cache + proper `outputs`.
3. Day 3: split required PR checks vs nightly/full checks.
4. Day 4: parallelize lint/typecheck/test jobs on affected set.
5. Day 5: measure cache hit rates and fix deterministic cache misses.

---

## Reference workflow (putting it together)

```yaml
name: pr-ci

on:
  pull_request:
    paths-ignore:
      - '**/*.md'
      - 'docs/**'

concurrency:
  group: pr-ci-${{ github.ref }}
  cancel-in-progress: true

env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: your-team-slug

jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: pnpm/action-setup@v4
        with:
          version: 9
          run_install: false

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: pnpm-lock.yaml

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Ensure main is available
        run: git fetch origin main --depth=100

      - name: Lint (affected)
        run: pnpm turbo run lint --filter=...[origin/main]

      - name: Typecheck (affected)
        run: pnpm turbo run typecheck --filter=...[origin/main]

      - name: Test (affected)
        run: pnpm turbo run test --filter=...[origin/main]

      - name: Build (affected)
        run: pnpm turbo run build --filter=...[origin/main]
```

If you apply only the top 3 items (affected-only + remote cache + PR check split), you'll usually see the largest drop quickly.
