# Polyglot Monorepo Patterns

Sources: Software Engineering at Google (Winters et al, 2020), Google ACM 2016 paper, Antoniucci (Ultimate Monorepo, 2024), 2024-2026 industry research

Covers: repository structure patterns, cross-language dependency strategies, CODEOWNERS, shared tooling, real-world case studies, orchestrator comparison, decision framework.

## Repository Structure Patterns

Three dominant layouts exist in production monorepos. Choose based on team topology and growth trajectory.

### Domain-First (2026 Standard)

Group directories by business domain, with language as a secondary concern within each domain.

```
repo/
├── payments/
│   ├── api/          # Go gRPC service
│   ├── worker/       # Python batch processor
│   ├── sdk/          # TypeScript client SDK
│   └── proto/        # Shared protobuf definitions
├── identity/
│   ├── service/      # Rust auth service
│   ├── admin-ui/     # React frontend
│   └── proto/
├── analytics/
│   ├── pipeline/     # Python/Spark
│   ├── dashboard/    # TypeScript
│   └── models/       # Python ML models
└── shared/
    ├── infra/        # Terraform modules
    ├── proto/        # Cross-domain contracts
    └── scripts/      # Polyglot dev tooling
```

Domain-first aligns with Conway's Law: teams own vertical slices, not horizontal language layers. Code review, ownership, and deployment boundaries map to business units rather than technology stacks.

### Language-First

Group by language or runtime at the top level.

```
repo/
├── go/
│   ├── services/
│   └── libraries/
├── python/
│   ├── services/
│   └── libraries/
├── typescript/
│   ├── apps/
│   └── packages/
└── proto/
```

Language-first simplifies toolchain configuration — one `go.work`, one `pyproject.toml` at the language root. Works well when teams are organized by language expertise rather than product domain. Becomes unwieldy when a single feature spans multiple language directories.

### Hybrid (Apps + Services + Packages + Proto)

```
repo/
├── apps/             # User-facing frontends
├── services/         # Backend microservices (any language)
├── packages/         # Shared libraries (any language)
├── proto/            # All protobuf definitions
└── infra/            # Infrastructure as code
```

Hybrid is the most common pattern in mid-size organizations. It separates deployment units (apps, services) from reusable code (packages) without enforcing language segregation.

### Structure Pattern Comparison

| Pattern | Best For | Strengths | Weaknesses |
|---------|----------|-----------|------------|
| Domain-first | Product orgs, Conway's Law alignment | Clear ownership, vertical slices, easy onboarding | Cross-domain shared code harder to discover |
| Language-first | Language-specialist teams, simple toolchains | Toolchain config simple, language experts navigate easily | Feature work spans multiple top-level dirs |
| Hybrid | Mid-size orgs, mixed team topologies | Flexible, widely understood | Ambiguity about where new code belongs |

## Cross-Language Dependency Patterns

### Protocol Buffers and gRPC

Protocol Buffers are the dominant contract format for polyglot service communication. Define once, generate clients in any language.

Canonical `proto/` directory structure:

```
proto/
├── buf.yaml              # buf.build configuration
├── buf.gen.yaml          # Code generation targets
├── payments/
│   └── v1/
│       ├── service.proto
│       └── types.proto
├── identity/
│   └── v1/
│       └── service.proto
└── shared/
    └── v1/
        └── common.proto
```

`buf.yaml` — workspace configuration:

```yaml
version: v2
modules:
  - path: .
    name: buf.build/yourorg/protos
lint:
  use:
    - DEFAULT
breaking:
  use:
    - FILE
```

`buf.gen.yaml` — multi-language generation:

```yaml
version: v2
plugins:
  - remote: buf.build/protocolbuffers/go
    out: gen/go
    opt: paths=source_relative
  - remote: buf.build/grpc/go
    out: gen/go
    opt: paths=source_relative
  - remote: buf.build/protocolbuffers/python
    out: gen/python
  - remote: buf.build/grpc/python
    out: gen/python
  - remote: buf.build/bufbuild/es
    out: gen/typescript
```

**Code generation strategy — committed vs build-time:**

Commit generated code when: team uses multiple IDEs, CI must be hermetic without network access, generated code needs code review, or non-build-tool consumers exist (e.g., scripts reading generated types).

