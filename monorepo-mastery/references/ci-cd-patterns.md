# CI/CD for Monorepos

Sources: GitHub Actions docs, GitLab CI docs, CircleCI docs, Nx Cloud docs, Vercel docs, 2024-2026 DevOps research

Covers: GitHub Actions path filtering, affected-only CI, dynamic matrix generation, reusable workflows, merge queues, GitLab parent-child pipelines, CircleCI dynamic config, remote caching, CI anti-patterns, performance optimization.

## GitHub Actions Patterns

### Path Filters for Workflow Triggering

Use `on.push.paths` and `on.pull_request.paths` to restrict when a workflow runs. This prevents unnecessary runs when unrelated packages change.

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'packages/api/**'
      - 'packages/shared/**'
  pull_request:
    paths:
      - 'packages/api/**'
      - 'packages/shared/**'
```

Path filters apply at the workflow level — the workflow either runs or skips entirely. For job-level control, use `dorny/paths-filter`.

### Job-Level Filtering with dorny/paths-filter

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.filter.outputs.api }}
      web: ${{ steps.filter.outputs.web }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            api:
              - 'packages/api/**'
              - 'packages/shared/**'
            web:
              - 'packages/web/**'
              - 'packages/shared/**'

  build-api:
    needs: changes
    if: ${{ needs.changes.outputs.api == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm --filter api build
```

Include shared packages in each job's condition — a change to `shared` should trigger all downstream consumers.

### Affected-Only CI

Run only tasks affected by the current change. Both Turborepo and Nx compute this from the git diff against a base ref.

**Turborepo:**

```bash
# Packages changed since main, plus their dependents
turbo run build --filter=...[origin/main]

# Changed since previous commit (for push events)
turbo run build --filter=...[HEAD^1]
```

The `...[ref]` syntax means "packages changed since ref". The trailing `...` includes all packages that depend on them.

**Nx:**

```bash
nx affected --target=build --base=origin/main
nx affected --targets=build,test,lint --base=origin/main
```

Nx computes the project graph from `project.json` files. Turborepo uses `package.json` workspaces.

### Dynamic Matrix Generation

Generate a GitHub Actions matrix from affected packages instead of hardcoding package names.

```yaml
jobs:
  detect-affected:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      has-affected: ${{ steps.set-matrix.outputs.has-affected }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - id: set-matrix
        run: |
          AFFECTED=$(npx nx show projects --affected --base=origin/main --json)
          echo "matrix={\"package\":$(echo $AFFECTED)}" >> $GITHUB_OUTPUT
          echo "has-affected=$([ "$AFFECTED" != "[]" ] && echo true || echo false)" >> $GITHUB_OUTPUT

  build:
    needs: detect-affected
    if: needs.detect-affected.outputs.has-affected == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.detect-affected.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: npx nx build ${{ matrix.package }}
```

### Reusable Workflows

Extract common CI logic into reusable workflows to avoid duplication.

```yaml
# .github/workflows/_reusable-node-build.yml
on:
  workflow_call:
    inputs:
      package-name:
        required: true
        type: string
      node-version:
        required: false
        type: string
        default: '20'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npx nx build ${{ inputs.package-name }}
      - run: npx nx test ${{ inputs.package-name }}
```

Call it from a package-specific workflow:

```yaml
jobs:
  build:
    uses: ./.github/workflows/_reusable-node-build.yml
    with:
      package-name: api
```

Prefix reusable workflow filenames with `_` to distinguish them from triggerable workflows.

### Merge Queues

Merge queues serialize PRs before merging to main, preventing the "merge race" where two PRs pass CI independently but break when combined.

**Native GitHub Merge Queue:** Enable in repository settings under "Branches" > "Branch protection rules" > "Require merge queue". Add `merge_group` to workflow triggers:

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]
```

GitHub batches PRs and runs CI on the combined state. If CI passes, all PRs in the group merge atomically.

**Trunk.io:** Manages the merge queue externally. Rebases PRs onto latest main, runs CI, merges when green. Supports parallel testing of independent PRs.

**Aviator:** Provides configurable batching, priority lanes, and Slack notifications. Supports custom merge strategies per branch pattern.

Choose native GitHub merge queue for simplicity. Choose Trunk or Aviator when you need advanced batching, priority lanes, or cross-repository coordination.

## GitLab CI Patterns

### rules:changes for Path-Based Job Filtering

```yaml
build-api:
  script:
    - cd packages/api && npm run build
  rules:
    - changes:
        - packages/api/**/*
        - packages/shared/**/*
    - when: never

