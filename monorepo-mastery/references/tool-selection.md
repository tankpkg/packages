# Monorepo Tool Selection

Sources: monorepo.tools, Nx docs (2026), Turborepo docs (2026), Bazel docs, 2024-2026 ecosystem research

Covers: orchestrator/build tool selection, feature comparison, decision matrix, migration complexity, anti-patterns.

## Orchestrator Landscape

Monorepo orchestrators handle task scheduling, caching, and affected-package detection. They sit above package managers (pnpm/npm/yarn/bun) and below CI systems. Choose the orchestrator first; workspace manager second.

### Nx v22

**Stars:** 25K | **npm:** ~36M/month | **Language:** TypeScript/Rust internals

Nx is the most feature-complete orchestrator in the JS ecosystem. It ships a plugin ecosystem covering React, Angular, Next.js, Node, Vite, .NET, and Maven, making it viable for polyglot shops that still center on JS/TS. Computation caching stores task outputs locally and remotely (Nx Cloud). Affected detection traces the dependency graph to run only tasks impacted by a change. Code generation via `nx generate` scaffolds libraries, components, and configurations. Distributed Task Execution (DTE) splits CI work across agents. Nx Console provides IDE integration for VS Code and JetBrains. Self-Healing CI automatically retries flaky tasks and adjusts agent allocation. Polygraph visualizes cross-project dependencies. TypeScript project references are managed automatically.

**Ideal for:** Large JS/TS monorepos, teams that want batteries-included tooling, organizations already using Angular or React at scale, shops that need code generation and enforced module boundaries.

**Limitations:** Steep learning curve — the mental model of executors, generators, and project graph takes time. Configuration is heavy; `project.json` files proliferate. Nx Cloud is proprietary; self-hosted remote cache requires extra setup. Upgrades between major versions can be disruptive.

### Turborepo v2.8

**Stars:** 30K | **npm:** ~1.2M/week | **Language:** Rust

Turborepo optimizes for simplicity. A single `turbo.json` defines the pipeline; Rust internals make it fast. The Terminal UI renders task output cleanly. Devtools (browser-based) visualize task timelines. Microfrontend support and package boundaries (enforced via `boundaries`) are first-class. Sidecar tasks run alongside primary tasks (e.g., a dev server alongside a test watcher). Watch mode re-runs tasks on file change. Bun is a supported package manager. An Agent Skill integrates with AI coding assistants.

**Ideal for:** JS/TS-only repos that want minimal configuration, teams migrating from a single-package repo, projects where simplicity and fast onboarding matter more than code generation.

**Limitations:** JS/TS only — no native support for Go, Rust, Python, or Java workspaces. No code generation. No plugin ecosystem. No distributed execution (remote cache via Vercel or self-hosted, but no agent-based DTE). Smaller feature surface than Nx.

### Bazel v7+

**Stars:** 23K | **Origin:** Google | **Language:** Java/Starlark

Bazel delivers hermetic, reproducible builds. Every action runs in a sandbox with declared inputs and outputs, so the same source always produces the same artifact. Native polyglot support covers C++, Java, Python, Go, Rust, JavaScript, and Swift through rulesets. Remote caching and remote execution (RE API) distribute work across a build cluster. `bzlmod` (module system) replaces `WORKSPACE` for dependency management. The query language (`bazel query`, `bazel cquery`, `bazel aquery`) answers dependency and action graph questions precisely.

**Ideal for:** Large polyglot repos where reproducibility and hermetic builds are non-negotiable, organizations with dedicated build engineering teams, C++/Java/Go shops that need fine-grained caching at the file level.

**Limitations:** Extreme complexity. BUILD file maintenance is a full-time concern. Rulesets vary in quality and maintenance. Onboarding takes weeks. Debugging sandbox failures requires deep knowledge. Not appropriate for small teams or JS-only repos.

### Rush v5

**Stars:** 5.5K | **Origin:** Microsoft | **Language:** TypeScript

Rush is purpose-built for large JS/TS monorepos with strict dependency hygiene. It enforces pnpm-only (phantom dependency detection catches undeclared imports). Versioning and publishing workflows are first-class: `rush change`, `rush publish`, and `rush version` handle changelogs and npm releases. Phased builds define explicit task phases with dependencies. Subspaces partition the repo into isolated pnpm workspaces within a single repo. Cobuild distributes CI work across agents.

