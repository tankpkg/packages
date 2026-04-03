# Security Hardening

Sources: CIS Docker Benchmark v1.7, Docker Hardened Images documentation (2025-2026), OWASP Docker Security Cheat Sheet, Trivy documentation, Grype documentation, Snyk Container documentation, Google distroless project

Covers: non-root user configuration, distroless and minimal base images, read-only filesystems, image scanning tools and CI integration, secrets management in containers, and essential CIS benchmark controls.

## Non-Root Users

Docker containers run as root by default. A container escape with root privileges gives the attacker root on the host (unless user namespaces are configured). Run as non-root.

### Creating a Non-Root User

#### Debian/Ubuntu-based

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
```

#### Alpine-based

```dockerfile
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
```

#### Distroless

Distroless images include a `nonroot` user (UID 65532):

```dockerfile
FROM gcr.io/distroless/nodejs22-debian12:nonroot
COPY --chown=nonroot:nonroot ./dist /app
CMD ["app/index.js"]
```

Or use the numeric UID:

```dockerfile
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
USER 65532:65532
ENTRYPOINT ["/server"]
```

### Placement Rules

| Rule | Reason |
|------|--------|
| Set USER after all RUN, COPY instructions that need root | Package installation requires root |
| Set USER before CMD/ENTRYPOINT | Application runs as non-root |
| Use `--chown` on COPY | Files owned by non-root user without extra layer |
| Use numeric UIDs in Kubernetes | Some admission controllers require numeric UIDs |

### Port Considerations

Non-root users cannot bind to ports below 1024. Bind to high ports (3000, 8080, 8443) and map externally:

```bash
docker run -p 80:8080 myapp
```

## Distroless and Minimal Images

Minimal images remove shells, package managers, and utilities. No shell means attackers cannot execute commands inside a compromised container.

### Distroless Variants

| Image | Runtime | Size | Use for |
|-------|---------|------|---------|
| `gcr.io/distroless/static-debian12` | None | ~2 MB | Statically-linked Go/Rust binaries |
| `gcr.io/distroless/base-debian12` | glibc | ~20 MB | C/C++ with dynamic linking |
| `gcr.io/distroless/cc-debian12` | glibc + libgcc | ~25 MB | C++ with libstdc++ |
| `gcr.io/distroless/nodejs22-debian12` | Node.js 22 | ~120 MB | Node.js applications |
| `gcr.io/distroless/python3-debian12` | Python 3 | ~50 MB | Python applications |
| `gcr.io/distroless/java21-debian12` | Java 21 | ~220 MB | Java applications |

Every variant has a `:nonroot` tag with the non-root user preconfigured.

### Chainguard Images

Chainguard provides hardened images with SBOMs, daily rebuild for CVE patches, and FIPS variants:

```dockerfile
FROM cgr.dev/chainguard/node:latest
```

### Debugging Distroless

No shell means `docker exec -it container sh` fails. Options:

| Technique | Command |
|-----------|---------|
| Debug variant | Use `:debug` tag (includes busybox shell) |
| Ephemeral container | `docker debug container_name` (Docker Desktop) |
| Copy files out | `docker cp container:/path ./local` |
| Logs | `docker logs container` (stdout/stderr always available) |

## Read-Only Filesystems

Prevent runtime modification of the container filesystem. If an attacker gains code execution, they cannot write malicious scripts.

### Docker Run

```bash
docker run --read-only --tmpfs /tmp:rw,noexec,nosuid myapp
```

### Docker Compose

```yaml
services:
  app:
    image: myapp:latest
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
    volumes:
      - app-data:/app/data:rw
```

### Common Writable Paths

Applications often need to write to specific paths. Mount tmpfs or volumes for those:

| Application | Writable path needed | Solution |
|-------------|---------------------|----------|
| Node.js | `/tmp` | tmpfs |
| Python | `/tmp`, `__pycache__` | tmpfs, or disable with `PYTHONDONTWRITEBYTECODE=1` |
| Java | `/tmp` (JVM temp) | tmpfs |
| Nginx | `/var/cache/nginx`, `/var/run` | tmpfs |
| Any | Application log directory | Named volume or tmpfs |

### Security Profile

Combine read-only with other restrictions:

```bash
docker run \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges \
  myapp
