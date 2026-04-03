# Dockerfile Patterns

Sources: Docker official documentation (Dockerfile reference, 2025-2026), Docker Best Practices guide, OCI Image Specification, NodeSource production patterns, Google distroless project

Covers: multi-stage build architecture, layer ordering for cache efficiency, ENTRYPOINT vs CMD selection, base image decision framework, .dockerignore patterns, and production Dockerfiles for Node.js, Python, Go, Rust, and Java.

## Multi-Stage Build Architecture

Multi-stage builds separate build-time dependencies from runtime. The final image contains only production artifacts.

### Structure

```dockerfile
# Stage 1: Build
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:22-slim AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Key Principles

| Principle | Why |
|-----------|-----|
| Name every stage (`AS builder`) | Enables targeted builds: `docker build --target builder` |
| Copy only artifacts to final stage | Build tools, source code, devDependencies stay in builder |
| Use the same base for build and run | Avoids glibc/musl compatibility issues |
| Minimize final stage instructions | Each instruction adds metadata; keep it lean |

### Advanced: Three-Stage Pattern

For languages with separate dependency and compilation steps:

```dockerfile
# Stage 1: Dependencies
FROM golang:1.23 AS deps
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

# Stage 2: Build
FROM deps AS builder
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

# Stage 3: Runtime
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

Separating dependency download from compilation maximizes cache reuse — source code changes do not re-download dependencies.

## Layer Ordering

Docker caches layers. When a layer changes, all subsequent layers are invalidated. Order instructions from least-changing to most-changing.

### Optimal Order

```dockerfile
FROM base:tag                    # 1. Base image (changes rarely)
RUN apt-get update && \          # 2. System dependencies (changes rarely)
    apt-get install -y --no-install-recommends pkg && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app                     # 3. Working directory
COPY package.json package-lock.json ./  # 4. Dependency manifests (changes sometimes)
RUN npm ci --omit=dev            # 5. Install dependencies (cached if lockfile unchanged)
COPY . .                         # 6. Application source (changes frequently)
RUN npm run build                # 7. Build step
```

### Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| `COPY . .` before dependency install | Every code change reinstalls all deps | Copy lockfile first, install, then copy source |
| Separate `RUN apt-get update` and `RUN apt-get install` | Stale package index cached | Combine in one RUN with `&&` |
| Not cleaning package manager caches | Bloated layers | `rm -rf /var/lib/apt/lists/*` in same RUN |
| Installing dev dependencies in final image | Larger image, more vulnerabilities | Use `--omit=dev` (npm) or virtual packages (apk) |

## ENTRYPOINT vs CMD

| Instruction | Purpose | Override behavior |
|-------------|---------|-------------------|
| `ENTRYPOINT` | The executable — what the container runs | Requires `--entrypoint` to override |
| `CMD` | Default arguments to ENTRYPOINT (or default command if no ENTRYPOINT) | Overridden by any `docker run` arguments |

### Forms

| Form | Syntax | PID 1 | Signal handling |
|------|--------|-------|-----------------|
| Exec form (preferred) | `["node", "server.js"]` | node is PID 1 | Receives SIGTERM directly |
| Shell form (avoid) | `node server.js` | /bin/sh is PID 1 | Shell swallows signals |

Always use exec form for production. Shell form wraps the command in `/bin/sh -c`, which does not forward signals to the child process. See `references/lifecycle-signals.md`.

### Combined Pattern

```dockerfile
ENTRYPOINT ["node"]
CMD ["dist/server.js"]
```

`docker run myapp` executes `node dist/server.js`. `docker run myapp dist/worker.js` executes `node dist/worker.js`.

Use this pattern when the executable is fixed but the entrypoint script may vary.

## Base Image Selection

### Decision Matrix