**Ideal for:** JS/TS monorepos where phantom dependency detection and structured publishing workflows are priorities, Microsoft-ecosystem shops, teams that need strict pnpm enforcement.

**Limitations:** JS/TS only. Smaller community than Nx or Turborepo. Less ecosystem tooling. Configuration is verbose. Cobuild requires Azure DevOps or custom infrastructure.

### Lerna v8

**Stars:** 35K (historical) | **Maintainer:** Nx team | **Language:** TypeScript

Lerna is the oldest JS monorepo tool. Since the Nx team took over maintenance, Lerna v8 runs Nx under the hood for task orchestration. Its primary value is the most mature npm publishing workflow in the ecosystem: `lerna publish`, `lerna version`, conventional commits integration, and per-package changelogs. Teams already on Lerna can adopt Nx incrementally.

**Ideal for:** Teams with existing Lerna repos that need a migration path to Nx, projects where the Lerna publishing API is deeply embedded in CI scripts.

**Limitations:** Essentially Nx with a Lerna API layer. New projects should start with Nx directly. The Lerna-specific features beyond publishing are superseded by Nx.

### Moon v2

**Stars:** 3.5K | **Language:** Rust | **Polyglot:** JS/TS/Rust/Go/Python/PHP/Ruby/Deno/Bun

Moon is a Rust-based task runner with broad language support. The `proto` toolchain manager installs and pins language runtimes (Node, Bun, Deno, Python, Go, Rust) per project. WASM plugins extend Moon's language support without recompiling the core. Task inheritance lets child projects extend parent task definitions.

**Ideal for:** Polyglot repos that need runtime version management alongside task orchestration, teams that want Turborepo-like simplicity with broader language coverage.

**Limitations:** Smaller community and ecosystem than Nx or Turborepo. Fewer integrations. Remote caching is available but less mature than Nx Cloud or Turborepo's Vercel integration.

### Pants v2

**Stars:** 3.5K | **Language:** Python/Rust | **Focus:** Python-first polyglot

Pants infers dependencies automatically by parsing import statements — no BUILD file maintenance for most cases. Fine-grained caching operates at the file level. PEX packaging produces self-contained Python executables. Compatible with the Bazel Remote Execution API for distributed builds. Supports Python, Go, Java, Scala, Shell, Docker, and Terraform.

**Ideal for:** Python-heavy polyglot repos, data engineering and ML monorepos, teams that want Bazel-level caching without Bazel's BUILD file burden.

**Limitations:** Python-first — other language support is less mature. Smaller community than Bazel. Less tooling for JS/TS workloads.

### Buck2

**Stars:** 3.8K | **Origin:** Meta | **Language:** Rust/Starlark

Buck2 is Meta's successor to Buck1, rewritten in Rust. It uses Starlark (a Python dialect) for BUILD files, the same language as Bazel. BXL (Buck eXtension Language) enables custom build graph queries and actions. Claimed 2x faster than Buck1 on Meta's internal benchmarks.

**Ideal for:** Organizations already invested in Meta's toolchain, teams that need Bazel-like semantics with better performance, shops with dedicated build engineering capacity.

**Limitations:** Meta-centric — rulesets and integrations reflect Meta's internal stack. Smaller external community than Bazel. Documentation assumes familiarity with Buck1 or Bazel concepts.

### Gradle Composite Builds

**Stars:** 17K | **Language:** Groovy/Kotlin | **Focus:** JVM

Gradle's composite builds link multiple Gradle projects into a single build. Configuration cache stores the build configuration graph for fast incremental builds. Version catalogs (`libs.versions.toml`) centralize dependency versions. Kotlin DSL is the modern build script format.

**Ideal for:** JVM monorepos (Java, Kotlin, Scala, Android), organizations standardized on Gradle, Android multi-module apps.

**Limitations:** JVM-centric. JS/TS support exists but is not idiomatic. Build script complexity grows with repo size. Configuration cache has known incompatibilities with some plugins.

## Feature Comparison

