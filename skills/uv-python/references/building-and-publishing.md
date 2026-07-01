# Building and Publishing

Sources: Astral uv documentation (docs.astral.sh/uv), Python Packaging User Guide (packaging.python.org), PEP 517 (build system interface), PEP 621 (project metadata), PEP 740 (attestations)

Covers: building packages with uv build, publishing to PyPI and private registries with uv publish, build system configuration, version management, trusted publishing, and attestation support.

## Build Systems

A build system is required to package a Python project for distribution. Configure it in `pyproject.toml`:

### Common Build Backends

| Backend | When to Use | Configuration |
|---------|-------------|---------------|
| `hatchling` | General purpose, default for uv | `requires = ["hatchling"]` |
| `setuptools` | Legacy projects, C extensions | `requires = ["setuptools>=42"]` |
| `flit-core` | Simple pure-Python packages | `requires = ["flit_core>=3.4"]` |
| `maturin` | Rust extensions (PyO3) | `requires = ["maturin>=1.0"]` |
| `uv_build` | uv's own build backend | `requires = ["uv_build>=0.11"]` |

### Configuration Examples

```toml
# Hatchling (recommended default)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Setuptools
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

# Flit
[build-system]
requires = ["flit_core>=3.4,<4"]
build-backend = "flit_core.buildapi"

# Maturin (for Rust extensions)
[build-system]
requires = ["maturin>=1.0,<2"]
build-backend = "maturin"

# uv_build
[build-system]
requires = ["uv_build>=0.11.3,<0.12"]
build-backend = "uv_build"
```

### Application vs Library

| Type | Build System Needed? | Publishable? |
|------|---------------------|--------------|
| Application | No (but add one if publishing) | Optional |
| Library | Yes | Yes |
| Packaged application | Yes | Yes |

If no `[build-system]` is present, `uv build` falls back to legacy setuptools. Always configure one explicitly.

## Entry Points

Define CLI commands for your package:

```toml
[project.scripts]
my-cli = "my_package:main"
my-tool = "my_package.cli:run"

[project.gui-scripts]
my-gui = "my_package.gui:start"
```

After installation, `my-cli` and `my-tool` are available as commands.

## Building Packages

### Basic Build

```bash
# Build source distribution and wheel
uv build

# Build specific format
uv build --sdist
uv build --wheel

# Build from different directory
uv build path/to/project

# Build specific workspace member
uv build --package my-lib
```

Output goes to `dist/`:

```
dist/
  my_project-0.1.0.tar.gz       # Source distribution
  my_project-0.1.0-py3-none-any.whl  # Wheel
```

### Build with Source Validation

When publishing, verify the package builds without uv-specific sources:

```bash
# Build without tool.uv.sources
uv build --no-sources
```

This ensures the package builds correctly for users who install from PyPI, where `tool.uv.sources` is not available.

### Build Dependencies

Build dependencies specified in `build-system.requires` are installed automatically. They can also have `tool.uv.sources` entries for development:

```toml
[build-system]
requires = ["setuptools>=42"]
build-backend = "setuptools.build_meta"

[tool.uv.sources]
setuptools = { path = "./packages/setuptools" }
```

## Version Management

### Reading Version

```bash
# Show current version
uv version
```

### Setting Version

```bash
# Set exact version
uv version 1.0.0

# Preview without changing
uv version 2.0.0 --dry-run
```

### Bumping Version

```bash
# Semantic version bumps
uv version --bump major    # 1.2.3 -> 2.0.0
uv version --bump minor    # 1.2.3 -> 1.3.0
uv version --bump patch    # 1.2.3 -> 1.2.4

# Pre-release versions
uv version --bump patch --bump beta     # 1.2.3 -> 1.2.4b1
uv version --bump major --bump alpha    # 1.2.3 -> 2.0.0a1
uv version --bump beta                  # 1.2.4b1 -> 1.2.4b2

# Promote to stable
uv version --bump stable                # 1.2.4b2 -> 1.2.4

# Post-release
uv version --bump post                  # 1.2.4 -> 1.2.4.post1

# Dev builds with custom number
uv version --bump patch --bump dev=66463664  # 0.0.1 -> 0.0.2.dev66463664

# Skip auto lock/sync
uv version --bump minor --frozen
```

