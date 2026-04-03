# Caching and Performance

Sources: GitHub Actions caching documentation (2026), actions/cache repository, actions/setup-node docs, GitHub artifacts documentation

Covers: dependency caching strategies, cache keys and restore keys, setup-* built-in caching, artifact management, job sharding, and CI performance optimization patterns.

## actions/cache

The `actions/cache` action stores and restores files between workflow runs. Cache hits skip expensive install/build steps.

### Basic Usage

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      npm-${{ runner.os }}-
```

| Parameter | Purpose |
|-----------|---------|
| `path` | Directories or files to cache |
| `key` | Exact match key — cache hit if found |
| `restore-keys` | Fallback prefix match keys (oldest to newest) |
| `save-always` | Save cache even if job fails (default: false) |
| `enableCrossOsArchive` | Share cache across OS (default: false) |

### Cache Hit Logic

1. Search for exact `key` match
2. If miss, search `restore-keys` in order (prefix match, most recent)
3. If restored from a restore-key, the cache is saved with the original `key` at job end (creating an updated cache entry)

### Cache Limits

| Limit | Value |
|-------|-------|
| Individual cache entry | 10 GB |
| Total cache per repository | 10 GB |
| Cache retention | 7 days since last access |
| Eviction | LRU when at capacity |

Caches not accessed for 7 days are automatically evicted. When the 10 GB repo limit is reached, oldest caches are evicted first.

## Cache Key Patterns

### Package Manager Caching

| Package Manager | Key Pattern | Path |
|-----------------|------------|------|
| npm | `npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}` | `~/.npm` |
| yarn (v1) | `yarn-${{ runner.os }}-${{ hashFiles('**/yarn.lock') }}` | `~/.cache/yarn` |
| pnpm | `pnpm-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}` | `~/.local/share/pnpm/store` |
| pip | `pip-${{ runner.os }}-${{ hashFiles('**/requirements*.txt') }}` | `~/.cache/pip` |
| go | `go-${{ runner.os }}-${{ hashFiles('**/go.sum') }}` | `~/go/pkg/mod` |
| cargo | `cargo-${{ runner.os }}-${{ hashFiles('**/Cargo.lock') }}` | `~/.cargo/registry` + `~/.cargo/git` + `target/` |
| gradle | `gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}` | `~/.gradle/caches` |
| maven | `maven-${{ runner.os }}-${{ hashFiles('**/pom.xml') }}` | `~/.m2/repository` |

### Effective Restore Keys

Design restore keys as progressively broader fallbacks:

```yaml
key: npm-linux-abc123      # Exact lockfile hash
restore-keys: |
  npm-linux-                # Same OS, any lockfile (most npm packages still cached)
  npm-                      # Any OS (cross-platform fallback)
```

A stale cache (partial hit from restore-key) is nearly always faster than no cache. The action saves an updated cache with the exact `key` at job end.

### Multiple Cache Paths

Cache multiple directories in a single cache entry:

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      node_modules
      .next/cache
    key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
```

## Setup-* Built-in Caching

Many `actions/setup-*` actions include built-in caching that eliminates the need for separate `actions/cache` steps:

```yaml
# Node.js — caches npm/yarn/pnpm automatically
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'                 # 'npm', 'yarn', or 'pnpm'

# Python — caches pip/pipenv/poetry
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

# Go — caches go modules
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true

# Java — caches maven/gradle/sbt
- uses: actions/setup-java@v4
  with:
    distribution: 'temurin'
    java-version: '21'
    cache: 'gradle'
```

Built-in caching uses `hashFiles()` on the appropriate lockfile automatically. Prefer this over manual `actions/cache` when available — simpler and fewer lines.

## Build Artifact Caching

Cache build outputs to avoid rebuilding across jobs:

```yaml
# Next.js build cache
- uses: actions/cache@v4
  with:
    path: .next/cache
    key: nextjs-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.ts', '**/*.tsx') }}
    restore-keys: |
      nextjs-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}-
      nextjs-${{ runner.os }}-

# Turborepo cache
- uses: actions/cache@v4
  with:
    path: node_modules/.cache/turbo
    key: turbo-${{ runner.os }}-${{ hashFiles('**/turbo.json') }}-${{ github.sha }}
    restore-keys: |
      turbo-${{ runner.os }}-${{ hashFiles('**/turbo.json') }}-
      turbo-${{ runner.os }}-
```

## Artifacts

Artifacts share files between jobs within a workflow run. Unlike caches, artifacts persist after the run and are downloadable from the UI.

### Upload Artifact

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: |
      dist/
      !dist/**/*.map
    retention-days: 5
    if-no-files-found: error     # 'warn' or 'ignore' as alternatives
```

### Download Artifact

```yaml
- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: ./dist

# Download all artifacts
- uses: actions/download-artifact@v4
  with:
    merge-multiple: true
```

### Cache vs Artifact

| Dimension | Cache | Artifact |
|-----------|-------|----------|
| Purpose | Speed up repeated operations | Share data between jobs/runs |
| Scope | Repository-wide, cross-run | Single workflow run |
| Retention | 7 days since last access (LRU) | 90 days default (configurable) |
| Size limit | 10 GB per repo | Per-artifact limits, 500 MB default |
| Access | Same key matches across runs | Downloaded by job in same run |
| Downloadable from UI | No | Yes |
| Use when | Dependency install, build cache | Test results, built assets, coverage |

## Performance Optimization Patterns

### 1. Skip Unnecessary Work

```yaml
on:
  push:
    paths-ignore: ['docs/**', '*.md', 'LICENSE']
```

Use `paths` filters to skip workflows when only docs or config files change.

### 2. Cancel Superseded Runs

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

See `references/matrix-and-concurrency.md` for concurrency patterns.

### 3. Parallelize with Matrix Sharding

Split test suites across matrix entries:

```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: npx jest --shard=${{ matrix.shard }}/4
```

### 4. Use Smaller Runner Images

| Runner | Boot Time | Cost | Use When |
|--------|-----------|------|----------|
| `ubuntu-latest` | ~15s | 1x | Default — most CI jobs |
| `ubuntu-24.04` | ~15s | 1x | Pinned OS version |
| `windows-latest` | ~40s | 2x | Windows-specific builds |
| `macos-latest` | ~30s | 10x | macOS/iOS builds only |

Avoid macOS runners for non-Apple tasks — they cost 10x against the parallel job limit.

### 5. Conditional Job Execution

Skip expensive jobs when not needed:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'server/**'

  test-backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: npm test
```

### 6. Minimize Checkout Depth

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 1              # Shallow clone (default)
```

Use `fetch-depth: 0` only when full history is needed (changelog generation, affected detection). Shallow clones are significantly faster for large repos.

### 7. Docker Layer Caching

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

GitHub Actions cache backend for Docker BuildKit. `mode=max` caches all layers, not just the final image layers.

## Cache Management

### List and Delete Caches

```bash
# List all caches
gh cache list

# Delete a specific cache by key
gh cache delete npm-linux-abc123

# Delete all caches matching a prefix
gh cache list --key npm- --json key -q '.[].key' | xargs -I {} gh cache delete {}
```

### Cache Debugging

When cache misses are unexpected:

1. Check `key` value — any component change (OS, lockfile hash) creates a new key
2. Check cache limit — 10 GB repo limit may evict entries
3. Check retention — caches unused for 7 days are evicted
4. Check branch scope — PR caches are scoped to the PR branch + base branch
5. Enable debug logging: set `ACTIONS_STEP_DEBUG` secret to `true`

### Branch Scope

Caches follow branch scope rules:

| Created On | Accessible From |
|-----------|-----------------|
| Default branch (main) | All branches |
| Feature branch | Same branch + default branch |
| PR branch | Same PR + base branch + default branch |

This prevents feature branches from polluting each other's caches while allowing inheritance from the default branch.
