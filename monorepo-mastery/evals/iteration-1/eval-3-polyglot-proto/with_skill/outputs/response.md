For a monorepo with Go services + React frontend + Python ML pipeline that all share protobuf contracts, I would use a **hybrid structure + Pants + Buf** as the core.

Why this is the best fit for your stack:
- You are polyglot and include Python ML, so JS-only orchestrators (Turborepo, Rush) are a bad fit.
- You need one contract system (protobuf) with multi-language codegen and breaking-change checks.
- Pants gives you polyglot changed-target execution and strong caching without Bazel-level operational overhead.

## Recommended architecture

Use a **hybrid layout** (`apps/`, `services/`, `packages/`, `proto/`) so deployment units and shared code are clear.

```text
repo/
├── apps/
│   └── web/                          # React app (Vite/Next)
├── services/
│   ├── api-gateway/                  # Go service
│   ├── billing/                      # Go service
│   └── ml-orchestrator/              # Python service invoking ML pipeline
├── pipelines/
│   └── training/                     # Python ML pipeline jobs
├── packages/
│   ├── ts-sdk/                       # TS client package (optional)
│   ├── py-sdk/                       # Python client helpers (optional)
│   └── go-sdk/                       # Go shared client/helpers (optional)
├── proto/
│   ├── buf.yaml
│   ├── buf.gen.yaml
│   ├── payments/v1/*.proto
│   ├── ml/v1/*.proto
│   └── shared/v1/*.proto
├── gen/
│   ├── go/
│   ├── python/
│   └── typescript/
├── build-support/
│   └── scripts/
│       ├── proto_generate.sh
│       └── verify_proto_clean.sh
├── pnpm-workspace.yaml
├── pyproject.toml                    # uv workspace
├── go.work
├── pants.toml
├── Makefile
└── .github/workflows/ci.yml
```

## Tooling decisions

### 1) Orchestrator: Pants

Pants is the best match when Python is meaningful in the stack (which it is here, ML pipeline), while still supporting Go and JS/TS workflows.

Minimal `pants.toml` to start:

```toml
[GLOBAL]
pants_version = "2.27.0"
backend_packages = [
  "pants.backend.python",
  "pants.backend.go",
  "pants.backend.javascript",
  "pants.backend.experimental.javascript.lint.eslint",
  "pants.backend.experimental.javascript.typecheck.typescript",
  "pants.backend.shell",
]

[source]
root_patterns = ["/", "services", "apps", "pipelines", "packages", "proto", "gen"]

[python]
interpreter_constraints = [">=3.11,<3.13"]

[python.resolves]
python-default = "3rdparty/python/default.lock"

[go]
minimum_expected_version = "1.23"

[tailor]
ignore_paths = ["gen/**"]

[changed]
since = "origin/main"
```

Typical CI commands:

```bash
pants lint --changed-since=origin/main ::
pants test --changed-since=origin/main ::
pants package --changed-since=origin/main ::
```

### 2) Contracts and codegen: Buf (protobuf + gRPC)

Use one canonical proto source tree in `proto/`, generate into `gen/`.

`proto/buf.yaml`:

```yaml
version: v2
modules:
  - path: .
    name: buf.build/acme/platform-proto
lint:
  use:
    - DEFAULT
breaking:
  use:
    - FILE
```

`proto/buf.gen.yaml`:

```yaml
version: v2
plugins:
  - remote: buf.build/protocolbuffers/go
    out: ../gen/go
    opt: paths=source_relative
  - remote: buf.build/grpc/go
    out: ../gen/go
    opt: paths=source_relative
  - remote: buf.build/protocolbuffers/python
    out: ../gen/python
  - remote: buf.build/grpc/python
    out: ../gen/python
  - remote: buf.build/bufbuild/es
    out: ../gen/typescript
```

Proto workflow:

```bash
cd proto
buf lint
buf breaking --against '.git#branch=main'
buf generate
```

### 3) Workspace managers per language

Use native managers per ecosystem (not one tool forcing all ecosystems).

#### React/TS: pnpm workspace

`pnpm-workspace.yaml`:

```yaml
packages:
  - "apps/*"
  - "packages/*"

catalog:
  react: "^19.0.0"
  typescript: "^5.7.0"
  vite: "^6.0.0"
```

`apps/web/package.json` (example):

```json
{
  "name": "@acme/web",
  "private": true,
  "dependencies": {
    "react": "catalog:",
    "react-dom": "^19.0.0",
    "@acme/ts-sdk": "workspace:*"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  }
}
```

#### Python ML: uv workspace

Root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["services/*", "pipelines/*", "packages/*"]

[tool.uv.sources]
acme-py-sdk = { workspace = true }

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6.0", "mypy>=1.11.0"]
```

`pipelines/training/pyproject.toml` (example):

```toml
[project]
name = "acme-training"
version = "0.1.0"
dependencies = [
  "numpy>=2.0.0",
  "pandas>=2.2.0",
  "grpcio>=1.66.0",
  "protobuf>=5.27.0"
]
```

#### Go services: go.work overlay + per-module go.mod

`go.work`:

```text
go 1.23

use (
    ./services/api-gateway
    ./services/billing
    ./packages/go-sdk
)
```

In CI, force module correctness:

```bash
GOWORK=off go test ./...
```

## Generated code policy (important)

For this stack, commit generated stubs in `gen/`.

Why:
- Easier local dev and IDE support across Go/Python/TS.
- Avoids every consumer needing the full proto toolchain at runtime.
- Lets CI enforce: `buf generate && git diff --exit-code`.

If generated output becomes huge or noisy later, switch to build-time generation only for selected targets.

## Module/dependency boundaries

Enforce simple, explicit boundaries from day one:
- `apps/web` can import only `packages/ts-sdk` and TS libraries.
- Go services import `gen/go` + Go shared packages, never Python runtime code.
- Python pipelines import `gen/python` + Python packages, never TS/Go internals.
- No service reads raw `.proto` directly at runtime; all use generated clients.

## Root task interface (developer UX)

Use a thin root Makefile as the single developer entrypoint:

```makefile
.PHONY: proto lint test build ci

proto:
	cd proto && buf lint && buf generate

lint:
	pants lint ::

test:
	pants test ::

build:
	pants package ::

ci:
	cd proto && buf breaking --against '.git#branch=main'
	pants lint --changed-since=origin/main ::
	pants test --changed-since=origin/main ::
	pants package --changed-since=origin/main ::
```

## CI blueprint (GitHub Actions)

```yaml
name: ci

on:
  pull_request:
  merge_group:
    types: [checks_requested]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"

      - uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Install uv
        run: pipx install uv

      - name: Proto checks
        run: |
          cd proto
          buf lint
          buf breaking --against '.git#branch=main'
          buf generate
          git diff --exit-code

      - name: Pants changed targets
        run: |
          pants lint --changed-since=origin/main ::
          pants test --changed-since=origin/main ::
```

## Ownership and review safety

Add `CODEOWNERS` early for contracts and platform-critical files:

```text
/proto/                       @org/platform @org/backend
/services/api-gateway/        @org/backend
/pipelines/training/          @org/ml
/apps/web/                    @org/frontend
/pants.toml                   @org/platform
/go.work                      @org/backend
/pyproject.toml               @org/ml
/pnpm-workspace.yaml          @org/frontend
```

## When to choose something else

- Choose **Moon** instead of Pants if your team is smaller, wants very low config overhead, and Python is present but not dominant.
- Choose **Bazel** only when you need strict hermetic/reproducible builds at large scale with dedicated build engineering capacity.

## Practical rollout plan (order matters)

1. Create `proto/` + `buf.yaml` + `buf.gen.yaml`, generate Go/Python/TS stubs.
2. Lock language workspaces (`pnpm-workspace.yaml`, `pyproject.toml` with uv, `go.work`).
3. Introduce Pants for lint/test/package with changed-target CI.
4. Add root Makefile and CODEOWNERS.
5. Add CI guards: `buf breaking`, generated-code drift check, affected-only Pants runs.

If you follow this shape, you get: one source of truth for contracts, polyglot builds that scale, and fast CI without forcing a JS-only monorepo tool onto Go/Python workloads.
