---
name: "@tank/docker-production-patterns"
description: |
  Production Docker patterns for any language or stack. Covers Dockerfile
  authoring (multi-stage builds, layer ordering, ENTRYPOINT/CMD, base image
  selection, .dockerignore), BuildKit optimization (cache mounts, build
  secrets, SSH forwarding, multi-platform builds), security hardening
  (non-root users, distroless images, read-only filesystems, image scanning
  with Trivy/Grype), Docker Compose for production (profiles, service
  dependencies, resource limits, secrets, override files), container
  lifecycle (PID 1 problem, SIGTERM handling, tini/dumb-init, health checks,
  restart policies), logging and observability (log drivers, rotation,
  structured output, CPU/memory limits), and CI/CD pipelines (GitHub Actions
  builds, image tagging strategies, registry management, multi-arch builds).
  Includes language-specific Dockerfiles for Node.js, Python, Go, Rust,
  and Java.

  Synthesizes Docker official documentation (2025-2026), Docker BuildKit
  reference, OCI Image Specification, Dockerfile reference, Docker Compose
  Specification, and CIS Docker Benchmark.

  Trigger phrases: "Dockerfile", "docker", "docker compose", "multi-stage
  build", "docker production", "docker best practices", "docker security",
  "docker non-root", "distroless", "docker health check", "docker secrets",
  "BuildKit", "docker compose production", "docker CI/CD", "docker github
  actions", "docker image size", "docker layer caching", "dockerignore",
  "docker logging", "docker resource limits", "docker graceful shutdown",
  "SIGTERM docker", "docker compose profiles", "docker tagging strategy",
  "docker node.js", "docker python", "docker go", "docker scan", "Trivy"
---

# Docker Production Patterns

## Core Philosophy

1. **Ship the minimum viable image** — Every unnecessary binary, library, and shell in the final image is attack surface and wasted bandwidth. Multi-stage builds exist to separate build-time from run-time.
2. **Layers are the caching unit** — Order instructions from least-changing (base image, system deps) to most-changing (application code). A single misordered COPY invalidates every subsequent layer.
3. **Containers are ephemeral** — Design for termination. Handle SIGTERM, drain connections, flush buffers. If your container cannot stop cleanly in 10 seconds, the architecture is wrong.
4. **Security is not optional** — Run as non-root, use read-only filesystems, scan images in CI, never bake secrets into layers. The default Docker setup is insecure for production.
5. **Compose is not just for dev** — With profiles, resource limits, health checks, and secrets, Compose serves single-host production. Know when to graduate to orchestrators.

## Quick-Start: Common Problems

### "My Docker image is too large"

1. Switch to multi-stage build — separate builder from runtime
2. Use minimal base: `*-slim`, `*-alpine`, or distroless
3. Audit .dockerignore — exclude `node_modules/`, `.git/`, tests, docs
4. Combine RUN commands to reduce layers; clean package caches in same layer
5. Copy only production artifacts into the final stage
-> See `references/dockerfile-patterns.md`

### "Builds are slow in CI"

1. Enable BuildKit (`DOCKER_BUILDKIT=1`)
2. Use `--mount=type=cache` for package manager caches (npm, pip, go mod)
3. Order COPY instructions: lockfile first, install, then source code
4. Export/import cache with `--cache-to` and `--cache-from` in CI
-> See `references/buildkit-optimization.md`

### "How do I handle secrets during build?"

1. Use BuildKit secret mounts: `--mount=type=secret,id=mykey`
2. Pass at build time: `docker build --secret id=mykey,src=./key.pem`
3. Never use `ARG` or `ENV` for secrets — they persist in image layers
-> See `references/buildkit-optimization.md` and `references/security-hardening.md`

### "Container ignores SIGTERM / takes 10s to stop"

1. Use exec form for ENTRYPOINT: `["node", "server.js"]` not `node server.js`
2. Ensure your process is PID 1 (or use `--init` / tini)
3. Register a SIGTERM handler in your application code
-> See `references/lifecycle-signals.md`