```

## Image Scanning

Scan images for known vulnerabilities (CVEs) before pushing to production. Integrate scanning into CI to fail builds on critical findings.

### Tool Comparison

| Tool | License | Speed | Accuracy | SBOM | CI Integration |
|------|---------|-------|----------|------|----------------|
| Trivy | Apache 2.0 | Fast | High | Yes | GitHub Actions, GitLab, Jenkins |
| Grype | Apache 2.0 | Fast | High | Via Syft | GitHub Actions, GitLab |
| Snyk Container | Commercial | Medium | High | Yes | GitHub, GitLab, CLI |
| Docker Scout | Commercial | Medium | High | Yes | Docker Desktop, CLI |
| Clair | Apache 2.0 | Slow | Medium | No | Registry integration |

### Trivy Usage

```bash
# Scan local image
trivy image myapp:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL myapp:latest

# Fail on critical (CI gate)
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Generate SBOM
trivy image --format spdx-json --output sbom.json myapp:latest

# Scan Dockerfile for misconfigurations
trivy config ./Dockerfile
```

### Grype Usage

```bash
# Scan image
grype myapp:latest

# Fail on high severity
grype myapp:latest --fail-on high

# Use SBOM as input (from Syft)
syft myapp:latest -o spdx-json > sbom.json
grype sbom:./sbom.json
```

### GitHub Actions Integration

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE }}
    format: sarif
    output: trivy-results.sarif
    severity: CRITICAL,HIGH
    exit-code: "1"

- name: Upload scan results
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: trivy-results.sarif
```

### Vulnerability Management

| Severity | Action | SLA |
|----------|--------|-----|
| Critical | Block deployment, fix immediately | 24 hours |
| High | Block deployment in most orgs | 7 days |
| Medium | Track, fix in next release | 30 days |
| Low | Track, prioritize by context | 90 days |

### Reducing Vulnerability Count

| Strategy | Impact |
|----------|--------|
| Use minimal/distroless base | 80-95% fewer CVEs |
| Update base images weekly | Patch known CVEs |
| Remove unused packages | Fewer vulnerable components |
| Pin and audit dependencies | Controlled supply chain |
| Multi-stage builds | Build tools not in final image |

## Secrets in Running Containers

Build-time secrets (see `references/buildkit-optimization.md`) and runtime secrets are different concerns.

### Runtime Secret Delivery

| Method | Security | Complexity | Use when |
|--------|----------|------------|----------|
| Docker secrets (Swarm) | High (tmpfs, encrypted) | Medium | Docker Swarm |
| Compose secrets (file-based) | Medium (file on host) | Low | Single-host Compose |
| Environment variables | Low (visible in inspect) | Low | Non-sensitive config only |
| Volume mount from secret manager | High | Medium | Vault, AWS SM, GCP SM |
| Init container/sidecar | High | High | Kubernetes patterns |

### Compose Secrets

```yaml
services:
  app:
    image: myapp:latest
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    environment: API_KEY
```

Secrets mount as files at `/run/secrets/<name>`. Read the file in application code:

```python
import pathlib
db_password = pathlib.Path("/run/secrets/db_password").read_text().strip()
```

### Environment Variable Risks

| Risk | Details |
|------|---------|
| `docker inspect` exposes all env vars | Any user with Docker socket access sees secrets |
| Process listing shows env vars | `cat /proc/1/environ` inside container |
| Logging frameworks may dump env | Unintentional secret logging |
| Child processes inherit env | Secrets propagate to subprocesses |
| Orchestrator UIs display env | Dashboard exposure |

Prefer file-based secrets for anything genuinely sensitive.

## CIS Docker Benchmark Essentials

Key controls from the CIS Docker Benchmark relevant to image and container configuration:

| Control | Recommendation |
|---------|---------------|
| 4.1 | Use a non-root user in containers |
| 4.2 | Use trusted base images only |
| 4.3 | Do not install unnecessary packages |
| 4.4 | Scan images for vulnerabilities |
| 4.6 | Add HEALTHCHECK instruction |
| 4.9 | Use COPY instead of ADD |
| 5.2 | Do not use host networking unless required |
| 5.4 | Do not mount sensitive host paths |
| 5.10 | Set memory and CPU limits |
| 5.12 | Mount root filesystem as read-only |
| 5.15 | Do not share the host process namespace |
| 5.25 | Restrict container capabilities |
| 5.28 | Use `--pids-limit` to prevent fork bombs |

### Capability Dropping

```bash
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp
```

Common capabilities needed:

| Capability | Required for |
|------------|-------------|
| `NET_BIND_SERVICE` | Binding to ports < 1024 |
| `CHOWN` | Changing file ownership at runtime |
| `SETGID`, `SETUID` | Switching user at runtime |
| `DAC_OVERRIDE` | Reading files not owned by user |

Drop ALL and add back only what the application requires.
