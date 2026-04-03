# Workflow Syntax

Sources: GitHub Actions official documentation (2026), GitHub workflow syntax reference, GitHub expressions reference

Covers: workflow YAML structure, job configuration, step types, expressions and operators, contexts, built-in functions, conditionals, outputs, and environment variables.

## Workflow File Structure

Workflow files live in `.github/workflows/` with `.yml` or `.yaml` extension. A repository can have multiple workflows. Each runs independently unless chained via `workflow_run`.

```yaml
name: CI                          # Display name (optional but recommended)

on: [push, pull_request]          # Trigger(s)

permissions: {}                   # Top-level permissions (restrict globally)

env:                              # Workflow-level environment variables
  NODE_ENV: test

jobs:
  build:                          # Job ID (kebab-case)
    runs-on: ubuntu-latest        # Runner label
    permissions:                  # Job-level permissions (override top-level)
      contents: read
    steps:
      - uses: actions/checkout@v4 # Action step
      - run: npm test             # Shell step
```

## Jobs

### Job Properties

| Property | Purpose | Example |
|----------|---------|---------|
| `runs-on` | Runner label | `ubuntu-latest`, `windows-latest`, `macos-latest`, `self-hosted` |
| `needs` | Job dependencies | `needs: [build, lint]` |
| `if` | Conditional execution | `if: github.ref == 'refs/heads/main'` |
| `permissions` | GITHUB_TOKEN scopes | `permissions: { contents: read }` |
| `environment` | Deployment environment | `environment: production` |
| `concurrency` | Concurrency group | `concurrency: { group: deploy, cancel-in-progress: true }` |
| `timeout-minutes` | Max job duration | `timeout-minutes: 30` |
| `strategy` | Matrix configuration | See `references/matrix-and-concurrency.md` |
| `container` | Docker container for job | `container: node:20` |
| `services` | Sidecar containers | `services: { postgres: { image: postgres:16 } }` |
| `outputs` | Values for downstream jobs | `outputs: { version: ${{ steps.ver.outputs.v }} }` |
| `defaults` | Default shell/working-directory | `defaults: { run: { shell: bash } }` |

### Job Dependencies

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]

  test:
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    needs: [lint, test]           # Runs only after both complete successfully
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps: [...]
```

Use `needs` to create a DAG (directed acyclic graph) of jobs. A job runs only when all `needs` jobs succeed, unless overridden with `if: always()`.

### Accessing Outputs Across Jobs

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - id: set-matrix
        run: echo "matrix={\"node\":[18,20,22]}" >> "$GITHUB_OUTPUT"

  test:
    needs: prepare
    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "Testing on Node ${{ matrix.node }}"
```

## Steps

### Step Types

| Type | Syntax | Use Case |
|------|--------|----------|
| Action | `uses: owner/repo@ref` | Reusable community/official actions |
| Shell command | `run: command` | Inline scripts |
| Composite reference | `uses: ./path/to/action` | Local composite actions |

### Step Properties

| Property | Purpose |
|----------|---------|
| `id` | Identifier for referencing outputs |
| `name` | Display name in UI |
| `uses` | Action to run |
| `run` | Shell command(s) |
| `with` | Input parameters for action |
| `env` | Step-level environment variables |
| `if` | Conditional execution |
| `continue-on-error` | Do not fail job if step fails |
| `timeout-minutes` | Max step duration |
| `working-directory` | Override default directory |
| `shell` | Override default shell (`bash`, `pwsh`, `python`, `cmd`) |

### Multi-line Run Commands

```yaml
- name: Build and test
  run: |
    npm ci
    npm run build
    npm test
```

The `|` preserves newlines. Each line runs sequentially in the same shell session. If any line fails (non-zero exit), the step fails immediately (bash `set -e` behavior by default).

## Expressions

Expressions use the `${{ }}` syntax. They are evaluated at workflow parse time or runtime depending on context.

### Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `==` | Equality | `github.ref == 'refs/heads/main'` |
| `!=` | Inequality | `github.event_name != 'schedule'` |
| `&&` | Logical AND | `success() && github.ref == 'refs/heads/main'` |
| `\|\|` | Logical OR | `failure() \|\| cancelled()` |
| `!` | Negation | `!contains(github.event.head_commit.message, '[skip ci]')` |

### Type Coercion

GitHub Actions loosely coerces types in comparisons. This causes subtle bugs:

| Value | Boolean coercion |
|-------|-----------------|
| `null` | `false` |
| `0` | `false` |
| `''` (empty string) | `false` |
| `'0'` (string zero) | `true` (not false!) |
| Any other string | `true` |
| Any object | `true` |

Compare strings explicitly: use `== 'true'` not just a truthy check.

## Contexts

