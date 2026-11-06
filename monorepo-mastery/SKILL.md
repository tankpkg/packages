---
name: "@tank/monorepo-mastery"
description: "Monorepo architecture, tooling, and operations for any language or scale. Covers orchestrator selection (Nx, Turborepo, Bazel, Rush, Moon, Pants, Buck2), workspace managers (pnpm, Cargo, Go, uv, Gradle), polyglot patterns, CI/CD optimization, scaling, migration, and versioning. Triggers: monorepo, Nx, Turborepo, Bazel, Rush, Moon, Pants, pnpm workspaces, cargo workspaces, go.work, polyglot monorepo, affected builds, remote cache, changesets, monorepo CI, monorepo migration, sparse checkout."
---

# Monorepo Mastery

Architect, build, and operate monorepos at any scale, in any language.

## Core Philosophy

1. **Tooling is the entire game.** A monorepo without proper tooling is
   worse than polyrepo. Invest in orchestration, caching, and affected
   detection before scaling.
2. **Start simple, scale deliberately.** Begin with a workspace manager +
   lightweight orchestrator. Add complexity only when CI time or team size
   demands it.
3. **Affected-only everything.** Build, test, lint, and deploy only what
   changed. Full pipeline runs on every PR are the number one monorepo
   anti-pattern.
4. **Cache aggressively, invalidate precisely.** Content-addressed caching
   with correct input hashing is the foundation of monorepo performance.
5. **Boundaries prevent chaos.** Enforce module boundaries, dependency
   direction, and ownership rules from day one. Architectural drift in a
   monorepo is exponentially harder to fix than in polyrepo.

## Quick-Start

### "I need to set up a new monorepo"

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Detect existing signals (package.json, Cargo.toml, go.mod, etc.) | This file |
| 2 | Choose workspace manager for your language(s) | `references/workspace-managers.md` |
| 3 | Choose orchestrator based on scale and language needs | `references/tool-selection.md` |
| 4 | Configure CI with affected-only builds and caching | `references/ci-cd-patterns.md` |
| 5 | Set up versioning and publishing if needed | `references/versioning-and-publishing.md` |

### "My monorepo CI is too slow"

| Step | Action |
|------|--------|
| 1 | Enable affected-only builds (Nx affected, Turbo --filter, Pants --changed-since) |
| 2 | Add remote caching (Vercel Remote Cache, Nx Cloud, Bazel RE API) |
| 3 | Optimize git operations (shallow clone, sparse checkout) |
| 4 | Parallelize independent tasks |
-> See `references/scaling-and-performance.md` and `references/ci-cd-patterns.md`

### "I want to consolidate polyrepos into a monorepo"

| Step | Action |
|------|--------|
| 1 | Audit repos: dependencies, CI, ownership |
| 2 | Choose migration strategy (git subtree, git-filter-repo, strangler fig) |
| 3 | Set up target monorepo with workspace config |
| 4 | Migrate incrementally, one repo at a time |
| 5 | Verify CI parity before cutting over |
-> See `references/migration-guide.md`

### "I have a multi-language monorepo"

| Step | Action |
|------|--------|
| 1 | Choose repo structure pattern (domain-first, language-first, hybrid) |
| 2 | Set up cross-language contracts (protobuf, OpenAPI) |
| 3 | Choose polyglot orchestrator (Bazel, Pants, Moon) |
| 4 | Configure shared tooling (Lefthook, .editorconfig, CODEOWNERS) |
-> See `references/polyglot-patterns.md`

## Project Detection

Before recommending tools, check for existing signals:

| Signal | Indicates | Files to Check |
|--------|-----------|----------------|
| `turbo.json` | Turborepo | root |
| `nx.json` | Nx | root |
| `rush.json` | Rush | root |
| `.moon/workspace.yml` | Moon | `.moon/` |
| `pants.toml` | Pants | root |
| `MODULE.bazel` or `WORKSPACE` | Bazel | root |
| `pnpm-workspace.yaml` | pnpm workspaces | root |
| `Cargo.toml` with `[workspace]` | Cargo workspaces | root |
| `go.work` | Go workspaces | root |
| `[tool.uv.workspace]` | uv workspaces | `pyproject.toml` |
| `settings.gradle.kts` with `include` | Gradle multi-project | root |

## Decision Trees

### Orchestrator Selection (Quick)

| Signal | Recommendation |
|--------|---------------|
| JS/TS only, <20 packages, want simplicity | Turborepo |
| JS/TS, 20+ packages, need code gen + plugins | Nx |
| JS/TS enterprise, strict dep governance | Rush |
| Publishing many npm packages | Lerna (or Changesets) |
| Python-heavy, with Go/Java/Docker | Pants |
| JS/TS + Rust/Go/Python, medium scale | Moon |
| True polyglot, 100+ engineers | Bazel |
| Meta ecosystem, maximum extensibility | Buck2 |
| JVM only (Java/Kotlin/Scala) | Gradle |

### Workspace Manager Selection (JS)

| Signal | Recommendation |
|--------|---------------|
| Default for new projects 2026 | pnpm |
| Need zero-install, offline CI | Yarn Berry (PnP) |
| Fastest runtime + manager | Bun |
| Minimal setup, small team | npm |

### Versioning Strategy

| Signal | Strategy |
|--------|----------|
| Libraries consumed independently | Independent (Changesets) |
| Framework with tight coupling | Fixed/locked (Lerna) |
| Mix of both | Hybrid (grouped Changesets) |

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Run all tests on every PR | Use affected detection | CI time scales linearly with repo size |
| Skip remote caching | Enable from day one | Local-only caching wastes CI compute |
| Allow unrestricted imports | Enforce module boundaries | Prevents spaghetti dependencies |
| Manual version bumps | Use Changesets or conventional commits | Human error, forgotten changelogs |
| Full git clone in CI | Shallow clone + sparse checkout | Clone time dominates in large repos |
| One giant package | Split by domain/concern | Defeats purpose of monorepo tooling |

## Reference Files

| File | Contents |
|------|----------|
| `references/tool-selection.md` | Orchestrator comparison (Nx, Turborepo, Bazel, Rush, Moon, Pants, Buck2, Gradle), decision matrices, feature comparison, migration complexity |
| `references/workspace-managers.md` | Workspace managers for all languages (pnpm, npm, Yarn, Bun, Cargo, Go, uv, Gradle, .NET, CMake/Conan), config examples, comparison tables |
| `references/polyglot-patterns.md` | Multi-language repo structure, cross-language deps (protobuf, OpenAPI), shared tooling, CODEOWNERS, real-world examples (Google, Meta, Uber) |
| `references/ci-cd-patterns.md` | GitHub Actions, GitLab CI, CircleCI monorepo patterns, affected-only CI, remote caching setup, merge queues, workflow examples |
| `references/scaling-and-performance.md` | Git performance (sparse checkout, Scalar, Sapling), build caching, affected detection algorithms, incremental builds, scale thresholds |
| `references/migration-guide.md` | Polyrepo-to-monorepo (git subtree, git-filter-repo), monorepo-to-polyrepo extraction, tool migrations, incremental migration strategy |
| `references/versioning-and-publishing.md` | Changesets, Lerna, semantic-release, publishing to npm/PyPI/crates.io, dependency management (Renovate, Sherif, module boundaries) |
