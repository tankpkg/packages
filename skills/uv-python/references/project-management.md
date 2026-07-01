# Project Management

Sources: Astral uv documentation (docs.astral.sh/uv), Python Packaging User Guide (packaging.python.org), PEP 621 (pyproject.toml metadata), PEP 735 (dependency groups)

Covers: project initialization, pyproject.toml structure, dependency management with uv add/remove, dependency sources (git, path, index, workspace), optional dependencies, development dependency groups, and environment syncing.

## Creating Projects

### Application vs Library

| Type | Command | Build System | Key Difference |
|------|---------|-------------|----------------|
| Application | `uv init my-app` | None by default | Not installable as package, entry point via `uv run` |
| Library | `uv init --lib my-lib` | Included | Installable, publishable, src/ layout |
| Script | `uv init --script example.py` | N/A | Single file with inline metadata |
| Packaged app | `uv init --app --package my-app` | Included | Application that is also installable |

### uv init Options

```bash
# Basic application
uv init my-project

# Library with src/ layout
uv init --lib my-lib

# Specify Python version
uv init my-project --python 3.12

# Create inside existing directory
cd existing-dir && uv init

# Initialize inside a workspace (auto-adds as member)
cd workspace-root/packages && uv init new-package
```

When `uv init` runs inside an existing project with `[tool.uv.workspace]`, it automatically adds the new project as a workspace member.

## pyproject.toml Structure

### Minimal Project

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []
```

### Full Project

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "A sample project"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "httpx>=0.27",
]

[project.optional-dependencies]
viz = ["matplotlib>=3.9"]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.8"]
docs = ["mkdocs>=1.6"]

[project.scripts]
my-cli = "my_project:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
default-groups = ["dev"]

[tool.uv.sources]
# Development-only sources (not published)
```

### Key Sections

| Section | Purpose | Standard |
|---------|---------|----------|
| `[project]` | Core metadata (name, version, deps) | PEP 621 |
| `[project.optional-dependencies]` | Published extras | PEP 621 |
| `[dependency-groups]` | Local dev dependencies | PEP 735 |
| `[tool.uv.sources]` | Alternative dep sources (dev only) | uv-specific |
| `[tool.uv]` | uv configuration | uv-specific |
| `[build-system]` | Build backend | PEP 517 |

## Adding Dependencies

### Basic Usage

```bash
# Add to project.dependencies
uv add fastapi httpx

# Add with version constraint
uv add "fastapi>=0.115,<1"

# Add with extras
uv add "pandas[excel,plot]"
```

When adding, uv automatically:
1. Updates `pyproject.toml`
2. Re-resolves the lockfile
3. Syncs the environment

### Version Constraint Styles

| Style | Example | Meaning |
|-------|---------|---------|
| Compatible release | `~=1.4` | `>=1.4,<2.0` |
| Compatible patch | `~=1.4.2` | `>=1.4.2,<1.5` |
| Minimum bound | `>=1.4` | 1.4 or newer |
| Exact | `==1.4.2` | Only this version |
| Range | `>=1.4,<2` | Between 1.4 and 2.0 |
| Wildcard | `==1.4.*` | Any 1.4.x release |

Configure default bounds with `tool.uv.add-bounds`:

```toml
[tool.uv]
# Default: "lower" adds >=X.Y.Z
# Options: "lower", "exact", "range"
add-bounds = "lower"
```

### Development Dependencies

```bash
# Add to default "dev" group
uv add --dev pytest ruff mypy

# Add to custom group
uv add --group lint ruff
uv add --group test pytest pytest-cov
uv add --group docs mkdocs sphinx
```

Development dependencies use PEP 735 `[dependency-groups]`:

```toml
[dependency-groups]
dev = [
    "pytest>=8",
    "ruff>=0.8",
]
lint = ["ruff>=0.8"]
test = ["pytest>=8", "pytest-cov>=5"]
```

### Nesting Groups

Include one group inside another to avoid duplication:

```toml
[dependency-groups]
dev = [
    {include-group = "lint"},
    {include-group = "test"},
]
lint = ["ruff>=0.8"]
test = ["pytest>=8"]
```

### Default Groups

Control which groups sync by default:

```toml
[tool.uv]
default-groups = ["dev", "lint"]
# Or include all groups:
# default-groups = "all"
```

