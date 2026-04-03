# BuildKit Optimization

Sources: Docker BuildKit documentation (2025-2026), Docker build cache reference, Dockerfile reference (mount syntax), Docker CI/CD guides, Tonis Tiigi (BuildKit maintainer) patterns

Covers: BuildKit enablement, cache mounts for package managers, build secrets, SSH forwarding, multi-platform builds, cache export/import for CI, build arguments, and BuildKit-specific Dockerfile syntax.

## Enabling BuildKit

BuildKit is the default builder in Docker Desktop and Docker Engine 23.0+. For older versions or CI environments:

```bash
# Environment variable (per-command)
DOCKER_BUILDKIT=1 docker build .

# Docker daemon configuration (permanent)
# /etc/docker/daemon.json
{
  "features": { "buildkit": true }
}

# Buildx (recommended for CI)
docker buildx create --use
docker buildx build --platform linux/amd64 -t myapp:latest .
```

### BuildKit vs Legacy Builder

| Feature | Legacy Builder | BuildKit |
|---------|---------------|----------|
| Parallel stage execution | No | Yes |
| Cache mounts | No | Yes |
| Secret mounts | No | Yes |
| SSH forwarding | No | Yes |
| Multi-platform builds | No | Yes (via buildx) |
| Build output (--output) | No | Yes |
| Cache export/import | No | Yes |
| Progress output | Plain | Auto/plain/tty |
| Garbage collection | Manual | Automatic |

## Cache Mounts

Cache mounts persist a directory across builds without baking it into image layers. Package manager caches are the primary use case — download once, reuse across builds.

### Syntax

```dockerfile
RUN --mount=type=cache,target=/path/to/cache command
```

### Package Manager Recipes

#### npm / pnpm / yarn

```dockerfile
# npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev

# pnpm
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --prod

# yarn (classic)
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn \
    yarn install --frozen-lockfile --production
```

#### Python (pip / uv)

```dockerfile
# pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements.txt

# uv (faster)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
```

#### Go

```dockerfile
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app/server ./cmd/server
```

#### Rust

```dockerfile
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo build --release
```

#### Java (Gradle / Maven)

```dockerfile
# Gradle
RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew bootJar --no-daemon

# Maven
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn package -DskipTests
```

#### apt-get

```dockerfile
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends package-name
```

### Cache Mount Options

| Option | Default | Purpose |
|--------|---------|---------|
| `target` | Required | Path to mount inside container |
| `id` | target path | Cache key — share cache across stages with same id |
| `sharing` | `shared` | `shared` (concurrent), `private` (exclusive), `locked` (serial) |
| `mode` | `0755` | Permission bits for mount directory |
| `uid`, `gid` | `0` | Owner of cache directory |
| `from` | — | Copy initial contents from a stage |

### Cache Mount vs Layer Cache

| Aspect | Layer cache | Cache mount |
|--------|------------|-------------|
| Stored in | Image layers | BuildKit cache directory |
| Persists across builds | Yes (if layer unchanged) | Yes (independent of layers) |
| Survives instruction change | No (invalidated) | Yes (mount preserved) |
| Increases image size | Yes | No (not in final image) |
| Shareable across stages | No | Yes (via `id` option) |

## Build Secrets

Secrets are sensitive values needed during build (API keys, tokens, private repo credentials). Never use `ARG` or `ENV` — they persist in image layer metadata and history.

### Secret Mount Syntax

```dockerfile
# In Dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci

RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    pip install -r requirements.txt
```

```bash
# Build command
docker build --secret id=npmrc,src=$HOME/.npmrc \
             --secret id=pip_conf,src=./pip.conf .
```

### Secret Properties

| Property | Behavior |
|----------|----------|
| Availability | Only during the RUN instruction that mounts it |
| In final image | No — not in any layer |
| In build history | No — not visible via `docker history` |
| Default mount path | `/run/secrets/<id>` |
| Custom path | Use `target=/path/to/file` |

### Common Secret Patterns