| Feature | Nx | Turborepo | Bazel | Rush | Lerna | Moon | Pants | Buck2 | Gradle |
|---------|-----|-----------|-------|------|-------|------|-------|-------|--------|
| Local caching | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Remote caching | Nx Cloud / self | Vercel / self | RE API | Azure / self | Nx Cloud | Self | RE API | RE API | Build Scan |
| Distributed execution | Yes (DTE) | No | Yes (RE) | Yes (Cobuild) | Yes (DTE) | No | Yes (RE) | Yes (RE) | No |
| Affected detection | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Partial |
| Code generation | Yes | No | No | No | No | No | No | No | No |
| Plugin ecosystem | Yes | No | Yes (rulesets) | No | No | WASM | No | No | Yes |
| IDE integration | Nx Console | No | IntelliJ | No | No | No | No | No | IntelliJ |
| Polyglot | Partial | No | Yes | No | No | Yes | Yes | Yes | JVM |
| Dependency graph UI | Yes | Devtools | No | No | No | No | No | No | No |
| Module boundaries | Yes | Yes | Yes | Yes | No | No | No | No | No |
| Watch mode | Yes | Yes | No | No | No | Yes | No | No | No |
| Runtime version mgmt | No | No | No | No | No | Yes (proto) | No | No | No |
| Auto dep inference | No | No | No | No | No | No | Yes | No | No |
| Hermetic builds | No | No | Yes | No | No | No | Partial | Yes | No |

## Decision Matrix

| Signal | Recommended Tool |
|--------|-----------------|
| JS/TS only, want simplicity, small-to-mid team | Turborepo |
| JS/TS only, need code generation and module boundaries | Nx |
| JS/TS only, need strict publishing workflow and phantom dep detection | Rush |
| Existing Lerna repo, want incremental Nx adoption | Lerna v8 |
| Polyglot (JS + Go/Rust/Python), want simple config | Moon |
| Python-heavy polyglot, want auto dep inference | Pants |
| Large polyglot, need hermetic reproducible builds, have build engineers | Bazel |
| Meta-stack or Buck1 migration | Buck2 |
| JVM monorepo (Java/Kotlin/Android) | Gradle Composite |
| Need distributed execution in JS/TS | Nx (DTE) or Rush (Cobuild) |
| Need IDE integration for JS/TS | Nx (Nx Console) |
| Need runtime version pinning per project | Moon (proto) |
| Regulated environment requiring bit-for-bit reproducibility | Bazel or Buck2 |
| Team < 5 engineers, single language | Turborepo or npm/pnpm workspaces alone |

## Quick Selection

Work through these conditions in order. Stop at the first match.

1. **JVM-primary repo** (Java/Kotlin/Scala/Android) -> Gradle Composite Builds.
2. **Python-primary polyglot** (data, ML, backend Python) -> Pants.
3. **Hermetic builds required** (regulated, reproducibility SLA) -> Bazel.
4. **Meta/Buck ecosystem** -> Buck2.
5. **Polyglot with runtime version management** (JS + Go/Rust/Python) -> Moon.
6. **JS/TS, need publishing workflow + phantom dep detection** -> Rush.
7. **JS/TS, existing Lerna investment** -> Lerna v8 (then migrate to Nx).
8. **JS/TS, need code generation, module boundaries, IDE integration** -> Nx.
9. **JS/TS, want minimal config, fast onboarding** -> Turborepo.
10. **Repo < 10 packages, single language** -> Consider workspace scripts before adding an orchestrator.

## Migration Complexity

| From | To | Effort | Key Steps |
|------|----|--------|-----------|
| No orchestrator | Turborepo | Low (1-2 days) | Add `turbo.json`, define pipeline, enable remote cache |
| No orchestrator | Nx | Medium (3-5 days) | `nx init`, configure project graph, adopt executors incrementally |
| Lerna v7 | Lerna v8 / Nx | Low (1 day) | Upgrade package, Nx is auto-configured |
| Turborepo | Nx | Medium (1-2 weeks) | Map `turbo.json` pipeline to `nx.json` targets, adopt project graph |
| Nx | Turborepo | Medium (1-2 weeks) | Lose code gen and module boundaries; map executors to scripts |
| npm/yarn workspaces | Rush | High (1-3 weeks) | Migrate to pnpm, adopt Rush config, rewrite CI |
| Gulp/Grunt | Bazel | Very High (months) | Write BUILD files for every package, train team, set up RE |
| Bazel | Pants | High (weeks) | Rewrite BUILD files in Pants format, validate dep inference |
| Any JS tool | Bazel | Very High (months) | Full BUILD file authoring, sandbox debugging, RE infrastructure |

