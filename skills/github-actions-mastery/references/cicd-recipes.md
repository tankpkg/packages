# CI/CD Recipes

Sources: GitHub Actions documentation (2026), Docker build-push-action docs, semantic-release documentation, act (nektos/act) documentation, actions-runner-controller (ARC) docs

Covers: test/lint workflows, semantic release, Docker multi-platform builds, cloud deployment patterns, self-hosted runners, local testing with act, and production-ready workflow templates.

## Test and Lint

### Node.js CI

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions: {}

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test
```

### Python CI

```yaml
jobs:
  test:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: 'pip'
      - run: pip install -e ".[dev]"
      - run: pytest --cov --junitxml=results.xml
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.python }}
          path: results.xml
```

### E2E Tests with Service Containers

```yaml
jobs:
  e2e:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run e2e
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
```

## Semantic Release

Automate versioning and changelog generation based on conventional commits:

```yaml
name: Release
on:
  push:
    branches: [main]

permissions: {}

jobs:
  release:
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Tag-Based Release

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

## Docker Build and Push

### Single-Platform Build

```yaml
name: Docker
on:
  push:
    branches: [main]

jobs:
  build:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Multi-Platform Build

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Push to Multiple Registries

```yaml
steps:
  - uses: docker/login-action@v3
    with:
      registry: ghcr.io
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}
  - uses: docker/login-action@v3
    with:
      username: ${{ secrets.DOCKERHUB_USERNAME }}
      password: ${{ secrets.DOCKERHUB_TOKEN }}
  - uses: docker/build-push-action@v6
    with:
      push: true
      tags: |
        ghcr.io/${{ github.repository }}:latest
        ${{ secrets.DOCKERHUB_USERNAME }}/myapp:latest
```

## Cloud Deployment

### Deploy to AWS (OIDC)

```yaml
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - run: aws s3 sync dist/ s3://${{ vars.S3_BUCKET }}/
      - run: aws cloudfront create-invalidation --distribution-id ${{ vars.CF_DIST_ID }} --paths "/*"
```

### Deploy to Vercel

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.ref == 'refs/heads/main' && 'production' || 'preview' }}
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci && npm run build
      - id: deploy
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            URL=$(npx vercel --prod --token ${{ secrets.VERCEL_TOKEN }})
          else
            URL=$(npx vercel --token ${{ secrets.VERCEL_TOKEN }})
          fi
          echo "url=$URL" >> "$GITHUB_OUTPUT"
```

## Self-Hosted Runners

### When to Use Self-Hosted

| Signal | Runner Type |
|--------|------------|
| Standard CI (build, test, lint) | GitHub-hosted |
| GPU, ARM, or specialized hardware | Self-hosted |
| Air-gapped or regulated environment | Self-hosted |
| Large repos (>10 GB) or persistent build cache | Self-hosted |
| Cost optimization (high-volume CI) | Self-hosted |

### Actions Runner Controller (ARC) on Kubernetes

```bash
# Install ARC
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Deploy runner scale set
helm install arc-runner-set \
  --namespace arc-runners \
  --create-namespace \
  -f values.yaml \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

### Runner Labels

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux, x64, gpu]
```

Apply labels to runners to route specific jobs to appropriate hardware.

### Security for Self-Hosted Runners

| Risk | Mitigation |
|------|-----------|
| Previous job artifacts remain | Use ephemeral runners (ARC default) |
| Untrusted code execution | Never use self-hosted for public repos |
| Network access to internal systems | Restrict runner network access |
| Credential persistence | Use OIDC, not stored credentials |

## Local Testing with act

[`act`](https://github.com/nektos/act) runs GitHub Actions workflows locally using Docker:

```bash
# Install
brew install act

# Run default event (push)
act

# Run specific workflow
act -W .github/workflows/ci.yml

# Run specific job
act -j test

# Run with specific event
act pull_request

# Pass secrets
act -s GITHUB_TOKEN="$(gh auth token)"

# Use specific runner image
act --platform ubuntu-latest=catthehacker/ubuntu:act-latest
```

### act Limitations

| Limitation | Workaround |
|-----------|-----------|
| No service containers | Use Docker Compose alongside |
| Some actions incompatible | Mock or skip with `act-only` conditionals |
| No OIDC token support | Use traditional credentials locally |
| `macos-latest` not supported | Test macOS jobs only in CI |
| Large runner images | Use `-P ubuntu-latest=...` for smaller images |

### Conditional Steps for Local vs CI

```yaml
- if: ${{ !env.ACT }}
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: npm-${{ hashFiles('**/package-lock.json') }}
```

`env.ACT` is set when running under `act`, allowing conditional logic for steps that do not work locally.

## Workflow Status Badges

```markdown
![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg)
![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg?branch=main)
```

Add to README.md to display workflow status.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No `concurrency` on PR CI | Stale runs waste minutes | Add cancel-in-progress concurrency |
| `fetch-depth: 0` everywhere | Slow clones for large repos | Use `fetch-depth: 1` unless history needed |
| Missing `cache-from/to` on Docker | Full rebuild every time | Use `type=gha` cache backend |
| Self-hosted runners for public repos | Fork PRs execute untrusted code on your infrastructure | Use GitHub-hosted for public repos |
| No environment protection for prod | Any push to main deploys without review | Add required reviewers on production environment |
| Hardcoded versions in workflows | Drift, manual updates | Use `vars.` for versions, matrix for multi-version |
