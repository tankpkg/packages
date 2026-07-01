# Matrix Strategies and Concurrency

Sources: GitHub Actions workflow syntax reference (2026), GitHub concurrency documentation, production CI/CD patterns

Covers: static and dynamic matrix strategies, include/exclude modifiers, fail-fast behavior, concurrency groups, cancel-in-progress, and parallel execution patterns.

## Static Matrix

A matrix generates multiple job runs by combining variable values. Each combination runs as an independent job in parallel (subject to runner limits).

```yaml
jobs:
  test:
    strategy:
      matrix:
        node: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
```

This produces 6 jobs: `[18, ubuntu]`, `[18, windows]`, `[20, ubuntu]`, `[20, windows]`, `[22, ubuntu]`, `[22, windows]`.

### Matrix Properties

| Property | Default | Purpose |
|----------|---------|---------|
| `fail-fast` | `true` | Cancel remaining matrix jobs when one fails |
| `max-parallel` | Unlimited (runner limit) | Limit concurrent matrix jobs |

```yaml
strategy:
  fail-fast: true        # Stop all on first failure
  max-parallel: 3        # Run at most 3 simultaneously
  matrix:
    node: [18, 20, 22]
```

## Include and Exclude

### include — Add Extra Combinations

Add matrix entries that do not exist in the base combination, or add extra properties to specific combinations:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    node: [18, 20]
    include:
      # Add a combination not in the base matrix
      - os: macos-latest
        node: 22
        experimental: true
      # Add a property to an existing combination
      - os: ubuntu-latest
        node: 20
        coverage: true
```

### exclude — Remove Combinations

Remove specific combinations from the generated matrix:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node: [18, 20, 22]
    exclude:
      - os: windows-latest
        node: 18
      - os: macos-latest
        node: 18
```

### include-Only Matrix

Omit the base matrix entirely and use only `include` for fully custom combinations:

```yaml
strategy:
  matrix:
    include:
      - name: "Node 20 + Postgres 15"
        node: 20
        postgres: 15
      - name: "Node 22 + Postgres 16"
        node: 22
        postgres: 16
```

Each `include` entry becomes one job. Use `matrix.name` in step output for clarity.

## Dynamic Matrix

