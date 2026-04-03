# Migration

Sources: Astral uv documentation (docs.astral.sh/uv), pip documentation (pip.pypa.io), Poetry documentation (python-poetry.org), Pipenv documentation (pipenv.pypa.io), PDM documentation (pdm-project.org)

Covers: migration from pip/pip-tools, poetry, pipenv, and pdm to uv's project interface. Includes requirements file import, constraint preservation, platform-specific migration, development dependency groups, and source mapping.

## Migration from pip / pip-tools

### Quick Migration

```bash
# 1. Initialize uv project
uv init

# 2. Import requirements with locked versions as constraints
uv add -r requirements.in -c requirements.txt

# 3. Import dev requirements
uv add --dev -r requirements-dev.in -c requirements-dev.txt

# 4. Verify
uv sync --locked
uv run pytest
```

### Step-by-Step

#### Create pyproject.toml

```bash
uv init
```

This creates a minimal `pyproject.toml`. If one already exists, skip this step.

#### Import Base Dependencies

Use `-r` for the input requirements and `-c` for the compiled constraints:

```bash
uv add -r requirements.in -c requirements.txt
```

The `-r requirements.in` provides the declared dependencies (with loose constraints). The `-c requirements.txt` pins versions to match your existing lockfile -- preventing unexpected version changes during migration.

Without constraints:

```bash
# Re-resolves from scratch (may pick different versions)
uv add -r requirements.in
```

#### Import Development Dependencies

Strip parent references from dev requirements before importing:

```bash
# If requirements-dev.in includes `-r requirements.in`, strip it
sed '/^-r /d' requirements-dev.in | uv add --dev -r - -c requirements-dev.txt
```

Or manually:

```bash
uv add --dev -r requirements-dev.in -c requirements-dev.txt
```

If the dev file includes `-r requirements.in`, uv handles it gracefully -- base deps land in the correct `[project.dependencies]` section.

#### Import Additional Groups

```bash
uv add --group docs -r requirements-docs.in -c requirements-docs.txt
uv add --group test -r requirements-test.in -c requirements-test.txt
```

#### Handle Platform-Specific Lock Files

If you have separate lockfiles per platform (e.g., `requirements-linux.txt`, `requirements-win.txt`), add markers before importing:

```bash
# Add markers to platform-specific lockfiles
uv pip compile requirements.in -o requirements-linux.txt --python-platform linux --no-strip-markers
uv pip compile requirements.in -o requirements-win.txt --python-platform windows --no-strip-markers

# Import with multiple constraints
uv add -r requirements.in -c requirements-linux.txt -c requirements-win.txt
```

### Concept Mapping: pip to uv

| pip / pip-tools | uv | Notes |
|-----------------|-----|-------|
| `requirements.in` | `pyproject.toml` [project.dependencies] | Declared dependencies |
| `requirements.txt` | `uv.lock` | Locked versions |
| `pip install -r requirements.txt` | `uv sync` | Install locked deps |
| `pip install package` | `uv add package` | Add dependency |
| `pip uninstall package` | `uv remove package` | Remove dependency |
| `pip-compile` | `uv lock` | Resolve and lock |
| `pip freeze` | `uv pip freeze` | List installed |
| `pip list` | `uv pip list` | List packages |
| `python -m venv .venv` | `uv venv` (or automatic) | Create environment |
| `source .venv/bin/activate` | `uv run` (or activate) | Use environment |
| `pip install -e .` | `uv sync` (auto-editable) | Editable install |

### Gradual Migration with uv pip

Not ready for full migration? Use `uv pip` as a drop-in pip replacement:

```bash
# Same commands, 10-100x faster
uv pip install -r requirements.txt
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
uv pip freeze
```

This gives speed benefits without changing workflow.

## Migration from Poetry

### Concept Mapping: Poetry to uv

| Poetry | uv | Notes |
|--------|-----|-------|
| `pyproject.toml` [tool.poetry.dependencies] | `pyproject.toml` [project.dependencies] | PEP 621 standard |
| `poetry.lock` | `uv.lock` | Lockfile |
| `poetry install` | `uv sync` | Install deps |
| `poetry add package` | `uv add package` | Add dep |
| `poetry remove package` | `uv remove package` | Remove dep |
| `poetry run cmd` | `uv run cmd` | Run in env |
| `poetry lock` | `uv lock` | Resolve |
| `poetry build` | `uv build` | Build package |
| `poetry publish` | `uv publish` | Publish |
| `poetry shell` | `source .venv/bin/activate` | Activate env |
| `[tool.poetry.group.dev.dependencies]` | `[dependency-groups] dev = [...]` | PEP 735 |
| `[tool.poetry.extras]` | `[project.optional-dependencies]` | Extras |

### Migration Steps

#### 1. Convert Dependencies

Move from Poetry's format to PEP 621:

```toml
# Poetry format (BEFORE)
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115"
httpx = ">=0.27,<1"

[tool.poetry.group.dev.dependencies]
pytest = "^8"
ruff = "^0.8"
```

