# Lockfile and Resolution

Sources: Astral uv documentation (docs.astral.sh/uv), PEP 751 (pylock.toml), PEP 508 (dependency specifiers), Python Packaging User Guide (packaging.python.org)

Covers: uv.lock format and purpose, universal resolution, upgrade strategies, conflict handling, resolution overrides, environment markers, and the PEP 751 pylock.toml export format.

## The uv.lock File

`uv.lock` is uv's cross-platform lockfile. It captures the exact resolved versions of every dependency for all supported platforms, Python versions, and architectures in a single file.

### Key Properties

| Property | Description |
|----------|-------------|
| Universal | Resolves for all platforms at once (Linux, macOS, Windows, etc.) |
| Human-readable | TOML format, readable but managed by uv |
| Deterministic | Same inputs always produce same resolution |
| Self-contained | Includes hashes, sources, markers for every package |
| uv-specific | Not compatible with pip or other tools directly |

### When the Lockfile Updates

| Action | Lockfile Behavior |
|--------|-------------------|
| `uv add` | Re-resolves and updates |
| `uv remove` | Re-resolves and updates |
| `uv lock` | Explicitly re-resolves |
| `uv lock --upgrade` | Upgrades all within constraints |
| `uv sync` | Validates, updates if needed |
| `uv run` | Validates, updates if needed |

### Lockfile Flags

| Flag | Meaning |
|------|---------|
| `--locked` | Fail if lockfile is out of date with pyproject.toml |
| `--frozen` | Use lockfile as-is, skip all validation |

Use `--locked` in CI to catch unintentional dependency changes. Use `--frozen` when not all workspace members are available (e.g., Docker intermediate layers).

## Universal Resolution

Traditional pip resolves for the current platform only. uv resolves universally by default -- it considers all possible platform/Python combinations and produces a single lockfile that works everywhere.

### How It Works

uv evaluates all environment markers during resolution:

```
# A package might only be needed on Windows
colorama==0.4.6 ; sys_platform == 'win32'

# Another only on Python < 3.10
importlib-metadata==7.1.0 ; python_version < '3.10'
```

The lockfile includes both, with appropriate markers, so developers on any platform get correct dependencies.

### Limiting Resolution Environments

Narrow resolution to specific platforms when universal is too broad:

```toml
[tool.uv]
environments = [
    "sys_platform == 'linux'",
    "sys_platform == 'darwin'",
]
```

This reduces lockfile size and avoids resolving Windows-only dependencies when deploying to Linux/macOS only.

## Upgrading Dependencies

### Upgrade All

```bash
# Upgrade everything to latest compatible versions
uv lock --upgrade
```

This re-resolves all packages from scratch, finding the newest versions that satisfy constraints in `pyproject.toml`.

### Upgrade Specific Package

```bash
# Upgrade just one package (and its affected dependents)
uv lock --upgrade-package httpx

# Upgrade multiple specific packages
uv lock --upgrade-package httpx --upgrade-package anyio
```

### Pin to Specific Version

```bash
# Change constraint and upgrade
uv add "httpx==0.28.0"
```

### Upgrade Strategy Comparison

| Strategy | Command | When to Use |
|----------|---------|-------------|
| Upgrade all | `uv lock --upgrade` | Regular dependency updates |
| Upgrade one | `uv lock --upgrade-package X` | Targeted security patch |
| Re-add with constraint | `uv add "X>=0.28"` | Change version bounds |
| Fresh resolve | Delete `uv.lock` + `uv lock` | Nuclear option, rarely needed |

## Conflict Resolution

### Conflicting Dependency Groups

If two dependency groups require incompatible versions of the same package, declare them as conflicting:

```toml
[tool.uv]
conflicts = [
    [
        { group = "test-old" },
        { group = "test-new" },
    ],
]
```

### Conflicting Extras

Similarly for optional dependency extras:

```toml
[tool.uv]
conflicts = [
    [
        { extra = "cpu" },
        { extra = "gpu" },
    ],
]
```

When groups or extras are declared as conflicting, uv resolves them independently -- they do not need to be compatible with each other.

## Resolution Overrides

Force specific versions or override resolution behavior when upstream metadata is incorrect or incompatible:

### Override Version

```toml
[tool.uv]
override-dependencies = [
    "grpcio==1.60.0",
]
```

This forces `grpcio` to version 1.60.0 regardless of what other packages request.

### Constraint Dependencies

Add global constraints without adding direct dependencies:

```toml
[tool.uv]
constraint-dependencies = [
    "numpy<2",
]
```

Constraints narrow valid versions but do not add the package to the project. Useful for preventing incompatible transitive dependency versions.

## Resolution Settings

### Resolution Strategy

```toml
[tool.uv]
resolution = "lowest-direct"
```

| Strategy | Behavior |
|----------|----------|
| `highest` (default) | Prefer newest compatible version |
| `lowest` | Prefer oldest compatible version |
| `lowest-direct` | Lowest for direct deps, highest for transitive |

`lowest-direct` is useful for testing minimum supported versions of direct dependencies.

### Exclude Newer

Limit resolution to packages published before a date:

```toml
[tool.uv]
exclude-newer = "2024-06-01T00:00:00Z"
```

Useful for reproducible builds and investigating regressions.

### Pre-release Handling

```toml
[tool.uv]
prerelease = "if-necessary-or-explicit"
```

| Mode | Behavior |
|------|----------|
| `disallow` | Never use pre-releases |
| `allow` | Always allow pre-releases |
| `if-necessary` | Only if no stable version satisfies |
| `if-necessary-or-explicit` (default) | Pre-releases for explicitly requested packages |

## Exporting the Lockfile

Export `uv.lock` to formats other tools can consume:

### Export to requirements.txt

```bash
# Standard requirements format
uv export --format requirements-txt -o requirements.txt

# Include hashes for verification
uv export --format requirements-txt --hashes -o requirements.txt

# Only production deps (no dev)
uv export --format requirements-txt --no-dev -o requirements.txt

# Specific extras
uv export --format requirements-txt --extra viz -o requirements.txt
```

### Export to pylock.toml (PEP 751)

```bash
uv export -o pylock.toml
```

The `pylock.toml` format is a standardized resolution output intended to eventually replace `requirements.txt`. It supports:
- Package hashes
- Source URLs
- Environment markers
- Tool-agnostic consumption

### Generate from pip Interface

```bash
# Compile requirements.in to pylock.toml
uv pip compile requirements.in -o pylock.toml

# Install from pylock.toml
uv pip sync pylock.toml
uv pip install -r pylock.toml
```

## Dependency Tree

Visualize the dependency graph:

```bash
# Full dependency tree
uv tree

# Show specific package
uv tree --package httpx

# Inverted tree (who depends on X)
uv tree --invert --package anyio

# Show depth limit
uv tree --depth 2
```

## Lockfile Best Practices

| Practice | Rationale |
|----------|-----------|
| Always commit `uv.lock` | Reproducible installs across machines |
| Use `--locked` in CI | Catch unintentional dependency drift |
| Run `uv lock --upgrade` periodically | Stay current with security patches |
| Review lockfile changes in PRs | Dependency changes deserve review |
| Use `uv tree --invert` to audit | Understand why a package is included |
| Set `exclude-newer` for reproducibility | Avoid surprise breakage from new releases |
| Export to `requirements.txt` for non-uv tools | Maintain compatibility when needed |