| Base | Size | Shell | Package Manager | Security | Use When |
|------|------|-------|-----------------|----------|----------|
| `scratch` | 0 MB | No | No | Minimal attack surface | Static Go/Rust binaries |
| Distroless (`gcr.io/distroless/...`) | 2-20 MB | No | No | Very low attack surface | Languages with runtimes (Node, Python, Java) |
| `*-alpine` | 5-50 MB | Yes (ash) | apk | Small but watch musl DNS | When shell needed + small size |
| `*-slim` | 50-100 MB | Yes (bash) | apt | Moderate, glibc compatible | Default for most production use |
| Default (e.g., `node:22`) | 300-900 MB | Yes | apt | Large attack surface | Development only |
| Chainguard | 5-30 MB | Configurable | apk (dev variant) | Hardened, SBOM included | Enterprise compliance |

### Alpine Gotchas

- musl libc DNS resolution differs from glibc — may cause issues with `search` domains in `/etc/resolv.conf`
- Some native modules (node-gyp, Python C extensions) require recompilation for musl
- Thread stack size defaults differ — can cause segfaults in memory-intensive apps
- If hitting musl issues, switch to `*-slim` (Debian-based, glibc)

### Pin Image Versions

```dockerfile
# Bad: floating tag, unpredictable
FROM node:latest

# Better: major.minor version
FROM node:22-slim

# Best: digest pin for reproducibility
FROM node:22-slim@sha256:abc123...
```

Pin to a specific version for reproducible builds. Use digest pinning in CI/CD for guaranteed immutability. Use Renovate or Dependabot to automate base image updates.

## .dockerignore

The build context is everything sent to the Docker daemon. Exclude files that are not needed in the build.

### Production .dockerignore

```
# Version control
.git
.gitignore

# Dependencies (reinstalled in container)
node_modules
__pycache__
.venv
vendor/

# Build output (rebuilt in container)
dist
build
target

# IDE and editor
.vscode
.idea
*.swp
*.swo

# Environment and secrets
.env
.env.*
*.pem
*.key

# Testing
coverage
*.test.js
*.spec.ts
__tests__
tests

# Documentation
*.md
docs
LICENSE

# Docker files (avoid recursion)
Dockerfile*
docker-compose*
.dockerignore

# OS files
.DS_Store
Thumbs.db
```

### Impact

| Scenario | Build context | Effect |
|----------|--------------|--------|
| No .dockerignore, large repo | 500 MB+ sent to daemon | Slow build start, secrets leak risk |
| Proper .dockerignore | 5-50 MB sent | Fast context transfer, clean builds |
| Missing `.git` exclusion | 100+ MB of git history sent | Wasted bandwidth, potential secret exposure |

## Language-Specific Production Dockerfiles

### Node.js

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:22-slim
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app/dist ./dist
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/package.json ./
ENV NODE_ENV=production
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["node", "-e", "fetch('http://localhost:3000/health').then(r => process.exit(r.ok ? 0 : 1))"]
CMD ["node", "dist/index.js"]
```

### Python (uv)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Go

```dockerfile
FROM golang:1.23 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Rust

```dockerfile
FROM rust:1.82-slim AS planner
RUN cargo install cargo-chef
WORKDIR /app
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM rust:1.82-slim AS builder
RUN cargo install cargo-chef
WORKDIR /app
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser
COPY --from=builder /app/target/release/myapp /usr/local/bin/myapp
USER appuser
ENTRYPOINT ["myapp"]
```

### Java (Spring Boot)

```dockerfile
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app
COPY gradlew build.gradle.kts settings.gradle.kts ./
COPY gradle ./gradle
RUN ./gradlew dependencies --no-daemon
COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test

FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["wget", "-q", "--spider", "http://localhost:8080/actuator/health"]
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Instruction Quick Reference

| Instruction | Production rule |
|-------------|----------------|
| `FROM` | Pin version or digest; never use `latest` |
| `RUN` | Combine related commands with `&&`; clean caches in same layer |
| `COPY` | Prefer over `ADD` (ADD has implicit tar extraction and URL fetch) |
| `WORKDIR` | Always set explicitly; avoid relative paths |
| `USER` | Switch to non-root before CMD/ENTRYPOINT |
| `EXPOSE` | Document the port; does not publish it |
| `HEALTHCHECK` | Always define for orchestrator integration |
| `LABEL` | Add OCI labels: maintainer, version, source |
