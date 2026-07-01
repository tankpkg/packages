---
name: "@tank/uv-python"
description: |
  Python project management with uv -- the Rust-powered replacement for pip,
  pip-tools, pipx, poetry, pyenv, virtualenv, and twine. Covers project
  initialization (uv init, pyproject.toml), dependency management (uv add,
  uv remove, uv lock, uv sync), Python version management (uv python install,
  uv python pin), virtual environments, scripts with inline metadata (PEP 723),
  tool management (uvx, uv tool install), workspaces for monorepos, building
  and publishing packages (uv build, uv publish), Docker integration
  (multi-stage builds, cache mounts, intermediate layers), CI/CD patterns
  (GitHub Actions with astral-sh/setup-uv), and migration from pip, poetry,
  and pipenv. Synthesizes Astral uv official documentation (docs.astral.sh/uv),
  PEP 723, PEP 735, PEP 751, and Python Packaging User Guide.

  Trigger phrases: "uv", "uv python", "uv init", "uv add", "uv run",
  "uv sync", "uv lock", "uv pip", "uv build", "uv publish", "uv tool",
  "uvx", "uv workspace", "uv monorepo", "uv docker", "uv ci",
  "uv venv", "uv python install", "uv python pin", "pyproject.toml uv",
  "uv vs pip", "uv vs poetry", "migrate to uv", "uv script",
  "inline script metadata", "astral uv", "uv cache", "uv.lock",
  "python package manager", "uv dependency", "uv pip compile"
---

# UV Python

## Core Philosophy

1. **One tool replaces many** -- uv unifies pip, pip-tools, pipx, poetry, pyenv, virtualenv, and twine into a single binary. Prefer uv's project interface over its pip-compatibility layer for new projects.
2. **Speed is a feature** -- 10-100x faster than pip through Rust implementation, aggressive caching, and parallel resolution. Use the global cache and lockfile to maximize this advantage.
3. **Lockfiles are non-negotiable** -- Always commit `uv.lock` to version control. The universal lockfile captures cross-platform resolutions, eliminating "works on my machine" failures.
4. **Declarative over imperative** -- Define dependencies in `pyproject.toml`, not through ad-hoc `pip install`. Use inline metadata for scripts, `pyproject.toml` for projects.
5. **Environments are disposable** -- uv creates and manages `.venv` automatically. Never manually modify the project environment with `uv pip install` -- use `uv add` for project deps, `uv run --with` for one-off needs.

## Quick-Start: Common Problems

### "Start a new Python project"
1. Run `uv init my-project` (application) or `uv init --lib my-lib` (library)
2. Add dependencies: `uv add fastapi httpx`
3. Add dev dependencies: `uv add --dev pytest ruff`
4. Run code: `uv run python main.py` or `uv run pytest`
-> See `references/project-management.md`

### "Migrate from pip/poetry to uv"
1. Import requirements: `uv add -r requirements.in -c requirements.txt`
2. Import dev deps: `uv add --dev -r requirements-dev.in -c requirements-dev.txt`
3. From poetry: copy deps from `[tool.poetry.dependencies]` to `[project.dependencies]`
4. Verify: `uv sync --locked` then `uv run pytest`
-> See `references/migration.md`

### "Run a one-off script with dependencies"
1. Create script: `uv init --script example.py --python 3.12`
2. Add inline deps: `uv add --script example.py requests rich`
3. Run: `uv run example.py`
-> See `references/scripts-and-tools.md`

### "Set up CI/CD with uv"
1. Install: `uses: astral-sh/setup-uv@v7` with pinned version
2. Sync: `uv sync --locked --all-extras --dev`
3. Test: `uv run pytest`
4. Cache: enable with `enable-cache: true`
-> See `references/ci-cd-integration.md`

### "Optimize Docker builds with uv"
1. Copy binary: `COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/`
2. Use intermediate layers: sync deps first, copy source second
3. Cache mount: `--mount=type=cache,target=/root/.cache/uv`
-> See `references/docker-integration.md`

## Decision Trees

### Project Type Selection

| Signal | Command |
|--------|---------|
| Application (CLI, web service) | `uv init my-app` |
| Library (published to PyPI) | `uv init --lib my-lib` |
| Script (single file) | `uv init --script example.py` |
| Monorepo with shared deps | `uv init` + `[tool.uv.workspace]` |

### Dependency Management

| Need | Approach |
|------|----------|
| Production dependency | `uv add package` |
| Dev-only dependency | `uv add --dev package` |
| Custom dependency group | `uv add --group lint ruff` |
| Optional extra | `uv add --optional viz matplotlib` |
| Git source | `uv add git+https://github.com/org/repo` |
| Local path | `uv add --editable ../my-lib` |
| Platform-specific | `uv add "pkg; sys_platform == 'linux'"` |

### Python Version Management

| Task | Command |
|------|---------|
| Install Python | `uv python install 3.12` |
| Pin version for project | `uv python pin 3.12` |
| Use specific version | `uv run --python 3.11 script.py` |
| List installed | `uv python list` |

## Reference Index

| File | Contents |
|------|----------|
| `references/project-management.md` | Project init, pyproject.toml structure, dependency management (add/remove/sync/lock), dependency sources, optional and dev deps, dependency groups |
| `references/python-and-environments.md` | Python version installation and pinning, virtual environment creation and management, environment variables, .python-version files |
| `references/scripts-and-tools.md` | Inline script metadata (PEP 723), uv run, uv tool install, uvx, shebangs, script locking |
| `references/lockfile-and-resolution.md` | uv.lock format, universal resolution, upgrade strategies, conflict resolution, resolution overrides, PEP 751 pylock.toml |
| `references/workspaces.md` | Workspace setup, member management, shared lockfile, workspace sources, layout patterns, when to use vs path deps |
| `references/building-and-publishing.md` | uv build, uv publish, build systems, version bumping, trusted publishing, PyPI and custom indexes |
| `references/docker-integration.md` | Docker images, multi-stage builds, intermediate layers, cache optimization, workspace Docker patterns, compose watch |
| `references/ci-cd-integration.md` | GitHub Actions (setup-uv), caching, matrix testing, trusted publishing workflow, GitLab CI, private repos |
| `references/migration.md` | Migration from pip/pip-tools, poetry, pipenv, pdm; requirements file import, constraint preservation, platform-specific migration |