Toggle at runtime:
- `uv sync --no-default-groups` -- exclude all default groups
- `uv sync --no-group lint` -- exclude specific group
- `uv sync --all-groups` -- include all groups

## Removing Dependencies

```bash
# Remove from project.dependencies
uv remove httpx

# Remove from dev group
uv remove --dev ruff

# Remove from custom group
uv remove --group lint ruff
```

If a source is defined in `[tool.uv.sources]` for the removed dependency and no other references exist, the source is also removed.

## Dependency Sources

The `[tool.uv.sources]` table provides alternative sources during development. These are uv-specific and not included when publishing.

### Git Sources

```bash
# From HTTPS
uv add git+https://github.com/encode/httpx

# Specific tag
uv add git+https://github.com/encode/httpx --tag 0.27.0

# Specific branch
uv add git+https://github.com/encode/httpx --branch main

# Specific commit
uv add git+https://github.com/encode/httpx --rev abc123

# Subdirectory within repo
uv add "git+https://github.com/org/monorepo#subdirectory=libs/mylib"
```

### Local Path Sources

```bash
# Local directory (builds as package)
uv add ../my-lib

# Editable install (changes reflected immediately)
uv add --editable ../my-lib

# Local wheel file
uv add ./dist/my_lib-0.1.0-py3-none-any.whl
```

### Index Sources

Pin a package to a specific index:

```bash
uv add torch --index pytorch=https://download.pytorch.org/whl/cpu
```

```toml
[tool.uv.sources]
torch = { index = "pytorch" }

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true  # Only use for packages that reference it
```

### Platform-Specific Sources

Apply different sources per platform:

```toml
[tool.uv.sources]
torch = [
    { index = "torch-cpu", marker = "platform_system == 'Darwin'" },
    { index = "torch-gpu", marker = "platform_system == 'Linux'" },
]
```

### Workspace Member Sources

```toml
[tool.uv.sources]
my-lib = { workspace = true }
```

Workspace members are always editable. See `references/workspaces.md`.

## Optional Dependencies (Extras)

Define published extras for optional features:

```toml
[project.optional-dependencies]
viz = ["matplotlib>=3.9", "seaborn>=0.13"]
excel = ["openpyxl>=3.1", "xlrd>=2.0"]
all = ["my-project[viz,excel]"]
```

```bash
# Add optional dependency
uv add --optional viz matplotlib

# Install with extras
uv sync --extra viz
uv sync --all-extras
```

## Platform-Specific Dependencies

Use PEP 508 environment markers:

```bash
# Linux only
uv add "jax; sys_platform == 'linux'"

# Python version constraint
uv add "importlib-metadata>=7; python_version < '3.10'"

# Windows only
uv add "colorama>=0.4; platform_system == 'Windows'"
```

## Syncing and Running

### uv sync

Sync the environment to match the lockfile:

```bash
uv sync                    # Sync with default groups
uv sync --locked           # Fail if lockfile is out of date
uv sync --frozen           # Use lockfile as-is, no update check
uv sync --no-dev           # Skip dev dependencies
uv sync --all-extras       # Include all optional extras
uv sync --extra viz        # Include specific extra
```

### uv run

Run commands in the project environment:

```bash
uv run python main.py      # Run Python script
uv run pytest              # Run installed tool
uv run --with httpie -- http GET https://api.example.com  # One-off dep
uv run --python 3.11 pytest  # Use specific Python version
```

`uv run` automatically verifies the lockfile and syncs before execution -- the environment is always consistent.

## Upgrading Dependencies

```bash
# Upgrade all packages to latest compatible versions
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package httpx

# Re-add with new constraint
uv add "httpx>=0.28" --upgrade-package httpx
```

## Project Management Review Questions

1. Is this a project dependency, dev dependency, optional extra, or one-off tool?
2. Is the team using the project interface consistently, or mixing in `uv pip` habits?
3. Does the lockfile and sync workflow reflect how the repo actually ships code?

## uv Project Smells

| Smell | Why it matters |
|------|----------------|
| mixing `uv add` and ad hoc pip installs in project envs | environment drift |
| lockfile omitted from version control | weak reproducibility |
| dependency groups used inconsistently across team and CI | setup confusion |
