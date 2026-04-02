# Scaling and Performance

Sources: Software Engineering at Google (Winters et al, 2020), Git docs, Scalar docs, Sapling docs, 2024-2026 performance research

Covers: Git performance at scale, build caching strategies, affected detection algorithms, incremental build patterns, anti-patterns, scale thresholds, monitoring metrics.

## Git Performance at Scale

### Performance Thresholds

Repositories degrade predictably as they grow. Understand the thresholds to act before users feel pain.

| Dimension | Comfortable | Degraded | Critical |
|-----------|-------------|----------|----------|
| File count | <50K files | 50K-200K | >200K files |
| Repo size | <500MB | 500MB-2GB | >2GB |
| Commit history | <500K commits | 500K-1M | >1M commits |
| Contributors (concurrent) | <50 | 50-500 | >500 |

At the "Degraded" threshold, apply shallow clones and sparse checkout. At "Critical", evaluate Scalar or Sapling.

### Shallow Clones

Shallow clones fetch only recent history, dramatically reducing clone time and disk usage in CI environments.

```bash
# Fetch last 50 commits — sufficient for most CI diff operations
git clone --depth=50 https://github.com/org/repo.git

# Deepen when needed (e.g., for changelog generation)
git fetch --deepen=200

# Convert shallow to full when required
git fetch --unshallow
```

Use `--depth=50` as the default for CI. Deeper histories are rarely needed for build and test pipelines. Avoid `--depth=1` — it breaks `git diff` against base branches when the merge base falls outside the shallow window.

### Sparse Checkout

Sparse checkout lets developers and CI jobs work on a subset of the repository without materializing all files on disk.

```bash
# Enable sparse checkout with cone mode (faster pattern matching)
git clone --filter=blob:none --sparse https://github.com/org/repo.git
cd repo

# Add only the directories you need
git sparse-checkout set packages/api packages/shared tools/scripts

# Add more directories incrementally
git sparse-checkout add packages/web

# List current sparse patterns
git sparse-checkout list
```

Cone mode (`--cone`) restricts patterns to directory prefixes, enabling O(1) pattern matching instead of O(n) glob evaluation. Use non-cone mode only when you need file-level patterns — it is significantly slower at scale.

### Partial Clone

Partial clone defers downloading blob objects until they are accessed, reducing initial clone size for repositories with large binary assets or extensive history.

```bash
# Skip blob downloads entirely — fetch on demand
git clone --filter=blob:none https://github.com/org/repo.git

# Skip tree objects too (more aggressive, less compatible)
git clone --filter=tree:0 https://github.com/org/repo.git

# Combine with sparse checkout for maximum effect
git clone --filter=blob:none --sparse https://github.com/org/repo.git
```

`--filter=blob:none` is the safe default. It fetches all tree objects (directory structure) but defers blobs (file contents) until checkout. This preserves full `git log` and `git diff` functionality while reducing clone size by 60-90% for large repos.

### Scalar

Scalar ships with Git 2.38+ and auto-configures a suite of performance features with a single command.

```bash
# Clone and configure all optimizations automatically
scalar clone https://github.com/org/repo.git

# Register an existing repo with Scalar
scalar register

# Check Scalar status
scalar diagnose
```

Scalar automatically enables:

| Feature | What It Does |
|---------|-------------|
| FSMonitor | Daemon watches filesystem changes; `git status` skips full scan |
| Background maintenance | Prefetches, repacks, and prunes on a schedule |
| Sparse checkout | Cone mode enabled by default |
| Partial clone | `--filter=blob:none` applied at clone |
| Commit-graph | Precomputed graph for fast `git log` and reachability |
| Multi-pack index | Single index across multiple pack files |

Apply Scalar when a repository exceeds 100K files or 1GB. It requires no server-side changes — all optimizations run client-side.

### Sapling

Sapling is Meta's source control system, open-sourced in 2022. It is designed for monorepos at extreme scale (hundreds of millions of files, millions of commits).

Key capabilities:

| Feature | Description |
|---------|-------------|
| Smartlog (`sl`) | Shows only your relevant commits — not the full DAG |
| Stacked diffs | First-class support for chains of dependent commits |
| Directory branching | Branch on a subdirectory, not the whole repo |
| Virtual filesystem (EdenFS) | Files appear on demand; no full checkout required |
| Interactive rebase | `sl rebase -i` with conflict resolution built in |

```bash
# Clone with Sapling
sl clone https://github.com/org/repo.git

# View your relevant commits
sl

# Create a stack of commits
sl commit -m "feat: add API endpoint"
sl commit -m "feat: add tests for endpoint"

# Submit stack as separate PRs
sl pr submit --stack
```

Sapling is most valuable when teams work on stacked changes or when the repository is large enough that EdenFS's virtual filesystem provides meaningful checkout savings. For most monorepos under 500K files, Scalar is sufficient.

## Build Caching

### Local Caching

Local caches store build artifacts on the developer's machine or CI runner. They are fast (no network) but not shared across machines.

| Tool | Cache Location | Cache Key |
|------|---------------|-----------|
| Turborepo | `.turbo/cache/` | Hash of inputs + task |
| Nx | `.nx/cache/` | Hash of inputs + executor |
| Bazel | `~/.cache/bazel/` | Hash of action inputs |
| Gradle | `~/.gradle/caches/` | Hash of inputs + task |

Local caches provide value on developer machines (warm rebuilds) and on CI runners with persistent storage between runs. Without persistent storage, local caches provide no benefit in CI.

### Remote Caching

Remote caches share artifacts across all machines — developers and CI runners. A cache hit on CI means zero rebuild time regardless of which runner picks up the job.

| Tool | Remote Cache Provider | Protocol |
|------|-----------------------|----------|
| Turborepo | Vercel Remote Cache | HTTPS REST |
| Nx | Nx Cloud | HTTPS REST |
| Bazel | Buildbarn, BuildBuddy, EngFlow | gRPC RE API |
| Gradle | Gradle Enterprise | HTTPS REST |
| Any | Self-hosted S3/GCS | Custom |

```bash
# Turborepo: enable remote cache
npx turbo login
npx turbo link

# Nx: connect to Nx Cloud
npx nx connect-to-nx-cloud

# Bazel: configure remote cache in .bazelrc
echo 'build --remote_cache=grpcs://cache.buildbuddy.io' >> .bazelrc
echo 'build --remote_header=x-buildbuddy-api-key=YOUR_KEY' >> .bazelrc
```

### Content-Addressed Caching

All major build tools use content-addressed caching: the cache key is a hash of all inputs (source files, environment variables, tool versions, flags). This guarantees correctness — a cache hit means the output is identical to what a fresh build would produce.

Inputs that affect the cache key:

- Source file contents (not timestamps)
- Dependency versions (lockfile hashes)
- Environment variables declared as inputs
- Tool version (compiler, interpreter)
- Build flags and configuration

Inputs that must NOT affect the cache key (non-hermetic):

- Current timestamp
- Hostname or username
- Undeclared environment variables
- Network calls during build

Non-hermetic builds produce incorrect cache hits. Audit builds that embed timestamps or call external services during compilation.

### Cache Invalidation Strategies

| Strategy | When to Use | Tradeoff |
|----------|-------------|----------|
| Hash-based (default) | Always | Correct, no manual intervention |
| Named cache keys | Dependency updates | Predictable invalidation |
| TTL-based expiry | Large binary assets | May serve stale artifacts |
| Manual bust | Emergency rollback | Requires operator action |

For remote caches, set a retention policy: 7-30 days for most artifacts, 90 days for release builds. Unbounded caches grow without limit and become expensive.

### Compilation Caches

Compilation caches operate at the compiler level, below the build tool. They cache individual compilation units (object files, compiled modules).

| Tool | Languages | Mechanism |
|------|-----------|-----------|
| ccache | C, C++, Objective-C | Wraps compiler, caches object files |
| sccache | C, C++, Rust, CUDA | Distributed, supports S3/GCS backends |
| Turborepo daemon | TypeScript (tsc) | Persistent process, incremental compilation |

