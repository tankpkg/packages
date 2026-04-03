# CI/CD Integration

Sources: Astral uv documentation (docs.astral.sh/uv), astral-sh/setup-uv GitHub Action, astral-sh/trusted-publishing-examples, GitHub Actions documentation (docs.github.com)

Covers: GitHub Actions setup with astral-sh/setup-uv, Python version matrix testing, caching strategies, trusted publishing to PyPI, GitLab CI patterns, and private repository access.

## GitHub Actions

### Basic Setup

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.11.3"  # Pin uv version

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        run: uv run pytest
```

### setup-uv Options

| Option | Description | Default |
|--------|-------------|---------|
| `version` | uv version to install | Latest |
| `enable-cache` | Persist uv cache across runs | `false` |
| `cache-dependency-glob` | Glob for cache key | `**/uv.lock` |
| `python-version` | Python version to use | From project |

### Python Version Matrix

Test across multiple Python versions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.11.3"
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        run: uv run pytest
```

Setting `python-version` on setup-uv overrides `.python-version` and `requires-python`.

### Cross-Platform Matrix

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.11.3"
          python-version: ${{ matrix.python-version }}
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        run: uv run pytest
```

## Caching

### Built-in Cache (Recommended)

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
```

Automatically caches and restores the uv cache directory.

### Manual Cache Management

```yaml
jobs:
  test:
    env:
      UV_CACHE_DIR: /tmp/.uv-cache

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7

      - name: Restore cache
        uses: actions/cache@v5
        with:
          path: /tmp/.uv-cache
          key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
            uv-${{ runner.os }}

      # ... install and test ...

      - name: Minimize cache
        run: uv cache prune --ci
```

`uv cache prune --ci` removes unnecessary cache entries to reduce storage.

### Self-Hosted Runner Cache

For non-ephemeral runners, avoid unbounded cache growth:

```yaml
env:
  UV_CACHE_DIR: ${{ github.workspace }}/.cache/uv
```

Use a post-job hook to clean:

```bash
#!/usr/bin/env sh
uv cache clean
```

Set `ACTIONS_RUNNER_HOOK_JOB_STARTED` to point to this script.

## Linting and Type Checking Workflow

```yaml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.11.3"
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked --dev

      - name: Lint
        run: uv run ruff check .

      - name: Format check
        run: uv run ruff format --check .

      - name: Type check
        run: uv run mypy src/
```

## Trusted Publishing to PyPI

Publish without storing credentials using OIDC-based trusted publishing:

```yaml
name: Publish

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7

      - name: Install Python
        run: uv python install 3.13

      - name: Build
        run: uv build

      - name: Smoke test (wheel)
        run: uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py

      - name: Smoke test (source distribution)
        run: uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py

      - name: Publish
        run: uv publish
```

### Setup Steps

1. Create `pypi` environment in GitHub repo Settings > Environments
2. Add a trusted publisher on PyPI project Settings > Publishing
3. Ensure workflow, repository, and environment name match the publisher config
4. Tag and push: `git tag -a v1.0.0 -m v1.0.0 && git push --tags`

## Token-Based Publishing

When trusted publishing is not available:

```yaml
- name: Publish
  run: uv publish --token ${{ secrets.PYPI_TOKEN }}
```

Store the token as a repository secret.

## Private Repository Access

Access private Git dependencies in CI:

```yaml
steps:
  - name: Register PAT
    run: echo "${{ secrets.MY_PAT }}" | gh auth login --with-token

  - name: Configure Git credentials
    run: gh auth setup-git

  - name: Install dependencies
    run: uv sync --locked
```

The `gh auth setup-git` command configures a Git credential helper that uses the PAT for all github.com requests.

## GitLab CI

```yaml
# .gitlab-ci.yml
variables:
  UV_CACHE_DIR: .cache/uv

stages:
  - test
  - publish

test:
  image: ghcr.io/astral-sh/uv:python3.12-trixie-slim
  stage: test
  cache:
    key: uv-$CI_COMMIT_REF_SLUG
    paths:
      - .cache/uv
  script:
    - uv sync --locked --all-extras --dev
    - uv run pytest
    - uv run ruff check .

publish:
  image: ghcr.io/astral-sh/uv:python3.12-trixie-slim
  stage: publish
  only:
    - tags
  script:
    - uv build
    - uv publish --token $PYPI_TOKEN
```

## Using uv pip in CI

For projects not yet using the project interface:

```yaml
steps:
  - uses: actions/checkout@v6

  - uses: actions/setup-python@v6
    with:
      python-version-file: ".python-version"

  - name: Install uv
    uses: astral-sh/setup-uv@v7
    with:
      version: "0.11.3"

  - name: Install requirements
    run: uv pip install --system -r requirements.txt

  - name: Run tests
    run: pytest
```

Set `UV_SYSTEM_PYTHON=1` or use `--system` when installing into the runner's Python rather than a virtual environment.

## CI Best Practices

| Practice | Rationale |
|----------|-----------|
| Pin uv version | Reproducible CI builds |
| Use `--locked` | Fail on stale lockfile, catch drift |
| Enable cache | Faster subsequent runs |
| Run `uv cache prune --ci` | Keep cache size manageable |
| Use matrix strategy | Test across Python versions and platforms |
| Separate lint and test jobs | Faster feedback, parallel execution |
| Use trusted publishing | No credential management for PyPI |
| Smoke test before publishing | Catch packaging mistakes |

## Common CI Patterns

| Scenario | Approach |
|----------|----------|
| Monorepo with workspace | `uv sync --locked` + `uv run --package X pytest` |
| Library with extras | `uv sync --locked --all-extras --dev` |
| Application deployment | `uv sync --locked --no-dev` + Docker build |
| Documentation build | `uv sync --locked --group docs` + `uv run mkdocs build` |
| Release pipeline | Tag trigger -> build -> smoke test -> publish |