Generate at build time when: generated code is large (>10k files), strict single-source-of-truth is required, or build system (Bazel/Buck2) manages hermetic generation natively.

Most organizations commit generated code for gRPC stubs and regenerate on proto changes via CI check (`buf generate && git diff --exit-code`).

Use `buf breaking` in CI to detect backward-incompatible proto changes before merge.

### OpenAPI and JSON Schema

For REST APIs, OpenAPI 3.x serves as the contract layer. Store specs alongside the service that owns them:

```
services/
└── catalog/
    ├── openapi.yaml      # Source of truth
    ├── src/              # Service implementation
    └── gen/              # Generated clients (committed)
        ├── go/
        ├── python/
        └── typescript/
```

Generate clients with `openapi-generator-cli`:

```bash
openapi-generator-cli generate \
  -i services/catalog/openapi.yaml \
  -g typescript-fetch \
  -o services/catalog/gen/typescript \
  --additional-properties=supportsES6=true
```

Run generation in CI and fail on diff to enforce spec-code consistency.

JSON Schema works well for shared configuration validation across services. Store schemas in `shared/schemas/` and reference from service configs. Use `ajv` (Node), `jsonschema` (Python), or `serde_json` (Rust) for validation.

### Shared Configuration Files

Centralize configuration that multiple services consume in `shared/config/` (logging format, OpenTelemetry templates, feature flag definitions) and `shared/schemas/` (JSON Schema for service configs and deployment manifests). Services reference shared configs via relative paths or symlinks. A single change in `shared/config/` propagates to all consumers — avoid duplicating config values across service directories.

### Shared Docker Base Images

Define base images in `infra/docker/` (one directory per runtime: `base-go/`, `base-python/`, `base-node/`) and reference by digest in service Dockerfiles:

```dockerfile
FROM ghcr.io/yourorg/base-go@sha256:abc123... AS builder
```

Reference by digest, not tag, to ensure reproducibility. Build and push base images in CI when their Dockerfiles change. Use Renovate bot to automate digest updates across service Dockerfiles.

### Makefile as Polyglot Orchestration Layer

A root `Makefile` provides a language-agnostic interface for common developer tasks. Every engineer runs the same commands regardless of which service they work on.

```makefile
.PHONY: help build test lint proto clean dev

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

proto:  ## Regenerate all protobuf clients
	buf generate
	@echo "Proto generation complete"

build:  ## Build all services
	$(MAKE) -C services/payments build
	$(MAKE) -C services/identity build
	cd typescript && pnpm build

test:  ## Run all tests
	go test ./...
	pytest python/
	cd typescript && pnpm test

lint:  ## Lint all languages
	golangci-lint run ./go/...
	ruff check python/
	cd typescript && pnpm lint
	buf lint

dev:  ## Start local development stack
	docker compose up -d
	@echo "Services running. See http://localhost:3000"

clean:  ## Remove build artifacts
	find . -name "*.pyc" -delete
	find . -name "node_modules" -type d -prune -exec rm -rf {} +
	go clean ./...
```

Keep Makefile targets thin — they delegate to language-native tools. The Makefile is the entry point, not the implementation.

## CODEOWNERS Patterns

GitHub and GitLab CODEOWNERS files enforce review requirements at directory granularity.

### Per-Directory

```
# CODEOWNERS
# Domain teams own their vertical slices
/payments/                    @org/payments-team
/identity/                    @org/identity-team
/analytics/                   @org/analytics-team

# Shared infrastructure requires platform review
/shared/infra/                @org/platform-team
/infra/                       @org/platform-team

# Proto changes require both domain team and platform review
/proto/payments/              @org/payments-team @org/platform-team
/proto/identity/              @org/identity-team @org/platform-team
/proto/shared/                @org/platform-team

# Root config files require senior review
/.github/                     @org/repo-admins
/Makefile                     @org/platform-team
/buf.yaml                     @org/platform-team
```

### Language-Team Ownership

When teams are organized by language, add language-specific ownership for toolchain files:

```
# Go toolchain files
/go.work                      @org/go-guild
/go.work.sum                  @org/go-guild
**/*.go                       @org/go-guild

# Python toolchain files
/pyproject.toml               @org/python-guild
/uv.lock                      @org/python-guild

# TypeScript toolchain files
/pnpm-workspace.yaml          @org/frontend-guild
/tsconfig.base.json           @org/frontend-guild
```