### Bump Components

| Component | Example |
|-----------|---------|
| `major` | 1.2.3 -> 2.0.0 |
| `minor` | 1.2.3 -> 1.3.0 |
| `patch` | 1.2.3 -> 1.2.4 |
| `alpha` | 1.2.3 -> 1.2.3a1 (or needs major/minor/patch bump) |
| `beta` | 1.2.3 -> 1.2.3b1 |
| `rc` | 1.2.3 -> 1.2.3rc1 |
| `post` | 1.2.3 -> 1.2.3.post1 |
| `dev` | 1.2.3 -> 1.2.3.dev1 |
| `stable` | 1.2.3b2 -> 1.2.3 |

## Publishing Packages

### Publish to PyPI

```bash
# Publish all distributions in dist/
uv publish

# Publish specific files
uv publish dist/my_project-0.1.0-py3-none-any.whl

# With authentication
uv publish --token pypi-AgEIcH...

# Or via environment variables
UV_PUBLISH_TOKEN=pypi-AgEIcH... uv publish
```

### Authentication Methods

| Method | How | When |
|--------|-----|------|
| Trusted publishing | No credentials needed | GitHub Actions, GitLab CI |
| API token | `--token` or `UV_PUBLISH_TOKEN` | Manual publishing |
| Username/password | `--username` + `--password` | Legacy (PyPI deprecated this) |

### Publish to Custom Index

Configure a publish URL for your index:

```toml
[[tool.uv.index]]
name = "internal"
url = "https://internal.example.com/simple/"
publish-url = "https://internal.example.com/upload/"
explicit = true
```

```bash
uv publish --index internal
```

### Publish to TestPyPI

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

```bash
uv publish --index testpypi --token pypi-AgEIcH...
```

### Error Recovery

If publishing fails mid-upload (some files uploaded, some not):
- **PyPI**: Retry the same `uv publish` command. Identical existing files are skipped.
- **Other registries**: Use `--check-url <index-url>` to skip already-uploaded files.

```bash
uv publish --check-url https://pypi.org/simple/
```

## Attestations (PEP 740)

uv supports uploading attestation files alongside distributions. Attestations provide cryptographic proof of provenance.

### Attestation Discovery

Place `.publish.attestation` files next to distributions:

```
dist/
  my_project-0.1.0-py3-none-any.whl
  my_project-0.1.0-py3-none-any.whl.publish.attestation
  my_project-0.1.0.tar.gz
  my_project-0.1.0.tar.gz.publish.attestation
```

`uv publish` automatically discovers and uploads attestations.

### Disable Attestations

Some registries do not support attestations and may reject uploads:

```bash
uv publish --no-attestations
```

## Smoke Testing Published Packages

Verify the published package works before announcing:

```bash
# Test wheel
uv run --isolated --no-project --with dist/*.whl -- python -c "import my_project"

# Test source distribution
uv run --isolated --no-project --with dist/*.tar.gz -- python -c "import my_project"

# Test from registry (after publishing)
uv run --isolated --no-project --with my-project --refresh-package my-project -- python -c "import my_project"
```

Use `--refresh-package` to bypass cache when testing a newly published version.

## Complete Publishing Workflow

```bash
# 1. Bump version
uv version --bump minor

# 2. Build
uv build --no-sources

# 3. Smoke test locally
uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py

# 4. Publish
uv publish

# 5. Verify from registry
uv run --isolated --no-project --with my-project --refresh-package my-project -- python -c "import my_project; print(my_project.__version__)"
```
