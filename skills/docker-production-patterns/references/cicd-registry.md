# CI/CD and Registry Management

Sources: Docker GitHub Actions documentation (2025-2026), docker/metadata-action reference, GitHub Container Registry documentation, Docker Hub documentation, AWS ECR documentation, Docker multi-platform build guide

Covers: GitHub Actions Docker build workflows, image tagging strategies, registry selection and management, multi-architecture builds in CI, layer caching in CI pipelines, and image promotion workflows.

## GitHub Actions Docker Build

### Basic Build and Push

```yaml
name: Build and Push
on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Key Actions

| Action | Purpose | Version |
|--------|---------|---------|
| `docker/setup-buildx-action` | Install Buildx for advanced builds | v3 |
| `docker/login-action` | Authenticate to any registry | v3 |
| `docker/metadata-action` | Generate tags and OCI labels | v5 |
| `docker/build-push-action` | Build and push images | v6 |
| `docker/setup-qemu-action` | Enable multi-platform emulation | v3 |

## Image Tagging Strategy

### docker/metadata-action Configuration

```yaml
- name: Extract metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: |
      ghcr.io/${{ github.repository }}
      docker.io/myorg/myapp
    tags: |
      # Semver tags from git tags
      type=semver,pattern={{version}}
      type=semver,pattern={{major}}.{{minor}}
      type=semver,pattern={{major}}
      # Branch name
      type=ref,event=branch
      # PR number
      type=ref,event=pr
      # Git short SHA
      type=sha,prefix=sha-
      # Latest on default branch
      type=raw,value=latest,enable={{is_default_branch}}
```

### Tag Types Explained

| Type | Pattern | Git event | Example output |
|------|---------|-----------|----------------|
| `semver` | `{{version}}` | Tag: `v1.2.3` | `1.2.3` |
| `semver` | `{{major}}.{{minor}}` | Tag: `v1.2.3` | `1.2` |
| `semver` | `{{major}}` | Tag: `v1.2.3` | `1` |
| `ref` | `event=branch` | Push to `main` | `main` |
| `ref` | `event=pr` | PR #42 | `pr-42` |
| `sha` | `prefix=sha-` | Any push | `sha-abc1234` |
| `raw` | `value=latest` | Default branch | `latest` |

### Tagging Best Practices

| Practice | Reason |
|----------|--------|
| Use semver for releases | Clear version communication |
| Include SHA tag for traceability | Link image to exact commit |
| Use immutable tags for deploys | `v1.2.3` not `latest` |
| Never deploy `latest` to production | Mutable tag, unpredictable content |
| Tag PRs with `pr-N` | Easy identification of PR builds |
| Multi-tag pushes | One build produces multiple useful tags |

### Immutable vs Mutable Tags

| Tag type | Example | Mutable? | Use for |
|----------|---------|----------|---------|
| Semver | `v1.2.3` | No (by convention) | Production deploys |
| Git SHA | `sha-abc1234` | No | CI traceability |
| Branch | `main`, `develop` | Yes (overwritten) | Staging environments |
| `latest` | `latest` | Yes | Development convenience |
| PR | `pr-42` | Yes (per push) | PR review environments |

## Registry Selection

### Registry Comparison

| Registry | Free tier | Private repos | Auth | Best for |
|----------|-----------|--------------|------|----------|
| Docker Hub | 1 private repo | Paid plans | Docker ID | Public images, OSS |
| GitHub Container Registry (GHCR) | Unlimited private (with GH plan) | Included | GITHUB_TOKEN | GitHub-native projects |
| AWS ECR | 500 MB free | Per-repo pricing | IAM | AWS deployments |
| Google Artifact Registry | 500 MB free | Per-project | IAM | GCP deployments |
| Azure Container Registry | Basic tier | Per-registry | Azure AD | Azure deployments |
| Self-hosted (Harbor) | Unlimited | N/A | Configurable | Air-gapped, compliance |

### Login Patterns

#### Docker Hub

```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

#### GHCR

```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

#### AWS ECR

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/github-actions
    aws-region: us-east-1

- name: Login to ECR
  uses: aws-actions/amazon-ecr-login@v2
```

### Multi-Registry Push

Push to multiple registries from a single build:

```yaml
- name: Extract metadata
  uses: docker/metadata-action@v5
  with:
    images: |
      ghcr.io/${{ github.repository }}
      docker.io/myorg/myapp
      123456789.dkr.ecr.us-east-1.amazonaws.com/myapp
```