### Cross-Cutting Concerns

Security-sensitive paths require security team review regardless of domain:

```
# Security-sensitive paths — always require security review
**/auth/                      @org/security-team
**/crypto/                    @org/security-team
**/secrets/                   @org/security-team
**/*_secret*                  @org/security-team
**/*_key*                     @org/security-team
/shared/schemas/              @org/platform-team @org/security-team
```

Avoid over-specifying CODEOWNERS — too many required reviewers creates bottlenecks. Assign ownership at the directory level, not file level, except for critical cross-cutting files.

## Shared Tooling Across Languages

### Lefthook (Polyglot Git Hooks Standard)

Lefthook is a Go binary that manages git hooks across any language stack. Install once, configure in `lefthook.yml`, works for all contributors regardless of their primary language.

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    lint-go:
      glob: "**/*.go"
      run: golangci-lint run {staged_files}
    lint-python:
      glob: "**/*.py"
      run: ruff check {staged_files}
    lint-typescript:
      glob: "**/*.{ts,tsx}"
      run: cd typescript && pnpm eslint {staged_files}
    format-go:
      glob: "**/*.go"
      run: gofmt -w {staged_files}
    format-python:
      glob: "**/*.py"
      run: ruff format {staged_files}

pre-push:
  commands:
    proto-check:
      run: buf lint && buf breaking --against '.git#branch=main'
    test-changed:
      run: scripts/test-changed.sh
```

Install: `lefthook install` — creates git hooks that call lefthook. Commit `lefthook.yml` to the repo. Each contributor runs `lefthook install` once after cloning.

Lefthook outperforms Husky (Node-only), pre-commit (Python-only), and shell scripts (fragile) for polyglot repos.

### .editorconfig

`.editorconfig` enforces consistent formatting across editors and languages without requiring per-language formatter configuration:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.go]
indent_style = tab
indent_size = 4

[*.{py,pyi}]
indent_style = space
indent_size = 4

[*.{ts,tsx,js,jsx,json,yaml,yml}]
indent_style = space
indent_size = 2

[*.proto]
indent_style = space
indent_size = 2

[Makefile]
indent_style = tab

[*.md]
trim_trailing_whitespace = false
```

All major editors (VS Code, JetBrains, Vim, Emacs) support `.editorconfig` natively or via plugin.

### Dev Containers

`.devcontainer/devcontainer.json` provides a consistent environment across all contributors. Define one container with all language runtimes via `devcontainers/features` (go, python, node). Set `postCreateCommand` to `lefthook install && make deps` so hooks and dependencies install automatically on first open. Add language-specific VS Code extensions in `customizations.vscode.extensions`.

Dev containers eliminate "works on my machine" problems and reduce onboarding time from days to hours. Commit the devcontainer definition alongside the Lefthook and editorconfig files as the standard contributor setup trio.

## Real-World Monorepo Case Studies

| Organization | Scale | VCS | Build System | Key Characteristics |
|---|---|---|---|---|
| Google | 10B+ LOC, 86TB, 45K engineers | Piper (internal) + CitC (cloud workspace) | Blaze (open-sourced as Bazel) | Single global repo, no branches for development, 25K commits/day, hermetic builds |
| Meta | Per-language repos (www, fbcode, etc.) | Sapling (open-sourced) | Buck2 | Not a single monorepo — federated per-language repos with shared tooling, Sapling handles scale |
| Microsoft | Virtual Monorepo (VMR) for .NET | Git + Scalar | MSBuild + custom | Scalar enables Git at scale (250GB+ repos), sparse checkout, partial clone |
| Uber | Per-language monorepos, 3K+ services | Git | Bazel | Go monorepo, Python monorepo, JavaScript monorepo — separate repos per language, unified Bazel config |
| Airbnb | JVM monorepo migrated to Bazel | Git | Bazel (migrated from Gradle) | 4.5-year migration, 3-5x build speed improvement, 100K+ source files, required dedicated build-infra team |

Key insight from Google's ACM 2016 paper: the monorepo model requires investment in tooling proportional to scale. At Google's scale, the build system, code search, and review tooling are themselves major engineering efforts. Smaller organizations should not attempt to replicate Google's infrastructure — use Bazel or Nx instead of building custom tooling.

