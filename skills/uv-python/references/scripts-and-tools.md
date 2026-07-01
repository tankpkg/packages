# Scripts and Tools

Sources: Astral uv documentation (docs.astral.sh/uv), PEP 723 (inline script metadata), Python Packaging User Guide (packaging.python.org)

Covers: running scripts with uv run, inline dependency metadata for single-file scripts, tool management with uvx and uv tool install, shebangs for executable scripts, and script locking.

## Running Scripts

### Basic Script Execution

```bash
# Run a Python file
uv run example.py

# Pass arguments
uv run example.py --flag value

# Read from stdin
echo 'print("hello")' | uv run -

# Here-document
uv run - <<EOF
print("hello from heredoc")
EOF
```

### Script in a Project Context

When run inside a project directory, `uv run` installs the current project before running. Skip this for standalone scripts:

```bash
# Skip project installation (flag must come before script name)
uv run --no-project example.py
```

### Ad-hoc Dependencies

Request packages for a single run without modifying any config:

```bash
# Single dependency
uv run --with rich example.py

# Multiple dependencies
uv run --with rich --with httpx example.py

# With version constraints
uv run --with "rich>=13,<14" example.py

# Combined with project exclusion
uv run --no-project --with pandas example.py
```

### Using a Specific Python Version

```bash
# Override Python version for this run
uv run --python 3.11 example.py

# Use PyPy
uv run --python pypy@3.10 example.py
```

## Inline Script Metadata (PEP 723)

PEP 723 defines a standard for declaring dependencies directly in script files. uv fully supports this format, enabling self-contained scripts that declare their own requirements.

### Creating a Script with Metadata

```bash
# Initialize a script with metadata block
uv init --script example.py --python 3.12

# Add dependencies to existing script
uv add --script example.py requests rich
```

### Metadata Format

The metadata block uses TOML embedded in a Python comment:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.31",
#     "rich>=13",
# ]
# ///

import requests
from rich.pretty import pprint

resp = requests.get("https://api.github.com/repos/astral-sh/uv")
pprint(resp.json()["stargazers_count"])
```

### Metadata Fields

| Field | Required | Description |
|-------|----------|-------------|
| `dependencies` | Yes (even if empty) | List of PEP 508 dependency strings |
| `requires-python` | No | Python version constraint |
| `[tool.uv]` | No | uv-specific settings |
| `[[tool.uv.index]]` | No | Custom package indexes |

### Empty Dependencies

The `dependencies` field must always be present, even if empty:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

type Point = tuple[float, float]
print(Point)
```

### Adding Custom Indexes to Scripts

```bash
uv add --index "https://example.com/simple" --script example.py requests
```

Produces:

```python
# /// script
# dependencies = [
#     "requests",
# ]
# [[tool.uv.index]]
# url = "https://example.com/simple"
# ///
```

### Reproducibility with exclude-newer

Lock resolution to a point in time:

```python
# /// script
# dependencies = [
#     "requests",
# ]
# [tool.uv]
# exclude-newer = "2024-06-01T00:00:00Z"
# ///
```

### Behavior with Inline Metadata

When a script has inline metadata:
- Project dependencies are **ignored** (even inside a project directory)
- The `--no-project` flag is not needed
- uv creates an isolated, ephemeral environment for the script
- The environment is cached and reused when dependencies have not changed

## Script Locking

Lock a script's dependencies for fully reproducible execution:

```bash
# Create a lockfile for the script
uv lock --script example.py
```

This creates `example.py.lock` adjacent to the script. Once locked:
- `uv run example.py` uses the locked versions
- `uv add --script` updates the lockfile
- `uv export --script example.py` exports locked versions

## Executable Scripts with Shebangs

Make scripts directly executable on Unix systems:

```python
#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

import httpx
print(httpx.get("https://example.com").status_code)
```

```bash
chmod +x my-script
./my-script
```

The `#!/usr/bin/env -S uv run --script` shebang ensures uv manages the execution environment automatically.

## GUI Scripts (Windows)

Use `.pyw` extension for windowed Python applications:

```python
# example.pyw
from tkinter import Tk, ttk

root = Tk()
root.title("uv GUI")
ttk.Label(root, text="Hello World").grid()
root.mainloop()
```

```powershell
uv run example.pyw
```

uv automatically uses `pythonw` for `.pyw` files on Windows.

## Tool Management

uv replaces pipx for managing CLI tools distributed as Python packages.

### Running Tools Ephemerally (uvx)

`uvx` is an alias for `uv tool run`. It runs tools in temporary, isolated environments:

```bash
# Run a tool without installing
uvx ruff check .
uvx black --check .
uvx mypy src/

# Run with specific version
uvx ruff@0.8.0 check .

# Run from specific package (when command differs from package name)
uvx --from jupyter-core jupyter

# Include extra dependencies
uvx --with numpy ipython
```

### Installing Tools Persistently

Install tools globally so they are always available on PATH:

```bash
# Install a tool
uv tool install ruff

# Install specific version
uv tool install ruff@0.8.0

# Install with extras
uv tool install "mkdocs[material]"

# Install with additional packages in tool environment
uv tool install --with mkdocs-material mkdocs
```

### Managing Installed Tools

```bash
# List installed tools
uv tool list

# Upgrade a tool
uv tool upgrade ruff

# Upgrade all tools
uv tool upgrade --all

# Uninstall a tool
uv tool uninstall ruff

# Show tool installation directory
uv tool dir

# Show tool binary directory
uv tool dir --bin
```

### Tool Directories

| Path | Purpose |
|------|---------|
| `~/.local/share/uv/tools/` | Tool virtual environments |
| `~/.local/bin/` | Tool executables (symlinked) |

Ensure `~/.local/bin` is on your PATH for installed tools to be found.

### Tool Environment Isolation

Each installed tool gets its own virtual environment, preventing dependency conflicts between tools. For example, `ruff` and `black` can use different versions of shared dependencies without interference.

### Common Tool Patterns

| Task | Command |
|------|---------|
| Format code | `uvx black .` |
| Lint code | `uvx ruff check .` |
| Type check | `uvx mypy src/` |
| Build docs | `uvx --with mkdocs-material mkdocs build` |
| Run Jupyter | `uvx jupyter lab` |
| HTTP client | `uvx httpie GET https://api.example.com` |
| Serve files | `uvx python -m http.server 8000` |
| Benchmark | `uvx richbench benchmarks/` |

## uv run vs uvx

| Feature | `uv run` | `uvx` / `uv tool run` |
|---------|----------|----------------------|
| Environment | Project `.venv` or script ephemeral | Tool-specific ephemeral |
| Dependencies | From `pyproject.toml` or inline metadata | From tool's own requirements |
| Use case | Run project code and scripts | Run standalone CLI tools |
| Persistence | Project env persists | Environment is temporary |
| Alias | N/A | `uvx` = `uv tool run` |

Rule of thumb: Use `uv run` for project code, `uvx` for external tools.