### "How do I run Compose in production?"

1. Use override files: `docker-compose.yml` (base) + `docker-compose.prod.yml`
2. Set resource limits (memory, CPU), restart policies, health checks
3. Use `docker compose --profile prod up` for environment-specific services
4. Manage secrets via Compose secrets, not environment variables
-> See `references/compose-production.md`

## Decision Trees

### Base Image Selection

| Requirement | Base Image |
|-------------|-----------|
| Smallest size, maximum security | Distroless (gcr.io/distroless) or `scratch` |
| Need shell for debugging | `*-slim` variants (debian-slim, python-slim) |
| Alpine ecosystem / musl acceptable | `*-alpine` (watch for DNS/musl issues) |
| Enterprise compliance / support | Docker Official Images, Chainguard |
| Widest compatibility | Default Debian-based tags |

### When to Graduate from Compose

| Signal | Recommendation |
|--------|---------------|
| Single host, < 10 services | Docker Compose is fine |
| Multi-host, high availability needed | Kubernetes or Docker Swarm |
| Auto-scaling required | Kubernetes |
| Rolling updates with zero downtime | Kubernetes or Swarm |
| Simple deploy, one server | Compose + systemd |

### Image Tagging Strategy

| Tag | Purpose | Mutable? |
|-----|---------|----------|
| `v1.2.3` | Release artifact, immutable reference | No |
| `sha-abc1234` | Git SHA, CI traceability | No |
| `latest` | Convenience for dev, never for production deploys | Yes |
| `main` | Latest from default branch | Yes |

## Language-Specific Quick Reference

| Language | Base (build) | Base (runtime) | Key gotcha |
|----------|-------------|---------------|------------|
| Node.js | `node:22-slim` | `node:22-slim` or distroless | Copy `package*.json` first, `npm ci --omit=dev` |
| Python | `python:3.12-slim` | `python:3.12-slim` | Use `--mount=type=cache,target=/root/.cache/pip` |
| Go | `golang:1.23` | `scratch` or distroless | `CGO_ENABLED=0` for static binary |
| Rust | `rust:1.82` | `debian:bookworm-slim` or distroless | Use `cargo-chef` for dependency caching |
| Java | `eclipse-temurin:21-jdk` | `eclipse-temurin:21-jre-alpine` | Use jlink for custom minimal JRE |

-> See `references/dockerfile-patterns.md` for complete Dockerfiles per language.

## Reference Index

| File | Contents |
|------|----------|
| `references/dockerfile-patterns.md` | Multi-stage builds, layer ordering, ENTRYPOINT vs CMD, base image selection, .dockerignore patterns, language-specific production Dockerfiles (Node.js, Python, Go, Rust, Java) |
| `references/buildkit-optimization.md` | BuildKit cache mounts, build secrets, SSH forwarding, multi-platform builds, cache export/import, CI cache backends, build arguments |
| `references/security-hardening.md` | Non-root users, distroless and minimal images, read-only filesystems, image scanning (Trivy, Grype, Snyk), secrets management, CIS benchmark essentials |
| `references/compose-production.md` | Compose v2 production configuration, profiles, service dependencies, override files, secrets, resource limits, networking, environment management |
| `references/lifecycle-signals.md` | PID 1 problem, SIGTERM/SIGKILL handling, tini and dumb-init, exec form vs shell form, health checks, restart policies, graceful shutdown patterns per language |
| `references/logging-observability.md` | Log drivers (json-file, fluentd, syslog), log rotation, structured logging, resource limits (CPU/memory/pids), monitoring patterns, OOM behavior |
| `references/cicd-registry.md` | GitHub Actions Docker builds, docker/metadata-action tagging, registry management (Docker Hub, GHCR, ECR), multi-arch builds, layer caching in CI, image promotion workflows |