build-web:
  script:
    - cd packages/web && npm run build
  rules:
    - changes:
        - packages/web/**/*
        - packages/shared/**/*
    - when: never
```

The `when: never` fallback ensures the job is skipped when no matching paths change.

### Parent-Child Pipelines

Split a large pipeline into a parent that spawns child pipelines per package. This enables parallel execution and independent failure isolation.

```yaml
# .gitlab-ci.yml (parent)
trigger-api:
  trigger:
    include: packages/api/.gitlab-ci.yml
    strategy: depend
  rules:
    - changes:
        - packages/api/**/*
```

`strategy: depend` makes the parent job wait for the child pipeline and inherit its status. Each package maintains its own `.gitlab-ci.yml`.

### Dynamic Pipeline Generation

Generate pipeline YAML programmatically when the package set is large or changes frequently.

```yaml
generate-pipeline:
  script:
    - node scripts/generate-pipeline.js > generated-pipeline.yml
  artifacts:
    paths:
      - generated-pipeline.yml

trigger-generated:
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: generate-pipeline
    strategy: depend
```

The generation script reads workspace packages, detects affected packages via git diff, and outputs a YAML pipeline with one job per affected package.

## CircleCI Patterns

### Dynamic Config: Setup Phase

Enable dynamic config in project settings under "Advanced" > "Enable dynamic config using setup workflows".

```yaml
# .circleci/config.yml
version: 2.1
setup: true

orbs:
  path-filtering: circleci/path-filtering@1.1.4

workflows:
  setup:
    jobs:
      - path-filtering/filter:
          base-revision: main
          config-path: .circleci/continue-config.yml
          mapping: |
            packages/api/.* api true
            packages/web/.* web true
            packages/shared/.* shared true
```

### Continuation Phase

The continuation config receives parameters from the setup phase and uses them to conditionally run workflows.

```yaml
# .circleci/continue-config.yml
version: 2.1

parameters:
  api:
    type: boolean
    default: false
  shared:
    type: boolean
    default: false

workflows:
  api-workflow:
    when:
      or:
        - << pipeline.parameters.api >>
        - << pipeline.parameters.shared >>
    jobs:
      - build-api
```

The `path-filtering` orb maps changed paths to boolean parameters. The continuation config uses those parameters in `when` conditions to activate workflows.

## Affected-Only CI Strategy Comparison

| Tool | Command | Graph Source | Best For |
|------|---------|--------------|----------|
| Nx affected | `nx affected --target=build` | `project.json` + `nx.json` | JS/TS monorepos; plugin ecosystem |
| Turborepo filter | `turbo run build --filter=...[HEAD^1]` | `package.json` workspaces | Simpler JS/TS setups |
| Bazel query | `bazel query 'rdeps(//..., set(changed))'` | `BUILD` files | Polyglot; build correctness critical |
| Pants changed | `pants --changed-since=origin/main test` | `BUILD` files | Python-first; growing polyglot support |
| Moon ci | `moon ci` | `.moon/workspace.yml` | Newer projects; built-in affected detection |

Choose Nx or Turborepo for JavaScript/TypeScript monorepos. Choose Bazel or Pants when the monorepo spans multiple languages and build correctness is critical.

## Remote Caching in CI

Remote caching stores task outputs in a shared cache. Subsequent runs on any machine restore outputs instead of recomputing them.

### Vercel Remote Cache (Turborepo)

Set `TURBO_TOKEN` and `TURBO_TEAM` environment variables in CI:

```yaml
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}
steps:
  - run: turbo run build test lint