| Secret | Pattern |
|--------|---------|
| npm private registry | `--mount=type=secret,id=npmrc,target=/root/.npmrc` |
| pip private index | `--mount=type=secret,id=pip_conf,target=/etc/pip.conf` |
| Go private modules | `--mount=type=secret,id=netrc,target=/root/.netrc` |
| Git credentials | Use SSH forwarding instead (see below) |
| API keys for build | `--mount=type=secret,id=api_key` + read from `/run/secrets/api_key` |

### Why ARG/ENV Leak

```dockerfile
# WRONG: secret visible in docker history and layer metadata
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc && \
    npm ci && \
    rm .npmrc
# .npmrc removed from filesystem but NPM_TOKEN persists in layer metadata
```

Even deleting the file in the same RUN does not remove the ARG value from image history. Use `docker history --no-trunc` to verify.

## SSH Forwarding

Mount the host SSH agent socket for git clone operations during build, without copying keys into the image.

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.23 AS builder
RUN --mount=type=ssh \
    git clone git@github.com:org/private-repo.git
```

```bash
# Build with SSH agent forwarding
docker build --ssh default .
# Or with explicit key
docker build --ssh default=$HOME/.ssh/id_ed25519 .
```

The SSH socket is available only during the RUN instruction. No keys are stored in any layer.

## Multi-Platform Builds

Build images for multiple architectures from a single command using `docker buildx`.

```bash
# Create a builder with multi-platform support
docker buildx create --name multiarch --driver docker-container --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myrepo/myapp:latest \
  --push .
```

### Cross-Compilation Pattern (Go)

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.23 AS builder
ARG TARGETOS TARGETARCH
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH CGO_ENABLED=0 \
    go build -ldflags="-s -w" -o /app/server ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

`$BUILDPLATFORM` runs the build on the host architecture (fast, no emulation). `$TARGETOS` and `$TARGETARCH` cross-compile for the target platform.

### Platform Variables

| Variable | Example | Purpose |
|----------|---------|---------|
| `BUILDPLATFORM` | `linux/amd64` | Platform running the build |
| `TARGETPLATFORM` | `linux/arm64` | Platform the image targets |
| `TARGETOS` | `linux` | Target OS |
| `TARGETARCH` | `arm64` | Target architecture |
| `TARGETVARIANT` | `v8` | Architecture variant (e.g., ARM v7 vs v8) |

## Cache Export/Import for CI

Local BuildKit cache is lost between CI runs. Export cache to a registry or filesystem.

### Registry Cache

```bash
# Build and push cache to registry
docker buildx build \
  --cache-to type=registry,ref=myrepo/myapp:buildcache,mode=max \
  --cache-from type=registry,ref=myrepo/myapp:buildcache \
  -t myrepo/myapp:latest \
  --push .
```

### GitHub Actions Cache

```bash
docker buildx build \
  --cache-to type=gha,scope=main \
  --cache-from type=gha,scope=main \
  -t myapp:latest .
```

### Cache Modes

| Mode | Behavior | Size | Use when |
|------|----------|------|----------|
| `mode=min` | Cache only final stage layers | Small | Default, sufficient for most |
| `mode=max` | Cache all intermediate stages | Large | Multi-stage builds with expensive intermediate steps |

### Cache Backend Comparison

| Backend | Speed | Persistence | Setup complexity |
|---------|-------|-------------|-----------------|
| `type=local` | Fast | Local filesystem | Low |
| `type=registry` | Network-bound | Remote, shared | Medium |
| `type=gha` | CI-optimized | GitHub Actions cache | Low (GHA only) |
| `type=s3` | Network-bound | S3 bucket | Medium |
| `type=azblob` | Network-bound | Azure Blob | Medium |

## Build Arguments

Build-time variables that do not persist in the final image (unlike ENV). Use for non-sensitive configuration.

```dockerfile
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-slim

ARG BUILD_DATE
ARG GIT_SHA
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
```

```bash
docker build \
  --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --build-arg GIT_SHA=$(git rev-parse HEAD) .
```

### ARG Scope Rules

| Placement | Scope |
|-----------|-------|
| Before first FROM | Available in FROM instruction only |
| After FROM | Available in that build stage only |
| In next stage | Must redeclare ARG (value does not carry over) |

### Predefined ARGs

Docker provides several ARGs without needing `ARG` declaration: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `FTP_PROXY`, and the `BUILDPLATFORM`/`TARGETPLATFORM` family.