Generate matrix values at runtime from a prior job. Essential for monorepo workflows where the set of packages to test is determined by which files changed.

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: set
        run: |
          # Generate matrix JSON dynamically
          PACKAGES=$(ls packages/ | jq -R -s -c 'split("\n") | map(select(. != ""))')
          echo "matrix={\"package\":$PACKAGES}" >> "$GITHUB_OUTPUT"

  test:
    needs: detect
    strategy:
      matrix: ${{ fromJSON(needs.detect.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace packages/${{ matrix.package }}
```

### Dynamic Matrix from Changed Files

For monorepos, combine `dorny/paths-filter` or git diff with dynamic matrix:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.filter.outputs.changes }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            api:
              - 'packages/api/**'
            web:
              - 'packages/web/**'
            shared:
              - 'packages/shared/**'

  test:
    needs: changes
    if: needs.changes.outputs.packages != '[]'
    strategy:
      matrix:
        package: ${{ fromJSON(needs.changes.outputs.packages) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace packages/${{ matrix.package }}
```

See `references/monorepo-patterns.md` for advanced affected detection.

### Empty Matrix Handling

A matrix with zero entries causes the job to fail. Guard with an `if:` condition:

```yaml
test:
  needs: detect
  if: needs.detect.outputs.matrix != '{"package":[]}'
  strategy:
    matrix: ${{ fromJSON(needs.detect.outputs.matrix) }}
```

Or use `fromJSON` with a conditional that checks array length.

## Fail-Fast Behavior

| Setting | Behavior |
|---------|----------|
| `fail-fast: true` (default) | When any matrix job fails, cancel all remaining in-progress matrix jobs |
| `fail-fast: false` | All matrix jobs run to completion regardless of failures |

Set `fail-fast: false` when each matrix combination produces independent results (e.g., compatibility testing across OS versions where knowing all failures is valuable).

Set `fail-fast: true` for fast feedback during development — one failure is enough to know the build is broken.

### continue-on-error Per Job

Mark specific matrix entries as experimental without affecting the overall job status:

```yaml
strategy:
  fail-fast: false
  matrix:
    node: [18, 20, 22]
    include:
      - node: 22
        experimental: true

steps:
  - run: npm test
    continue-on-error: ${{ matrix.experimental == true }}
```

## Concurrency

Concurrency groups prevent multiple runs of the same workflow from executing simultaneously. Critical for deployment workflows and expensive CI runs.

### Basic Concurrency

```yaml
# Job level
jobs:
  deploy:
    concurrency: deploy-production
    runs-on: ubuntu-latest
```

Only one job with group `deploy-production` runs at a time. Queued runs wait.

### Cancel-in-Progress

Cancel queued or in-progress runs when a new run is triggered for the same group:

```yaml
# Workflow level — cancel superseded PR runs
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

### Concurrency Group Patterns

| Pattern | Group Key | Use Case |
|---------|-----------|----------|
| Per branch | `ci-${{ github.ref }}` | Cancel old PR runs when new commits pushed |
| Per PR | `pr-${{ github.event.pull_request.number }}` | Cancel old runs for same PR |
| Per environment | `deploy-${{ inputs.environment }}` | Serialize deployments per env |
| Global singleton | `deploy-production` | Only one production deploy at a time |
| Per workflow + branch | `${{ github.workflow }}-${{ github.ref }}` | Isolate different workflows |

### When to Cancel vs Queue

| Scenario | cancel-in-progress |
|----------|-------------------|
| PR CI — newest commit matters | `true` — old runs are wasted work |
| Production deploy | `false` — queue deploys, do not skip |
| Scheduled jobs | `false` — each run is independent |
| Manual dispatch | `false` — user expects their run to complete |

## Parallel Execution Limits

| Runner Type | Max Parallel Jobs |
|-------------|-------------------|
| GitHub-hosted (Free) | 20 |
| GitHub-hosted (Team) | 40 |
| GitHub-hosted (Enterprise) | 500 |
| Self-hosted | Unlimited (limited by runner count) |

macOS runners count as 10x against the parallel limit. Use `max-parallel` to stay within budget.

## Matrix Sharding Pattern

Split a large test suite across matrix entries for parallel execution:

```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]

steps:
  - run: npx jest --shard=${{ matrix.shard }}/4
```

Or with Playwright:

```yaml
strategy:
  matrix:
    shard: [1/4, 2/4, 3/4, 4/4]

steps:
  - run: npx playwright test --shard=${{ matrix.shard }}
```

### Merge Sharded Results

Use artifacts to collect results from each shard, then merge in a downstream job:

```yaml
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - run: npx jest --shard=${{ matrix.shard }}/4 --ci --json --outputFile=results-${{ matrix.shard }}.json
      - uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.shard }}
          path: results-${{ matrix.shard }}.json

  report:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: test-results-*
          merge-multiple: true
      - run: node merge-results.js
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No `fail-fast` on expensive matrix | All 20 jobs run when first fails | Use `fail-fast: true` (default) |
| Dynamic matrix with empty array | Job fails with "matrix must define at least one entry" | Guard with `if:` condition |
| No `cancel-in-progress` on PR CI | Old runs waste minutes | Add `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }` |
| `cancel-in-progress: true` on deploy | Deployment interrupted mid-way | Use `false` for deploy workflows |
| Forgetting `fromJSON()` on dynamic matrix | Matrix treated as literal string | Wrap with `fromJSON()` |
| Matrix values not quoted | YAML parses `3.10` as `3.1` (float) | Quote: `'3.10'` |
