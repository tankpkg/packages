# Python Versions and Environments

Sources: Astral uv documentation (docs.astral.sh/uv), Python Packaging User Guide (packaging.python.org), PEP 405 (virtual environments)

Covers: Python version installation and management, version pinning, virtual environment lifecycle, environment variables, the .python-version file, and integration with system Python.

## Python Version Management

uv replaces pyenv for managing Python installations. It downloads pre-built CPython and PyPy binaries managed by the `python-build-standalone` project.

### Installing Python

```bash
# Install specific version
uv python install 3.12

# Install multiple versions
uv python install 3.10 3.11 3.12 3.13

# Install latest available
uv python install

# Install PyPy
uv python install pypy@3.10
```

Installations go to `~/.local/share/uv/python/` (Linux/macOS) or `%APPDATA%\uv\python\` (Windows). They do not interfere with system Python.

### Listing Installed Versions

```bash
# List all installed versions
uv python list

# List all available versions (including not installed)
uv python list --all-versions

# Find a specific version
uv python find 3.12
```

### Pinning Python Version

Pin the Python version for a project with `.python-version`:

```bash
# Create .python-version file
uv python pin 3.12

# Pin exact patch version
uv python pin 3.12.4
```

The `.python-version` file is plain text:

```
3.12
```

Commit this file to version control. uv, pyenv, and other tools respect it.

### Version Resolution Order

When determining which Python to use, uv checks in order:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `--python` flag | Explicit CLI argument |
| 2 | `UV_PYTHON` env var | Environment override |
| 3 | `.python-version` | Project-level pin |
| 4 | `requires-python` in `pyproject.toml` | Project constraint |
| 5 | System PATH | Discovered Python installations |

### Python Version Requests

Flexible version specification syntax:

| Request | Meaning |
|---------|---------|
| `3.12` | Latest 3.12.x |
| `3.12.4` | Exact 3.12.4 |
| `>=3.11` | 3.11 or newer |
| `cpython@3.12` | CPython specifically |
| `pypy@3.10` | PyPy specifically |
| `3.12-dev` | Development/pre-release build |

Use in any command:

```bash
uv run --python 3.11 pytest
uv venv --python 3.12
uv init --python ">=3.11"
```

### Auto-Download

uv downloads Python versions automatically when needed. Control this with:

```bash
# Disable automatic downloads
export UV_PYTHON_DOWNLOADS=never

# Allow automatic downloads (default)
export UV_PYTHON_DOWNLOADS=automatic

# Only download on explicit install
export UV_PYTHON_DOWNLOADS=manual
```

Or in `pyproject.toml`:

```toml
[tool.uv]
python-downloads = "never"
```

## Virtual Environments

### Project Environments

uv manages a `.venv` directory automatically per project. This environment:

- Lives next to `pyproject.toml`
- Is created/updated by `uv sync` and `uv run`
- Should NOT be committed to version control (auto-excluded by `.gitignore`)
- Should NOT be modified manually with `uv pip install`

```bash
# Explicitly create/sync project environment
uv sync

# Run command in project environment
uv run python -c "import sys; print(sys.prefix)"
```

### Standalone Virtual Environments

Create virtual environments outside the project workflow:

```bash
# Create with project's pinned Python
uv venv

# Create with specific Python version
uv venv --python 3.12

# Create at specific path
uv venv /path/to/myenv

# Create with specific name
uv venv .my-custom-env
```

### Activating Environments

While `uv run` is preferred, traditional activation works:

```bash
# macOS/Linux (bash/zsh)
source .venv/bin/activate

# macOS/Linux (fish)
source .venv/bin/activate.fish

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Deactivate
deactivate
```

### Project Environment Path

Override the default `.venv` location:

```toml
[tool.uv]
# Use custom path
# UV_PROJECT_ENVIRONMENT can also be set as env var
```

```bash
# Install to system Python environment (useful in Docker/CI)
export UV_PROJECT_ENVIRONMENT=/usr/local
uv sync
```

## Environment Variables

### Core Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `UV_PYTHON` | Python version to use | Auto-detected |
| `UV_PYTHON_DOWNLOADS` | Auto-download behavior | `automatic` |
| `UV_PYTHON_PREFERENCE` | Prefer managed vs system | `managed` |
| `UV_PROJECT_ENVIRONMENT` | Custom env path | `.venv` |
| `UV_SYSTEM_PYTHON` | Allow system Python in pip interface | `false` |

### Cache Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `UV_CACHE_DIR` | Cache directory location | Platform-specific |
| `UV_NO_CACHE` | Disable cache entirely | `false` |
| `UV_LINK_MODE` | How to link cached packages | `hardlink` |

### Network and Index

| Variable | Purpose | Default |
|----------|---------|---------|
| `UV_INDEX_URL` | Default package index | `https://pypi.org/simple` |
| `UV_EXTRA_INDEX_URL` | Additional indexes | None |
| `UV_NO_INDEX` | Disable all indexes | `false` |
| `UV_OFFLINE` | Run without network | `false` |

### Build and Sync

| Variable | Purpose | Default |
|----------|---------|---------|
| `UV_COMPILE_BYTECODE` | Compile .pyc on install | `false` |
| `UV_NO_DEV` | Skip dev dependencies | `false` |
| `UV_FROZEN` | No lockfile updates | `false` |
| `UV_LOCKED` | Fail if lockfile stale | `false` |

## The pip Interface

uv provides a drop-in `uv pip` interface for gradual migration:

```bash
# Install packages
uv pip install flask

# Install from requirements
uv pip install -r requirements.txt

# Compile requirements (like pip-compile)
uv pip compile requirements.in -o requirements.txt

# Universal compilation (cross-platform)
uv pip compile --universal requirements.in -o requirements.txt

# Sync environment to lockfile
uv pip sync requirements.txt

# Freeze current environment
uv pip freeze

# Show package info
uv pip show flask

# List installed packages
uv pip list

# Uninstall
uv pip uninstall flask
```

### pip Interface vs Project Interface

| Feature | `uv pip` | Project (`uv add/sync/run`) |
|---------|----------|--------------------------|
| Lockfile | `requirements.txt` | `uv.lock` |
| Metadata | `requirements.in` | `pyproject.toml` |
| Resolution | Per-platform by default | Universal by default |
| Environment | Manual venv management | Automatic `.venv` |
| Use case | Migration, legacy workflows | New projects |

Prefer the project interface for new work. The pip interface exists for migration and compatibility with existing workflows.

## Managed vs Unmanaged Projects

Disable uv's automatic environment management when integrating with tools that manage their own environments:

```toml
[tool.uv]
managed = false
```

When `managed = false`:
- `uv run` and `uv sync` skip automatic lock/sync
- Manual `uv pip` commands still work
- Useful for projects using Conda, Nix, or custom environment management

## requires-python

Set the minimum Python version for the project:

```toml
[project]
requires-python = ">=3.11"
```

This constraint:
- Determines which Python versions uv considers during resolution
- Is enforced when creating environments
- Is respected by `uv python install` (installs compatible version)
- Propagates to the lockfile for cross-version compatibility

Common patterns:

| Constraint | Meaning |
|------------|---------|
| `>=3.11` | Python 3.11 or newer (recommended) |
| `>=3.11,<4` | 3.11 through 3.x |
| `>=3.11,<3.13` | Only 3.11 and 3.12 |
| `==3.12.*` | Only 3.12.x versions |
