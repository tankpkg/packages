# Workspace and Package Managers

Sources: pnpm docs (v10), npm docs (v11), Yarn Berry docs (v4), Bun docs (v1.3), Cargo docs, Go docs, uv docs, Gradle docs, .NET docs, CMake/Conan docs, 2024-2026 ecosystem research

Covers: JS/TS workspace managers (pnpm, npm, Yarn Berry, Bun), Rust Cargo workspaces, Go go.work, Python uv, JVM Gradle multi-project, .NET central package management, C/C++ CMake+Conan, comparison tables, decision matrix.

## JavaScript and TypeScript Workspace Managers

### pnpm v10 (Recommended Default, 2026)

pnpm uses a content-addressable store and symlinked `node_modules` that mirror the declared dependency graph. Packages can only import what they declare — phantom dependency access fails at runtime rather than silently at deploy time.

**`pnpm-workspace.yaml`**

```yaml
packages:
  - "apps/*"
  - "packages/*"

catalog:
  react: "^19.0.0"
  typescript: "^5.7.0"
  vitest: "^3.0.0"
```

**Workspace protocol in member `package.json`**

```json
{
  "dependencies": {
    "@myorg/ui": "workspace:*",
    "react": "catalog:"
  }
}
```

`workspace:*` pins to the exact local version; pnpm replaces it with a real semver range on publish. `catalog:` references the version defined in `pnpm-workspace.yaml`, eliminating version drift across packages without a separate tool.

**Key commands**

```bash
pnpm install                          # install all workspaces
pnpm --filter @myorg/ui build         # build one package
pnpm --filter "...@myorg/ui" build    # build package + its dependents
pnpm --filter "@myorg/ui..." build    # build package + its dependencies
pnpm -r exec -- node --version        # run command in every package
pnpm dedupe                           # collapse duplicate lockfile versions
```

**`.npmrc` for strict mode**

```ini
strict-peer-dependencies=true
auto-install-peers=true
shamefully-hoist=false
```

Set `shamefully-hoist=true` only when a package hard-codes `require()` from an undeclared path — treat it as a bug to fix, not a permanent setting.

---

### npm v11

npm ships with Node.js, making it the zero-install option. Workspaces use flat hoisting: all dependencies land in root `node_modules`. Packages can accidentally import undeclared dependencies; the build passes locally but fails in production.

**`package.json`**

```json
{
  "private": true,
  "workspaces": ["apps/*", "packages/*"]
}
```

```bash
npm install                          # install all workspaces
npm run build --workspaces           # run build in every workspace
npm run test -w @myorg/ui            # run test in one workspace
```

Use npm when teams cannot add tooling or when migrating an existing npm project incrementally. For new monorepos, prefer pnpm.

---

### Yarn Berry v4

Yarn Berry replaces `node_modules` with Plug'n'Play (PnP): packages are stored as zip archives and resolved via a generated `.pnp.cjs` loader. Zero-installs means committing the cache to git so CI never runs `yarn install`.

**`.yarnrc.yml`**

```yaml
nodeLinker: pnp
yarnPath: .yarn/releases/yarn-4.x.x.cjs
```

```bash
yarn workspaces foreach -A run build   # build all packages
yarn workspace @myorg/ui add react     # add dep to one package
```

PnP breaks packages that use dynamic `require` with computed paths. Check compatibility at `yarnpkg.com/package/compat-table`. Use `nodeLinker: node-modules` for compatibility at the cost of phantom dep risk.

Zero-installs setup: commit `.yarn/cache` and `.yarn/releases`; add `.yarn/install-state.gz` to `.gitignore`.

---

### Bun v1.3

Bun is a runtime, bundler, test runner, and package manager in one binary. Install speed is 10-30x faster than npm due to native code and parallel I/O. Workspaces use the same `package.json` format as npm.

```json
{
  "private": true,
  "workspaces": ["apps/*", "packages/*"]
}
```

```bash
bun install                          # install all workspaces; lockfile: bun.lock (binary)
bun run --filter @myorg/ui build     # run script in one package
bun run --filter '*' build           # run build in all packages
bun run src/index.ts                 # execute TypeScript natively, no compilation
```

Workspace filtering is less mature than pnpm's graph traversal. Use Bun when the runtime is already Bun or when install speed is a hard constraint.

---

## JS Package Manager Comparison