## Multi-Architecture Builds in CI

### GitHub Actions with QEMU

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push multi-arch
  uses: docker/build-push-action@v6
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Platform Selection

| Platform | Use case |
|----------|----------|
| `linux/amd64` | Standard x86 servers (AWS, GCP, most CI) |
| `linux/arm64` | AWS Graviton, Apple Silicon, Raspberry Pi |
| `linux/arm/v7` | Older ARM devices (Raspberry Pi 3) |
| `linux/amd64,linux/arm64` | Most common multi-arch combo |

### Cross-Compilation vs Emulation

| Approach | Speed | Compatibility | When to use |
|----------|-------|---------------|-------------|
| QEMU emulation | Slow (5-10x) | Works for everything | Default, simple setup |
| Cross-compilation | Fast (native speed) | Language must support it | Go, Rust, C with proper toolchain |
| Native runners | Fast | Full compatibility | Expensive, per-arch runners |

For Go and Rust, prefer cross-compilation using `$BUILDPLATFORM` and `$TARGETARCH` (see `references/buildkit-optimization.md`).

## Layer Caching in CI

### GitHub Actions Cache Backend

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

GitHub Actions cache is scoped per branch. PRs can read the default branch cache but write to their own scope.

### Registry Cache Backend

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=registry,ref=ghcr.io/myorg/myapp:buildcache
    cache-to: type=registry,ref=ghcr.io/myorg/myapp:buildcache,mode=max
```

Registry cache is shared across all branches and CI runs. Larger storage but network-bound.

### Cache Strategy Decision

| Factor | GHA cache | Registry cache |
|--------|-----------|---------------|
| Speed | Fast (local to runner) | Network latency |
| Size limit | 10 GB per repo | Unlimited |
| Sharing | Branch-scoped | Global |
| Setup | Zero config | Needs registry login |
| Cost | Free (within GHA limits) | Registry storage costs |
| Best for | Most projects | Large images, many branches |

## Image Promotion Workflow

Promote images through environments without rebuilding:

```
Build (PR) -> Test (staging tag) -> Promote (production tag) -> Deploy
```

### Tag-Based Promotion

```bash
# After successful staging tests, retag for production
docker buildx imagetools create \
  ghcr.io/myorg/myapp:sha-abc1234 \
  --tag ghcr.io/myorg/myapp:v1.2.3 \
  --tag ghcr.io/myorg/myapp:production
```

`imagetools create` adds tags to existing manifests without pulling or pushing image layers.

### GitHub Actions Promotion

```yaml
promote:
  needs: [test-staging]
  runs-on: ubuntu-latest
  steps:
    - uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Promote to production
      run: |
        docker buildx imagetools create \
          ghcr.io/${{ github.repository }}:sha-${{ github.sha }} \
          --tag ghcr.io/${{ github.repository }}:${{ github.ref_name }} \
          --tag ghcr.io/${{ github.repository }}:production
```

### Image Lifecycle

| Phase | Tag | Retention |
|-------|-----|-----------|
| Build | `sha-abc1234`, `pr-42` | 30 days (auto-cleanup) |
| Staging | `staging`, `sha-abc1234` | Until replaced |
| Production | `v1.2.3`, `production` | Indefinite (last N versions) |
| Deprecated | Keep semver tag | 90 days after replacement |

### Registry Cleanup

```bash
# GHCR: delete untagged images older than 30 days
gh api --method DELETE \
  /user/packages/container/myapp/versions/VERSION_ID

# ECR lifecycle policy
aws ecr put-lifecycle-policy --repository-name myapp --lifecycle-policy-text '{
  "rules": [{
    "rulePriority": 1,
    "selection": {
      "tagStatus": "untagged",
      "countType": "sinceImagePushed",
      "countUnit": "days",
      "countNumber": 30
    },
    "action": { "type": "expire" }
  }]
}'
```

## OCI Labels

Add metadata to images for traceability:

```dockerfile
LABEL org.opencontainers.image.title="My App"
LABEL org.opencontainers.image.description="Production API service"
LABEL org.opencontainers.image.url="https://github.com/myorg/myapp"
LABEL org.opencontainers.image.source="https://github.com/myorg/myapp"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.licenses="MIT"
```

The `docker/metadata-action` generates these labels automatically from GitHub context.