```bash
# Install sccache and configure Rust to use it
cargo install sccache
export RUSTC_WRAPPER=sccache

# Configure ccache for C/C++
export CC="ccache gcc"
export CXX="ccache g++"

# Check cache statistics
sccache --show-stats
ccache --show-stats
```

sccache is the preferred choice for polyglot monorepos — it handles Rust, C, and C++ with a single shared remote cache.

## Affected Detection Algorithms

Affected detection determines which packages or targets need to rebuild after a change. The algorithm's granularity determines how much unnecessary work CI performs.

### Nx Affected Detection

Nx computes affected packages through a multi-step pipeline:

1. Run `git diff --name-only <base>...<head>` to get changed files
2. Map each file to its owning project using `project.json` boundaries
3. Traverse the project dependency graph to find all dependents
4. Apply named inputs to filter irrelevant changes (e.g., `*.md` files)

```bash
# Run only affected tests
nx affected --target=test --base=origin/main

# Visualize the affected graph
nx affected:graph --base=origin/main

# Configure named inputs to exclude docs from cache keys
# nx.json
{
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": ["default", "!{projectRoot}/**/*.spec.ts", "!{projectRoot}/README.md"]
  }
}
```

Named inputs are the primary lever for reducing false positives — changes to test files or documentation should not invalidate production build caches.

### Turborepo Affected Detection

Turborepo uses hash-based detection per package. Each package's hash includes its source files, dependencies' hashes, and task configuration.

```bash
# Run only packages that have changed
turbo run build --filter=[origin/main]

# Run a specific package and its dependents
turbo run test --filter=...@myapp/api

# Dry run to see what would execute
turbo run build --dry-run --filter=[origin/main]
```

Turborepo's `--filter` syntax supports three modes:
- `[origin/main]` — packages changed since base branch
- `...@myapp/api` — package and all dependents (upstream)
- `@myapp/api...` — package and all dependencies (downstream)

### Bazel Affected Detection

Bazel operates at action granularity — individual compilation units, not packages. This provides finer-grained caching but requires explicit dependency declarations.

```bash
# Find all targets that depend on a changed file
bazel query "rdeps(//..., //packages/api:lib)"

# Run only affected tests
bazel test $(bazel query "rdeps(//..., set($(git diff --name-only origin/main | xargs -I{} echo //{})))")

# Use Bazel's built-in change detection
bazel build //... --build_event_publish_all_actions
```

Bazel's `rdeps()` query traverses the dependency graph in reverse — given a changed target, it finds everything that transitively depends on it. This is more precise than package-level detection but requires all dependencies to be declared in BUILD files.

### Pants Affected Detection

Pants infers dependencies from import statements, eliminating the need for manual dependency declarations.

```bash
# Run tests for changed files
pants test --changed-since=origin/main

# Include dependents of changed files
pants test --changed-since=origin/main --changed-dependents=transitive

# Lint only changed files
pants lint --changed-since=origin/main
```

Pants's import-based inference works well for Python and Java monorepos where import statements reliably reflect dependencies. For languages with less explicit imports, supplement with manual `dependencies` declarations.

## Incremental Build Strategies

### Task-Level vs Action-Level Granularity

| Dimension | Task-Level (Nx, Turbo) | Action-Level (Bazel, Pants) |
|-----------|------------------------|------------------------------|
| Unit of caching | Entire package task | Individual compilation unit |
| Setup cost | Low — works with existing scripts | High — requires BUILD file authoring |
| Cache granularity | Package boundary | File boundary |
| False invalidation | Higher (whole package) | Lower (only changed files) |
| Best for | JavaScript/TypeScript monorepos | Large polyglot monorepos |

### Cache Ratio Targets

| Cache Type | Cold Cache | Warm Cache (Target) |
|------------|------------|---------------------|
| Local developer | 0% (first run) | >80% (subsequent runs) |
| CI remote cache | 20-40% (new PRs) | >70% (mature repo) |
| Bazel action cache | 30-50% | >85% |

A remote cache hit rate below 50% indicates misconfigured inputs, non-hermetic builds, or insufficient cache retention. Investigate with `--profile` output before adding more CI runners.

### Warm vs Cold Cache Optimization

