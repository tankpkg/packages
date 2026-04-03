# Workspaces

Sources: Astral uv documentation (docs.astral.sh/uv), Cargo workspace design (doc.rust-lang.org/cargo), Python Packaging User Guide (packaging.python.org)

Covers: workspace setup and configuration, member management, shared lockfile, workspace sources, layout patterns, when to use workspaces vs path dependencies, and workspace limitations.

## Workspace Concept

A workspace is a collection of Python packages managed together in a single repository with a shared lockfile. Inspired by Cargo workspaces in Rust.

### Key Properties

| Property | Description |
|----------|-------------|
| Single lockfile | All members share one `uv.lock` |
| Shared resolution | Dependencies resolved together for consistency |
| Cross-member deps | Members reference each other as editable |
| Single `requires-python` | Intersection of all members' constraints |
| Root required | One project acts as workspace root |

## Setting Up a Workspace

### Create the Root

Add `[tool.uv.workspace]` to the root `pyproject.toml`:

```toml
[project]
name = "my-monorepo"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["shared-lib", "tqdm>=4,<5"]

[tool.uv.sources]
shared-lib = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]
```

### Add Members

```bash
# Auto-creates member and adds to workspace
cd packages
uv init my-lib --lib

# Or init inside workspace root (auto-detected)
uv init packages/my-service
```

Each member has its own `pyproject.toml`:

```toml
# packages/shared-lib/pyproject.toml
[project]
name = "shared-lib"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Member Globs

| Pattern | Matches |
|---------|---------|
| `packages/*` | Direct children of packages/ |
| `packages/**` | All descendants of packages/ |
| `libs/*` | Direct children of libs/ |
| `*` | Direct children of workspace root |

Every matched directory must contain a `pyproject.toml`.

## Workspace Layout

### Common Layout

```
my-monorepo/
  pyproject.toml          # Workspace root
  uv.lock                 # Shared lockfile
  packages/
    shared-lib/
      pyproject.toml
      src/
        shared_lib/
          __init__.py
    api-service/
      pyproject.toml
      src/
        api_service/
          __init__.py
    cli-tool/
      pyproject.toml
      src/
        cli_tool/
          __init__.py
```

### Virtual Root Pattern

The root project can be a non-package "virtual" root that exists solely to define the workspace:

```toml
# Root pyproject.toml
[project]
name = "my-workspace"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv]
package = false  # Not a real package

[tool.uv.workspace]
members = ["packages/*"]
```

Set `package = false` on the root to skip building it.

## Workspace Sources

### Declaring Member Dependencies

Reference workspace members using `{ workspace = true }` in sources:

```toml
# packages/api-service/pyproject.toml
[project]
name = "api-service"
version = "0.1.0"
dependencies = ["shared-lib"]

[tool.uv.sources]
shared-lib = { workspace = true }
```

Workspace member dependencies are always editable -- changes to `shared-lib` source code are reflected immediately without reinstalling.

### Root-Level Source Inheritance

Sources defined in the workspace root apply to ALL members unless overridden:

```toml
# Root pyproject.toml
[tool.uv.sources]
tqdm = { git = "https://github.com/tqdm/tqdm" }
```

Every member inherits this source. A member can override:

```toml
# packages/my-service/pyproject.toml
[tool.uv.sources]
tqdm = { index = "internal" }  # Override root source
```

When a member provides its own source for a dependency, the root's source for that dependency is completely ignored for that member, even if the member's source has a platform marker that does not match.

## Workspace Commands

### Scoped Operations

```bash
# Lock the entire workspace
uv lock

# Sync the workspace root
uv sync

# Sync a specific member
uv sync --package api-service

# Run in workspace root
uv run pytest

# Run in specific member
uv run --package api-service pytest

# Run from any directory
cd packages/shared-lib
uv run --package api-service python -m api_service
```

### Adding Dependencies

```bash
# Add to workspace root
uv add httpx

# Add to specific member
uv add --package api-service fastapi

# Add workspace member as dependency
uv add --package api-service shared-lib
```

## Virtual Workspace Members

A workspace member with `package = false` is "virtual" -- its dependencies are installed but the member itself is not built or installed:

```toml
# packages/config/pyproject.toml
[project]
name = "config"
version = "0.1.0"
dependencies = ["pyyaml>=6"]

[tool.uv]
package = false
```

Virtual members are useful for:
- Configuration packages that only aggregate dependencies
- Root projects that orchestrate but are not installable
- Non-distributable internal modules

## When to Use Workspaces

### Good Fit

| Scenario | Why |
|----------|-----|
| Shared library + multiple services | Common deps, consistent versions |
| Library + CLI wrapper | Shared lockfile, unified testing |
| Library + plugin system | Plugins depend on core, tested together |
| Extension module (Rust/C++) + Python | Build systems differ, shared env |

### Bad Fit

| Scenario | Use Instead |
|----------|-------------|
| Members need conflicting dep versions | Path dependencies (`[tool.uv.sources]`) |
| Members need separate virtual envs | Independent projects with path deps |
| Members target different Python versions | Separate projects |
| Loosely coupled packages | Independent repos |

### Path Dependencies Alternative

For packages that need independent resolution:

```toml
# Instead of workspace
[project]
dependencies = ["bird-feeder"]

[tool.uv.sources]
bird-feeder = { path = "packages/bird-feeder" }
```

This gives each package its own lockfile and virtual environment, but loses `uv run --package` convenience.

## Workspace Limitations

| Limitation | Detail |
|------------|--------|
| Single `requires-python` | Intersection of all members, cannot vary |
| No dependency isolation | Python cannot enforce import boundaries between members |
| Shared lockfile only | Cannot have per-member lockfiles |
| All members must resolve together | Conflicting deps require `conflicts` config or path deps |

### Handling requires-python Mismatch

If a dev group needs a different Python version:

```toml
[tool.uv.dependency-groups]
dev = { requires-python = ">=3.12" }
```

For members that cannot share `requires-python` at all, use separate projects with path dependencies instead.

## Docker with Workspaces

Use `--no-install-workspace` for intermediate layer optimization:

```dockerfile
# Install all third-party deps (workspace members excluded)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace

# Copy full source
COPY . /app

# Install workspace members
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```

Use `--frozen` for the first sync because not all member `pyproject.toml` files are available yet to validate the lockfile. The second sync uses `--locked` to validate everything.

See `references/docker-integration.md` for complete Docker patterns.