| Context | Contains | Common Properties |
|---------|----------|-------------------|
| `github` | Event and repo info | `.ref`, `.sha`, `.event_name`, `.repository`, `.actor`, `.event` |
| `env` | Environment variables | Any variable set in `env:` blocks |
| `vars` | Repository/org variables | Configuration variables (non-secret) |
| `secrets` | Encrypted secrets | `secrets.GITHUB_TOKEN`, custom secrets |
| `job` | Current job info | `.status`, `.container`, `.services` |
| `steps` | Step outputs/status | `steps.<id>.outputs.<name>`, `steps.<id>.outcome` |
| `runner` | Runner info | `.os`, `.arch`, `.temp`, `.tool_cache` |
| `needs` | Dependent job results | `needs.<job>.outputs.<name>`, `needs.<job>.result` |
| `matrix` | Current matrix values | `matrix.<key>` |
| `inputs` | Workflow inputs | For `workflow_dispatch` and reusable workflows |
| `strategy` | Matrix strategy info | `.fail-fast`, `.job-index`, `.job-total` |

### The `github` Context — Key Properties

```yaml
github.event_name        # "push", "pull_request", "schedule", etc.
github.ref               # "refs/heads/main", "refs/pull/42/merge"
github.ref_name          # "main", "42/merge"
github.sha               # Full commit SHA
github.head_ref          # PR source branch (only on pull_request)
github.base_ref          # PR target branch (only on pull_request)
github.repository        # "owner/repo"
github.actor             # Username that triggered the workflow
github.run_id            # Unique workflow run ID
github.run_number        # Sequential run number per workflow
github.event             # Full webhook payload
```

## Built-in Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `contains(search, item)` | String/array contains | `contains(github.event.head_commit.message, '[skip ci]')` |
| `startsWith(str, prefix)` | Prefix check | `startsWith(github.ref, 'refs/tags/')` |
| `endsWith(str, suffix)` | Suffix check | `endsWith(matrix.os, 'latest')` |
| `format(str, args...)` | String formatting | `format('Hello {0}', github.actor)` |
| `join(arr, sep)` | Join array | `join(matrix.os, ', ')` |
| `toJSON(value)` | Convert to JSON string | `toJSON(github.event)` |
| `fromJSON(str)` | Parse JSON string | `fromJSON(needs.prep.outputs.matrix)` |
| `hashFiles(patterns...)` | SHA-256 of files | `hashFiles('**/package-lock.json')` |
| `success()` | Previous steps succeeded | Default `if:` condition |
| `failure()` | Any previous step failed | `if: failure()` |
| `always()` | Run regardless | `if: always()` — cleanup steps |
| `cancelled()` | Workflow was cancelled | `if: cancelled()` |

### Status Check Functions in `if:`

| Function | Evaluates To True When |
|----------|----------------------|
| `success()` | All previous steps succeeded (default) |
| `failure()` | Any previous step failed |
| `always()` | Always — runs even if cancelled |
| `cancelled()` | Workflow was cancelled |

Combine: `if: always() && steps.test.outcome == 'failure'` — run cleanup only when tests failed.

## Environment Variables

### Setting Environment Variables

```yaml
# Workflow level — available to all jobs
env:
  CI: true

jobs:
  build:
    # Job level — available to all steps in this job
    env:
      NODE_ENV: production
    steps:
      # Step level — available only in this step
      - run: echo "$MY_VAR"
        env:
          MY_VAR: step-only

      # Dynamic — set for subsequent steps
      - run: echo "VERSION=1.2.3" >> "$GITHUB_ENV"
      - run: echo "$VERSION"  # Available here
```

### Setting Outputs

```yaml
steps:
  - id: extract
    run: echo "version=$(cat package.json | jq -r .version)" >> "$GITHUB_OUTPUT"
  - run: echo "Version is ${{ steps.extract.outputs.version }}"
```

Write to `$GITHUB_OUTPUT` (not the deprecated `::set-output`). Write to `$GITHUB_ENV` for environment variables available in subsequent steps.

### Default Environment Variables

| Variable | Value |
|----------|-------|
| `GITHUB_SHA` | Commit SHA |
| `GITHUB_REF` | Branch/tag ref |
| `GITHUB_REPOSITORY` | `owner/repo` |
| `GITHUB_WORKSPACE` | Checkout directory |
| `GITHUB_TOKEN` | Auto-generated token |
| `RUNNER_OS` | `Linux`, `Windows`, `macOS` |
| `RUNNER_ARCH` | `X86`, `X64`, `ARM`, `ARM64` |
| `GITHUB_OUTPUT` | File path for step outputs |
| `GITHUB_ENV` | File path for dynamic env vars |
| `GITHUB_STEP_SUMMARY` | File path for job summary markdown |

## Job Summaries

Write markdown to `$GITHUB_STEP_SUMMARY` to display rich content in the Actions UI:

```yaml
- name: Generate summary
  run: |
    echo "## Test Results" >> "$GITHUB_STEP_SUMMARY"
    echo "| Suite | Status |" >> "$GITHUB_STEP_SUMMARY"
    echo "|-------|--------|" >> "$GITHUB_STEP_SUMMARY"
    echo "| Unit  | Pass   |" >> "$GITHUB_STEP_SUMMARY"
```

## Service Containers

Run sidecar services (databases, caches) alongside job steps:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm test
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/postgres
```

Services start before steps and are accessible via `localhost` when using `ports` mapping. Use `options` for Docker health checks to ensure the service is ready before tests run.