| Feature | pnpm v10 | npm v11 | Yarn Berry v4 | Bun v1.3 |
|---------|----------|---------|---------------|----------|
| Phantom dep prevention | Strict (symlinks) | None (flat hoist) | Strict (PnP) | None (flat hoist) |
| Install speed | Fast | Slowest | Fast (zero-install) | Fastest |
| Disk usage | Lowest (content store) | High | Low (zip cache) | Medium |
| Config format | `pnpm-workspace.yaml` | `package.json` | `.yarnrc.yml` | `package.json` |
| Lockfile | `pnpm-lock.yaml` (text) | `package-lock.json` | `yarn.lock` | `bun.lock` (binary) |
| Version catalogs | Yes (native) | No | No | No |
| PnP support | No | No | Yes (default) | No |

## JS Package Manager Decision Matrix

| Situation | Recommendation | Reason |
|-----------|---------------|--------|
| New monorepo, no constraints | pnpm v10 | Phantom dep safety, catalogs, speed |
| Existing npm project | npm or migrate to pnpm | Lowest migration cost |
| CI install time is critical | Yarn Berry (zero-install) or Bun | Skip install or fastest install |
| Runtime is Bun | Bun | Unified toolchain |
| Need PnP strict isolation | Yarn Berry | Only manager with PnP |
| Shared version constraints | pnpm (catalogs) | Native catalog support |

---

## Cargo Workspaces (Rust)

Cargo workspaces are the most ergonomic multi-package setup across all ecosystems. A single `Cargo.lock` at the root ensures all crates resolve to identical dependency versions.

**Root `Cargo.toml`**

```toml
[workspace]
resolver = "2"
members = ["crates/core", "crates/api", "crates/cli"]

[workspace.dependencies]
tokio = { version = "1.40", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }

[workspace.package]
version = "0.1.0"
edition = "2021"
```

**Member `Cargo.toml`**

```toml
[package]
name = "my-api"
version.workspace = true
edition.workspace = true

[dependencies]
tokio.workspace = true
my-core = { path = "../core" }
```

`resolver = "2"` enables the feature resolver that avoids unifying features across dependency paths — use it in all new workspaces. `workspace.dependencies` centralizes versions; members opt in with `.workspace = true`.

```bash
cargo build                    # build all members
cargo build -p my-api          # build one crate
cargo test --workspace         # run all tests
cargo add tokio -p my-api      # add dep to one crate
```

---

## Go go.work (Go 1.18+)

`go.work` provides a local development overlay that lets multiple Go modules resolve each other without publishing. Each module retains its own `go.mod` and remains independently publishable.

**`go.work`**

```
go 1.23

use (
    ./services/api
    ./services/worker
    ./pkg/shared
)
```

```bash
go work init ./services/api ./pkg/shared   # create go.work
go work use ./services/worker              # add a module
GOWORK=off go build ./...                  # disable workspace for CI
```

Set `GOWORK=off` in CI to verify each module builds against its declared dependencies, not local overrides. Commit `go.work.sum` (workspace-level checksum database).

---

## Python uv Workspaces (2026 Standard)

uv creates a single virtual environment at the root with all member packages installed as editable installs. It replaces pip, pip-tools, Poetry, and virtualenv in most new projects.

**Root `pyproject.toml`**

```toml
[tool.uv.workspace]
members = ["packages/*", "apps/*"]

[tool.uv.sources]
my-core = { workspace = true }
```

**Member `pyproject.toml`**

```toml
[project]
name = "my-api"
dependencies = ["fastapi>=0.115", "my-core"]

[dependency-groups]
dev = ["pytest>=8.0", "httpx>=0.27"]
```

```bash
uv sync                          # install all members into single .venv
uv sync --package my-api         # install one member and its deps
uv run --package my-api pytest   # run tests in one package's context
uv add fastapi --package my-api  # add dep to one member
uv lock                          # generate uv.lock; commit it
```

`[dependency-groups]` (PEP 735) replaces optional extras for dev dependencies. uv's resolver is 10-100x faster than pip.

---

## Gradle Multi-Project (JVM)

Gradle multi-project builds are the standard for JVM monorepos (Java, Kotlin, Scala). The root `settings.gradle.kts` declares all subprojects; version catalogs centralize dependency versions.

**`settings.gradle.kts`**

```kotlin
rootProject.name = "my-monorepo"
include(":services:api", ":services:worker", ":libs:core")

dependencyResolutionManagement {
    versionCatalogs {
        create("libs") { from(files("gradle/libs.versions.toml")) }
    }
}
```