## Polyglot Build Orchestrator Comparison

| Tool | Language Support | Learning Curve | Scale Ceiling | Incremental Builds | Remote Cache | Best For |
|---|---|---|---|---|---|---|
| Bazel | Full polyglot (any language with rules) | Very high — BUILD files, Starlark, hermetic sandboxing | Unlimited (Google-proven) | Yes, hermetic | Yes (Bazel Remote Cache, EngFlow, BuildBuddy) | Large orgs, any language mix, long-term investment |
| Buck2 | Full polyglot (BUCK files, Starlark) | Very high — similar to Bazel | Unlimited (Meta-proven) | Yes, hermetic | Yes | Meta-style orgs, Rust-heavy stacks |
| Pants | Python-first, Java/Scala/Go/JS growing | Medium — `pants.toml`, targets | Large (1K+ services) | Yes | Yes (remote cache plugin) | Python-heavy orgs, data engineering |
| Moon | JS/TS + Rust + Go + Python growing | Low-medium — `moon.yml`, familiar config | Medium-large | Yes | Yes (Moonbase) | JS + one other language, growing teams |
| Nx | JS/TS-first, Go/Rust/Python via plugins | Medium — generators, executors | Large | Yes | Yes (Nx Cloud) | JS-primary orgs adding other languages |
| Turborepo | JavaScript/TypeScript only | Low — minimal config | Medium | Yes | Yes (Vercel Remote Cache) | Pure JS/TS monorepos |
| Gradle | JVM-primary (Java, Kotlin, Scala) | Medium | Large | Yes | Yes (Gradle Enterprise) | JVM-heavy orgs |

Remote caching is the highest-leverage feature for build speed. Prioritize tools with mature remote cache support when team size exceeds 10 engineers.

## Decision Framework
### Language Composition

| Situation | Recommendation | Rationale |
|---|---|---|
| JavaScript/TypeScript only | Turborepo or Nx | Lowest overhead, best ecosystem fit, fast setup |
| Python-heavy (>60% Python) | Pants | Native Python support, good for data/ML pipelines |
| JS + one other language | Moon | Polyglot support without Bazel complexity |
| Large org, any language mix | Bazel | Proven at scale, hermetic builds, long-term ROI |
| Meta-style, Rust-heavy | Buck2 | Meta-proven, excellent Rust support |
| JVM-primary | Gradle with build cache | Familiar to Java/Kotlin teams, mature ecosystem |

### Scale

| Team Size | Recommendation |
|---|---|
| 1-10 engineers | Turborepo, Nx, or Moon — low overhead |
| 10-50 engineers | Nx, Moon, or Pants — remote caching essential |
| 50-200 engineers | Pants, Moon, or Bazel — invest in build infra |
| 200+ engineers | Bazel or Buck2 — full hermetic build system |

### Migration Path

When migrating an existing multi-repo setup to a monorepo, sequence the work to minimize disruption:

1. Map existing repos to domain directories using domain-first structure.
2. Add a root `Makefile` as the unified developer interface before touching build systems.
3. Introduce Lefthook — replaces per-repo hook configurations in one step.
4. Commit generated proto/OpenAPI code from the start to reduce migration friction.
5. Migrate build system incrementally — run old and new systems in parallel during transition.
6. Add CODEOWNERS after team ownership is clear — premature assignment creates review bottlenecks.

Airbnb's 4.5-year Bazel migration required a dedicated build-infra team. Budget accordingly or choose a lower-complexity tool.

### Structure

| Signal | Structure |
|---|---|
| Teams organized by product domain | Domain-first |
| Teams organized by language expertise | Language-first |
| Mixed team topology, rapid growth | Hybrid (apps/services/packages/proto) |
| Existing repos being merged | Match existing team topology, migrate later |

Default to Protocol Buffers with buf.build for service-to-service contracts and OpenAPI for external REST APIs. Ad-hoc JSON contracts without schema validation become maintenance liabilities as the codebase grows.

For workspace manager configuration (Go workspaces, Python uv workspaces, pnpm workspaces), see `references/workspace-managers.md`. For CI/CD pipeline patterns, see `references/ci-cd-patterns.md`.
