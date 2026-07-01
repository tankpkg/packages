# Docker Integration

Sources: Astral uv documentation (docs.astral.sh/uv), Docker documentation (docs.docker.com), astral-sh/uv-docker-example repository

Covers: official Docker images, installing uv in containers, multi-stage builds, intermediate layers for caching, cache mount optimization, workspace Docker patterns, compose watch for development, and production best practices.

## Official Docker Images

### Distroless Images (for COPY --from)

Contain only uv binaries. Use to copy uv into your own base image:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

Pin to specific version:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
```

Pin to SHA256 for reproducible builds:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv@sha256:abc123... /uv /uvx /bin/
```

### Derived Images (ready-to-use)

Pre-built images with uv installed on popular base images:

| Base | Image Tag |
|------|-----------|
| Alpine 3.23 | `ghcr.io/astral-sh/uv:alpine` |
| Debian Trixie | `ghcr.io/astral-sh/uv:debian` |
| Debian Slim | `ghcr.io/astral-sh/uv:debian-slim` |
| Python 3.12 Slim | `ghcr.io/astral-sh/uv:python3.12-trixie-slim` |
| Python 3.12 Alpine | `ghcr.io/astral-sh/uv:python3.12-alpine` |

All derived images also have versioned variants: `ghcr.io/astral-sh/uv:0.11.3-alpine`.

## Installing uv in Docker

### Method 1: COPY from Distroless (Recommended)

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
```

Fast, no additional dependencies needed.

### Method 2: Installer Script

```dockerfile
FROM python:3.12-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/0.11.3/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
```

Requires curl. Useful when COPY --from is not available.

### Method 3: Temporary Mount

Use uv only during build without keeping it in the final image:

```dockerfile
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync
```

## Basic Project Dockerfile

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

WORKDIR /app
COPY . /app

ENV UV_NO_DEV=1
RUN uv sync --locked

CMD ["uv", "run", "my_app"]
```

Add `.venv` to `.dockerignore` -- the local virtual environment is platform-specific and must be recreated in the container.

## Intermediate Layers (Optimized Caching)

Separate dependency installation from source code to leverage Docker layer caching. Dependencies change rarely; source code changes frequently.

### Standard Project

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

WORKDIR /app

# Layer 1: Install dependencies only (cached until pyproject.toml/uv.lock change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Layer 2: Copy source and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
```

`--no-install-project` installs all dependencies but skips the project itself. The pyproject.toml is mounted (not copied) because only the metadata is needed -- source files are not yet available.

### Workspace Project

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

WORKDIR /app

# Layer 1: Install third-party deps (no workspace members)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --no-dev

# Layer 2: Copy everything and sync
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
```

Use `--frozen` (not `--locked`) in the first layer because workspace member `pyproject.toml` files are not yet available. The second sync uses `--locked` to validate the full lockfile.

## Multi-Stage Builds

Use non-editable install to copy only the virtual environment to the final image (no source code needed):

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Stage 2: Runtime (no uv, no source code)
FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
CMD ["/app/.venv/bin/my_app"]
```

`--no-editable` installs the project as a regular package (not linked to source), so only the `.venv` is needed at runtime.

## Cache Optimization

### Cache Mount

```dockerfile
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
```

`UV_LINK_MODE=copy` prevents warnings about cross-filesystem linking between cache mount and build layer.

### Python Cache

Cache managed Python installations separately:

```dockerfile
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python

RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install
```

### No Cache (Smaller Images)

When cache persistence is not needed:

```dockerfile
RUN uv sync --no-cache
# Or globally:
ENV UV_NO_CACHE=1
```

## Bytecode Compilation

Compile Python files to bytecode for faster startup in production:

```dockerfile
ENV UV_COMPILE_BYTECODE=1
RUN uv sync
```

Trade-off: larger image size and slower install, but faster application startup.

## Using the Environment

### Option 1: PATH Activation

```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
CMD ["my_app"]
```

### Option 2: uv run

```dockerfile
CMD ["uv", "run", "my_app"]
```

### Option 3: System Environment

Install directly into the system Python (avoids virtual environment entirely):

```dockerfile
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync
CMD ["my_app"]
```

## pip Interface in Docker

For migration or simpler scenarios:

```dockerfile
ENV UV_SYSTEM_PYTHON=1

COPY requirements.txt .
RUN uv pip install -r requirements.txt

# Or create a virtual environment
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install -r requirements.txt
```

## Development with Docker Compose

### Compose Watch

Auto-sync source changes without rebuilding:

```yaml
# compose.yaml
services:
  app:
    build: .
    develop:
      watch:
        - action: sync
          path: .
          target: /app
          ignore:
            - .venv/
        - action: rebuild
          path: ./pyproject.toml
```

```bash
docker compose watch
```

### Bind Mount with Volume Override

Keep the container's `.venv` isolated from local:

```bash
docker run --rm \
    --volume .:/app \
    --volume /app/.venv \
    my-image
```

The anonymous volume (`/app/.venv`) prevents the local `.venv` from overriding the container's platform-specific environment.

## Production Checklist

| Item | Setting |
|------|---------|
| Pin uv version | `ghcr.io/astral-sh/uv:0.11.3` |
| Use `--locked` | Fail if lockfile stale |
| Exclude dev deps | `UV_NO_DEV=1` or `--no-dev` |
| Compile bytecode | `UV_COMPILE_BYTECODE=1` |
| Use cache mount | `--mount=type=cache,target=/root/.cache/uv` |
| Set link mode | `UV_LINK_MODE=copy` |
| Add .venv to .dockerignore | Prevent local env in image |
| Use intermediate layers | Separate deps from source |
| Multi-stage for minimal image | Copy only `.venv` to runtime |