```toml
# uv format (AFTER)
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115,<1",
    "httpx>=0.27,<1",
]

[dependency-groups]
dev = [
    "pytest>=8,<9",
    "ruff>=0.8,<1",
]
```

#### 2. Version Constraint Translation

| Poetry | PEP 508 (uv) | Meaning |
|--------|-------------|---------|
| `^1.2.3` | `>=1.2.3,<2` | Compatible release (major) |
| `^0.2.3` | `>=0.2.3,<0.3` | Compatible release (minor for 0.x) |
| `~1.2.3` | `>=1.2.3,<1.3` | Tilde (patch flexibility) |
| `>=1.2,<2` | `>=1.2,<2` | Same syntax |
| `1.2.3` | `==1.2.3` | Exact version |
| `*` | (omit constraint) | Any version |

#### 3. Convert Sources

```toml
# Poetry
[tool.poetry.dependencies]
my-lib = { path = "../my-lib", develop = true }
other = { git = "https://github.com/org/other.git", branch = "main" }

# uv
[project]
dependencies = ["my-lib", "other"]

[tool.uv.sources]
my-lib = { path = "../my-lib", editable = true }
other = { git = "https://github.com/org/other.git", branch = "main" }
```

#### 4. Convert Build System

```toml
# Poetry
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# uv (use hatchling or any PEP 517 backend)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 5. Lock and Verify

```bash
uv lock
uv sync --all-extras --dev
uv run pytest
```

## Migration from Pipenv

### Concept Mapping: Pipenv to uv

| Pipenv | uv | Notes |
|--------|-----|-------|
| `Pipfile` | `pyproject.toml` | Project metadata |
| `Pipfile.lock` | `uv.lock` | Lockfile |
| `pipenv install` | `uv sync` | Install |
| `pipenv install pkg` | `uv add pkg` | Add dep |
| `pipenv install --dev pkg` | `uv add --dev pkg` | Add dev dep |
| `pipenv run cmd` | `uv run cmd` | Run command |
| `pipenv lock` | `uv lock` | Lock |
| `pipenv shell` | `source .venv/bin/activate` | Activate |

### Migration Steps

```bash
# 1. Export Pipfile to requirements format
pipenv requirements > requirements.txt
pipenv requirements --dev > requirements-dev.txt

# 2. Initialize uv project
uv init

# 3. Import
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# 4. Verify
uv sync --locked
uv run pytest
```

## Migration from PDM

### Concept Mapping: PDM to uv

| PDM | uv | Notes |
|-----|-----|-------|
| `pdm.lock` | `uv.lock` | Lockfile |
| `pdm add` | `uv add` | Add dep |
| `pdm remove` | `uv remove` | Remove dep |
| `pdm install` | `uv sync` | Install |
| `pdm run` | `uv run` | Run |
| `pdm lock` | `uv lock` | Lock |
| `[tool.pdm.dev-dependencies]` | `[dependency-groups]` | Dev deps |

PDM already uses PEP 621 `[project.dependencies]`, so the pyproject.toml format is mostly compatible. Main changes:

```bash
# 1. Move dev deps from [tool.pdm.dev-dependencies] to [dependency-groups]
# 2. Move [tool.pdm.source] to [[tool.uv.index]]
# 3. Re-lock
uv lock
uv sync
uv run pytest
```

## Post-Migration Cleanup

After successful migration:

1. Delete old files: `requirements.in`, `requirements.txt`, `Pipfile`, `Pipfile.lock`, `poetry.lock`, `pdm.lock`
2. Update CI/CD pipelines to use uv commands
3. Update Docker files to use uv (see `references/docker-integration.md`)
4. Update contributing documentation
5. Commit `pyproject.toml` and `uv.lock`
6. Run full test suite: `uv run pytest`

## Dependency Source Mapping

| Source Type | pip/requirements.txt | uv |
|-------------|---------------------|-----|
| Local path | `./libs/mylib` | `[tool.uv.sources] mylib = { path = "./libs/mylib" }` |
| Editable | `-e ./libs/mylib` | `mylib = { path = "./libs/mylib", editable = true }` |
| Git repo | `pkg @ git+https://github.com/org/pkg` | `pkg = { git = "https://github.com/org/pkg" }` |
| Git tag | `pkg @ git+https://github.com/org/pkg@v1.0` | `pkg = { git = "...", tag = "v1.0" }` |
| URL | `https://example.com/pkg.whl` | `pkg = { url = "https://example.com/pkg.whl" }` |
| Extra index | `--extra-index-url https://...` | `[[tool.uv.index]] url = "https://..."` |

## Migration Decision Guide

| Current Tool | Effort | Strategy |
|-------------|--------|----------|
| pip + requirements.txt | Low | `uv add -r` import, done |
| pip-tools | Low | `uv add -r -c` import with constraints |
| Poetry | Medium | Manual pyproject.toml conversion |
| Pipenv | Low | Export then import |
| PDM | Low | Already PEP 621, just re-lock |
| Conda | High | Extract pip deps, handle conda-only separately |