Optimize for the warm cache path — it is the common case. Cold cache runs (new branches, cache eviction) should be acceptable but not optimized at the expense of warm path complexity.

Strategies to improve warm cache ratio:

- Pin tool versions in lockfiles (prevents tool-version cache misses)
- Declare all environment variables used in builds as explicit inputs
- Separate test artifacts from build artifacts (tests change more frequently)
- Use `--output-style=stream` to surface cache misses during debugging

## Performance Anti-Patterns

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| No remote cache | Every CI run rebuilds from scratch | Configure Nx Cloud, Vercel Remote Cache, or Buildbarn |
| Full clone in CI | Clone takes 5+ minutes | Use `--depth=50` + `--filter=blob:none` |
| Running all tests on every PR | CI takes 30+ minutes regardless of change | Implement affected detection |
| Monolithic packages | One change invalidates entire repo | Split packages at logical boundaries |
| Non-hermetic builds | Cache hits produce wrong output | Audit and eliminate timestamp/network calls in builds |
| Undeclared dependencies | Incorrect affected detection | Declare all cross-package imports explicitly |
| No cache retention policy | Remote cache grows unbounded | Set 7-30 day TTL |
| Ignoring named inputs | Doc changes trigger full rebuild | Configure `namedInputs` to exclude non-code files |
| Sequential task execution | Parallelizable tasks run one at a time | Configure `dependsOn` and concurrency limits |
| Missing build graph | Cannot reason about impact | Generate and visualize dependency graph regularly |

## Scale Thresholds and Tooling

Choose tooling based on current scale and projected growth. Migrating build tools is expensive — select one tier above current needs.

| Scale | Packages | Recommended Tool | Remote Cache |
|-------|----------|-----------------|--------------|
| Small | <10 | Turborepo | Vercel Remote Cache |
| Medium | 10-50 | Turborepo or Nx | Nx Cloud or Vercel |
| Large | 50-200 | Nx | Nx Cloud or self-hosted |
| Very large | 200-1000 | Nx or Bazel | Nx Cloud or Buildbarn |
| Extreme | >1000 | Bazel or Pants | Buildbarn, BuildBuddy, EngFlow |

Git tooling thresholds:

| Repo Size | Recommended Git Strategy |
|-----------|--------------------------|
| <500MB, <50K files | Standard clone |
| 500MB-2GB, 50K-200K files | Shallow clone + sparse checkout |
| >2GB, >200K files | Scalar or partial clone |
| >10GB or >1M files | Sapling + EdenFS |

## Monitoring and Metrics

Track these metrics to detect degradation before users report it.

### Cache Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Remote cache hit rate | >70% | <50% |
| Local cache hit rate | >80% | <60% |
| Cache artifact size (P95) | <500MB | >1GB |
| Cache upload time | <30s | >2min |

### Build Time Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| CI build time P50 | <5min | >15min |
| CI build time P95 | <15min | >30min |
| Developer build time (warm) | <30s | >2min |
| Affected detection time | <10s | >60s |

### Collection and Dashboards

Collect metrics from build tool outputs and expose them to your observability platform.

```bash
# Turborepo: output JSON for parsing
turbo run build --output-logs=json 2>&1 | jq '.tasks[] | {task: .taskId, duration: .duration, cache: .cache.status}'

# Nx: generate build stats
nx run-many --target=build --output-style=static 2>&1 | grep -E "cache|duration"

# Bazel: use build event protocol
bazel build //... --build_event_json_file=build_events.json
```

Key dashboard panels:

- Cache hit rate over time (7-day rolling average)
- CI duration P50 and P95 by branch type (main vs PR)
- Build time breakdown: clone + install + build + test
- Affected package count per PR (distribution histogram)
- Cache miss reasons (new packages, tool version changes, non-hermetic inputs)

Review metrics weekly during active monorepo growth. A sustained drop in cache hit rate or increase in P95 build time signals a configuration problem, not a capacity problem — add capacity only after ruling out configuration issues.

For CI platform configuration (parallelism, runner sizing, artifact storage), see `references/ci-cd-patterns.md`.
For tool selection criteria and migration paths, see `references/tool-selection.md`.