**`gradle/libs.versions.toml`**

```toml
[versions]
kotlin = "2.1.0"
spring-boot = "3.4.0"

[libraries]
spring-boot-starter = { module = "org.springframework.boot:spring-boot-starter", version.ref = "spring-boot" }

[plugins]
kotlin-jvm = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
```

**Subproject `build.gradle.kts`**

```kotlin
plugins { alias(libs.plugins.kotlin.jvm) }
dependencies {
    implementation(libs.spring.boot.starter)
    implementation(project(":libs:core"))
}
```

Convention plugins in `buildSrc/` or a `build-logic` subproject extract shared build configuration. Type-safe catalog accessors (`libs.spring.boot.starter`) prevent typos at configuration time.

```bash
./gradlew build                        # build all subprojects
./gradlew :services:api:build          # build one subproject
./gradlew :services:api:test --tests "com.example.*"
```

---

## .NET Central Package Management

`Directory.Build.props` applies MSBuild properties to all projects in the directory tree. `Directory.Packages.props` centralizes NuGet package versions across all projects.

**`Directory.Build.props`**

```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

**`Directory.Packages.props`**

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <PackageVersion Include="Microsoft.AspNetCore.OpenApi" Version="9.0.0" />
    <PackageVersion Include="xunit" Version="2.9.0" />
  </ItemGroup>
</Project>
```

**Individual `.csproj`** (no version numbers when CPM is active)

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" />
    <ProjectReference Include="../../libs/Core/Core.csproj" />
  </ItemGroup>
</Project>
```

`.slnx` (Visual Studio 2022 17.10+) replaces `.sln` with a cleaner XML format. Use `VersionOverride` in a project file to pin a specific package version when the central version is incompatible.

---

## C/C++ CMake + Conan

CMake orchestrates the build graph; Conan 2.x manages dependencies. Conan generates CMake integration files that `find_package()` consumes.

**Root `CMakeLists.txt`**

```cmake
cmake_minimum_required(VERSION 3.28)
project(my-monorepo VERSION 1.0.0)
set(CMAKE_CXX_STANDARD 23)

find_package(fmt REQUIRED)
add_subdirectory(libs/core)
add_subdirectory(services/api)
```

**`conanfile.py`**

```python
from conan import ConanFile
from conan.tools.cmake import cmake_layout

class MyMonorepo(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps"

    def requirements(self):
        self.requires("fmt/11.0.2")
        self.requires("spdlog/1.14.1")
```

**Build workflow**

```bash
conan install . --output-folder=build --build=missing
cmake -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake
cmake --build build --parallel
```

Enable `sccache` or `ccache` via `CMAKE_CXX_COMPILER_LAUNCHER` to reduce rebuild time by 60-90% in CI. Standardize configure/build/test invocations with `CMakePresets.json`.

---

## Cross-Language Comparison

| Manager | Language | Shared lockfile | Phantom dep safety | Version centralization |
|---------|----------|-----------------|-------------------|----------------------|
| pnpm v10 | JS/TS | Yes | Strict (symlinks) | Catalogs |
| npm v11 | JS/TS | Yes | None | No |
| Yarn Berry v4 | JS/TS | Yes | Strict (PnP) | No |
| Bun v1.3 | JS/TS | Yes | None | No |
| Cargo | Rust | Yes (root) | Strict | `workspace.dependencies` |
| go.work | Go | Per-module | N/A | No |
| uv | Python | Yes | N/A | `tool.uv.sources` |
| Gradle | JVM | Per-project | N/A | Version catalogs |
| .NET CPM | .NET | Per-project | N/A | `Directory.Packages.props` |
| CMake+Conan | C/C++ | Conan lockfile | N/A | `conanfile.py` |

## Language-to-Manager Quick Reference

| Language | Default Choice | Alternative | Notes |
|----------|---------------|-------------|-------|
| JavaScript/TypeScript | pnpm v10 | Bun (if runtime matches) | Avoid npm for new monorepos |
| Rust | Cargo | — | Only option; highly ergonomic |
| Go | go.work | — | Set `GOWORK=off` in CI |
| Python | uv | — | Replaces Poetry, pip-tools |
| Java/Kotlin | Gradle | Maven (legacy) | Use version catalogs |
| .NET | CPM + Directory.Build.props | — | `.slnx` for modern solution files |
| C/C++ | CMake + Conan 2.x | CMake + vcpkg | Add sccache for CI speed |