Incremental adoption reduces risk. Nx and Turborepo both support adding orchestration to existing repos without restructuring packages.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|-------------|-------------|-----------------|
| Choosing Bazel for a JS-only repo | Complexity far exceeds benefit; BUILD file maintenance consumes engineering time | Use Nx or Turborepo; adopt Bazel only when polyglot hermetic builds are required |
| Using Lerna v7 (unmaintained) | No active maintenance; security and compatibility risks | Upgrade to Lerna v8 or migrate to Nx |
| Picking Nx for a 3-package repo | Overhead exceeds value at small scale | Use Turborepo or workspace scripts until the repo grows |
| Mixing orchestrators in one repo | Conflicting caching strategies, duplicate config, confused CI | Pick one orchestrator per repo |
| Skipping remote cache setup | Local cache only; CI gets no benefit from prior runs | Configure remote cache on day one; it is the primary CI speedup |
| Treating orchestrator as package manager | Orchestrators schedule tasks; package managers install dependencies | Use pnpm/npm/yarn/bun for installs; orchestrator for task execution |
| Adopting Rush without pnpm | Rush requires pnpm; retrofitting is painful | Migrate to pnpm before adopting Rush |
| Choosing tool by GitHub stars alone | Stars reflect historical popularity, not current fit | Evaluate against your language stack, team size, and feature requirements |
| Ignoring distributed execution needs | Local caching alone does not scale CI past ~50 packages | Plan for DTE (Nx), Cobuild (Rush), or RE API (Bazel/Pants) early |
| Over-configuring Turborepo | Adding complexity to compensate for missing features | If you need code gen or module boundaries, switch to Nx rather than hacking Turborepo |

## Caching Architecture Comparison

| Tool | Cache Key Inputs | Cache Granularity | Remote Cache Options |
|------|-----------------|-------------------|---------------------|
| Nx | Source files, env vars, task config | Per task | Nx Cloud, self-hosted (S3/GCS/Azure) |
| Turborepo | Source files, env vars, pipeline config | Per task | Vercel Remote Cache, self-hosted |
| Bazel | All declared inputs (hermetic) | Per action | RE API (BuildBuddy, EngFlow, RBE) |
| Rush | Source files, task config | Per task | Azure Blob, custom |
| Moon | Source files, env vars | Per task | Self-hosted |
| Pants | Source files, tool versions | Per target | RE API |
| Gradle | Source files, task inputs | Per task | Gradle Build Cache (local/remote) |

Cache hit rates above 80% in CI require: consistent environment variables, pinned tool versions, and remote cache configured before the first CI run.

## Ecosystem Maturity

| Tool | Release Cadence | Breaking Changes | LTS Policy | Corporate Backing |
|------|----------------|-----------------|------------|------------------|
| Nx | Monthly minor, annual major | Migrations provided | No formal LTS | Nrwl / Nx Inc. |
| Turborepo | Frequent minor | Low | No | Vercel |
| Bazel | Quarterly | Moderate | LTS releases | Google |
| Rush | Quarterly | Low | No | Microsoft |
| Lerna | Aligned with Nx | Low | No | Nx Inc. |
| Moon | Monthly | Low | No | moonrepo |
| Pants | Monthly | Moderate | No | Pants Build community |
| Buck2 | Continuous | High | No | Meta |
| Gradle | Quarterly | Low | No | Gradle Inc. |

## Nx vs Turborepo: The Common Decision

Most JS/TS teams face this choice. The decision hinges on three axes: feature needs, team capacity, and configuration tolerance.

### Choose Nx when

- The repo has 20+ packages and the dependency graph needs visualization.
- Teams need `nx generate` to scaffold consistent library and component structure.
- Module boundary enforcement (`@nx/enforce-module-boundaries`) is required to prevent circular imports or cross-domain coupling.
- Distributed Task Execution is needed — Turborepo has no equivalent.
- IDE integration (Nx Console) matters for developer experience.
- The stack includes Angular, which has deep Nx integration.
- Self-Healing CI and Polygraph are valued for large CI pipelines.

### Choose Turborepo when

- The repo is JS/TS only and the team values minimal configuration.
- Onboarding speed matters — a new engineer can understand `turbo.json` in an hour.
- The team does not need code generation or enforced module boundaries.
- Vercel hosts the frontend — Vercel Remote Cache integrates with zero config.
- The team wants to avoid Nx Cloud dependency for remote caching.
- Sidecar tasks or watch mode are the primary developer workflow needs.

### Switching cost