```

Turborepo hashes inputs (source files, environment variables, task config) and checks the remote cache before running. Self-host with `turborepo-remote-cache` (open source) to avoid Vercel dependency.

### Nx Cloud

Configure with `NX_CLOUD_ACCESS_TOKEN`. Nx Cloud also supports distributed task execution (DTE), which splits tasks across multiple CI agents automatically.

```yaml
env:
  NX_CLOUD_ACCESS_TOKEN: ${{ secrets.NX_CLOUD_ACCESS_TOKEN }}
steps:
  - run: npx nx affected --target=build --parallel=3
```

### Bazel Remote Execution API

Configure in `.bazelrc` with `--remote_cache=grpcs://your-cache.example.com`. Compatible backends include BuildBuddy, EngFlow, and Google Cloud Build. The RE API enables byte-for-byte reproducible builds across machines.

### Gradle Build Cache

Configure in `settings.gradle.kts` using `HttpBuildCache` pointing to a Gradle Enterprise or Develocity instance. Set `isPush = System.getenv("CI") != null` so only CI runners write to the cache — local builds read only.

## CI Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Run all tests on every PR | CI time grows linearly with repo size | Use affected detection; skip unaffected packages |
| No dependency caching | `npm install` runs from scratch every job | Cache `node_modules`, `~/.cargo`, `~/.gradle` with lockfile-keyed cache |
| No remote build cache | Every CI run recomputes already-computed outputs | Enable Nx Cloud, Vercel Remote Cache, or Bazel RE API |
| Long sequential pipelines | 45-minute pipeline blocks fast feedback | Parallelize lint, test, build; use `--parallel` flags |
| No merge queue at scale | Two PRs break when merged together | Enable merge queue; serialize merges through shared CI run |
| Hardcoded package list in matrix | Adding a package requires updating the workflow | Generate matrix dynamically from workspace packages |
| Fetching full git history unnecessarily | Slow checkout on large repos | Use `fetch-depth: 0` only for affected detection; shallow clone for builds |
| No build artifact reuse | Build job reruns in deploy job | Upload artifacts from build; download in deploy |

## CI Performance Optimization

### Parallel Jobs

Run `npx nx affected --target=lint --parallel=3` and `--target=test --parallel=3` as separate parallel jobs. Set `--parallel` to the number of CPU cores on the runner — GitHub-hosted runners have 2 cores; self-hosted runners can have more.

### Caching Dependencies

```yaml
# Node.js — built-in cache via setup-node
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'   # or 'pnpm', 'yarn'

# Rust — key on Cargo.lock
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/registry/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

# Go — key on go.sum
- uses: actions/cache@v4
  with:
    path: ~/go/pkg/mod
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
```

Key caches on the lockfile hash so the cache invalidates when dependencies change.

### Shallow Clones and Sparse Checkout

Use `fetch-depth: 0` only for affected detection jobs that need full git history. For build and deploy jobs, use `fetch-depth: 1` (shallow) or sparse checkout:

```yaml
- uses: actions/checkout@v4
  with:
    sparse-checkout: |
      packages/api
      packages/shared
      package.json
      turbo.json
```

Sparse checkout reduces checkout time significantly in large monorepos. Use it for deployment jobs that only need one package's files.

### Artifact Reuse Between Jobs

Upload build outputs from the build job and download them in the deploy job. This avoids rebuilding in the deploy stage.

```yaml
build:
  steps:
    - run: npm run build
    - uses: actions/upload-artifact@v4
      with:
        name: build-output
        path: dist/
        retention-days: 1   # only needed within the workflow run

deploy:
  needs: build
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: build-output
        path: dist/
    - run: ./scripts/deploy.sh
```

### Self-Hosted Runners

GitHub-hosted runners have 2 CPU cores and 7 GB RAM. For large monorepos, self-hosted runners with more resources reduce CI time significantly. Run on EC2, GCP, or Azure using managed solutions like Buildjet, Namespace, or Actuated. Size runners to match parallelism — 8-core runners support `--parallel=8` effectively. Use spot/preemptible instances for non-critical jobs and on-demand instances for merge queue jobs where reliability matters.

## Cross-Reference

For git performance and repository scaling strategies, see `references/scaling-and-performance.md`.
For versioning, changesets, and publishing workflows, see `references/versioning-and-publishing.md`.
For build tool selection and configuration, see `references/tool-selection.md`.