Moving from Turborepo to Nx is medium effort (1-2 weeks): map pipeline tasks to Nx targets, adopt the project graph, and optionally add executors. Moving from Nx to Turborepo is also medium effort but involves losing code generation and module boundaries — evaluate whether those features are actively used before migrating.

## Team Size and Tool Fit

| Team Size | Packages | Recommended Starting Point | When to Reconsider |
|-----------|----------|---------------------------|-------------------|
| 1-5 engineers | < 10 | Workspace scripts or Turborepo | When CI takes > 10 min |
| 5-20 engineers | 10-50 | Turborepo or Nx | When affected detection is insufficient |
| 20-100 engineers | 50-200 | Nx with DTE | When BUILD file tooling is needed |
| 100+ engineers | 200+ | Nx, Rush, or Bazel | When hermetic builds or polyglot is required |

Small teams pay a disproportionate configuration tax with Nx or Bazel. Start simple and migrate when the pain of the current tool exceeds the migration cost.

## Configuration Complexity

| Tool | Config Files | Typical Setup Time | Ongoing Maintenance |
|------|-------------|-------------------|---------------------|
| Turborepo | `turbo.json` (1 file) | 1-2 hours | Low |
| Nx | `nx.json` + `project.json` per package | 1-2 days | Medium |
| Rush | `rush.json` + `common/` directory | 2-3 days | Medium |
| Moon | `.moon/workspace.yml` + `moon.yml` per package | 1 day | Low-Medium |
| Pants | `pants.toml` + `BUILD` files (auto-inferred) | 2-5 days | Low (auto-inference) |
| Bazel | `WORKSPACE`/`MODULE.bazel` + `BUILD` per package | Weeks | High |
| Buck2 | `.buckconfig` + `BUCK` per package | Weeks | High |
| Gradle | `settings.gradle.kts` + `build.gradle.kts` per module | 1-3 days | Medium |

Configuration complexity compounds with repo size. Bazel and Buck2 BUILD file counts grow linearly with package count; Pants reduces this through automatic inference.

## Remote Execution vs Remote Caching

These are distinct capabilities that are often conflated.

**Remote caching** stores task outputs in a shared cache. When a task's inputs have not changed, the cached output is downloaded instead of recomputing. This benefits all tools and is the highest-ROI optimization for CI.

**Remote execution** distributes individual build actions across a cluster of workers. This parallelizes work within a single task (e.g., compiling 1000 Java files simultaneously). Only Bazel, Pants, and Buck2 support true remote execution via the RE API. Nx DTE and Rush Cobuild distribute at the task level (different packages), not the action level.

| Capability | Nx | Turborepo | Bazel | Rush | Pants | Buck2 |
|-----------|-----|-----------|-------|------|-------|-------|
| Remote caching | Yes | Yes | Yes | Yes | Yes | Yes |
| Task-level distribution | Yes (DTE) | No | No | Yes (Cobuild) | No | No |
| Action-level remote execution | No | No | Yes (RE API) | No | Yes (RE API) | Yes (RE API) |

For most JS/TS repos, remote caching alone provides 60-90% of the CI speedup. Action-level remote execution is only necessary when individual tasks (compile, test) take more than 5-10 minutes.

## Evaluating a Tool Change

Before committing to a migration, answer these questions:

1. **What is the current CI bottleneck?** Measure before assuming the orchestrator is the problem. Slow CI is often caused by missing remote cache, not the wrong tool.
2. **Which features are actively used?** If code generation is unused in Nx, Turborepo may suffice. If module boundaries are unenforced, they provide no value.
3. **What is the team's configuration tolerance?** A team that struggles to maintain `project.json` files will not succeed with Bazel BUILD files.
4. **Is the pain tool-specific or repo-structural?** Circular dependencies, missing affected detection, and slow installs are often repo structure problems, not orchestrator problems.
5. **What does the migration path look like?** Prefer tools with incremental adoption paths (Nx, Turborepo) over big-bang migrations (Bazel).

Run a proof-of-concept on a branch before committing. Measure CI time, cache hit rate, and developer onboarding time with the new tool before migrating the full repo.

For versioning and publishing workflows (changelogs, npm releases, semantic versioning), see `references/versioning-and-publishing.md`.
For workspace manager selection (pnpm, npm, yarn, bun, Cargo, Go modules), see `references/workspace-managers.md`.
For CI/CD integration patterns (GitHub Actions, GitLab CI, affected-based pipelines), see `references/ci-cd-patterns.md`.
