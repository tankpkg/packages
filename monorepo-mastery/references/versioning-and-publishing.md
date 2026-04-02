# Versioning and Publishing

Sources: Changesets docs, Lerna docs, semantic-release docs, npm docs, 2024-2026 publishing patterns

Covers: versioning strategies, Changesets workflow, Lerna v7+ publishing, semantic-release, publishing targets (npm/PyPI/crates.io/Docker), dependency management tools, anti-patterns.

## Versioning Strategies

Three strategies exist for versioning packages in a monorepo. The choice shapes your release tooling, changelog structure, and consumer expectations.

### Independent Versioning

Each package maintains its own version number. `@myorg/ui` can be at `3.1.0` while `@myorg/utils` is at `1.4.2`. This is the dominant pattern for library monorepos where packages are consumed independently.

**When to use:** Library collections, design systems, utility packages, any repo where consumers install individual packages rather than the whole suite.

**Tooling:** Changesets (default mode), Lerna with `--independent` flag, multi-semantic-release.

### Fixed/Locked Versioning

All packages share a single version number. When you release `2.0.0`, every package in the repo publishes at `2.0.0` regardless of whether it changed. Angular, Babel, and Jest use this model.

**When to use:** Frameworks where all packages must be used together, repos where version skew between packages causes bugs, teams that want a single "release train" to communicate.

**Tooling:** Lerna (default mode), Changesets with `fixed` groups covering all packages.

### Hybrid Versioning

Groups of packages share a version while other groups version independently. For example, `@myorg/react-*` packages all move together, but `@myorg/cli` versions independently.

**When to use:** Repos with distinct product lines that have different release cadences, or where some packages are tightly coupled and others are standalone utilities.

**Tooling:** Changesets `fixed` groups in `.changeset/config.json`, Lerna with selective grouping.

### Strategy Comparison

| Criterion | Independent | Fixed | Hybrid |
|-----------|-------------|-------|--------|
| Consumer clarity | High — each package has its own history | Medium — one version for everything | Medium — depends on grouping |
| Release complexity | High — many versions to track | Low — one version | Medium |
| Changelog granularity | Per-package | Single combined | Per-group |
| Best for | Library collections | Frameworks, tightly coupled suites | Mixed repos |
| Tooling complexity | Medium | Low | High |

## Changesets

Changesets is the 2026 standard for JS/TS monorepo versioning, with 2.2M weekly npm downloads. Its core insight: capture intent at contribution time, not at release time.

### How Changesets Work

A changeset is a markdown file in `.changeset/` that records which packages changed and by how much (patch/minor/major). Contributors create changesets when they open PRs. At release time, the tool consumes all accumulated changesets, bumps versions, and generates changelogs.

This separates two concerns that other tools conflate: "what changed and why" (captured by contributors) versus "when to release" (decided by maintainers).

### Workflow

**1. Initialize**

```bash
pnpm add -D @changesets/cli
pnpm changeset init
```

**2. Contributor adds a changeset**

```bash
pnpm changeset add
# Interactive: select packages, select bump type, write summary
```

This creates a file like `.changeset/purple-dogs-eat.md`:

```markdown
---
"@myorg/button": minor
"@myorg/theme": patch
---

Add `size` prop to Button; update theme tokens to match.
```

Commit this file alongside the code change. The changeset file travels with the PR.

**3. Changesets accumulate** — multiple PRs each add their own changeset files. No version bumps happen yet.

**4. Release**

```bash
pnpm changeset version   # bumps package.json versions, updates CHANGELOG.md, deletes changeset files
pnpm changeset publish   # runs npm publish for every package whose version changed
```

### Config: `.changeset/config.json`

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "restricted",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

Key fields:

| Field | Purpose | Common values |
|-------|---------|---------------|
| `access` | npm publish access | `"public"` for scoped public packages, `"restricted"` for private |
| `fixed` | Package groups that share a version | `[["@myorg/react-*"]]` |
| `updateInternalDependencies` | How to bump internal deps when a dep releases | `"patch"` or `"minor"` |
| `ignore` | Packages never published | Private apps, internal tooling |

### GitHub Actions Automation

The `changesets/action` bot automates the release loop. On every push to `main`, it either opens a "Version Packages" PR (if changesets are pending) or publishes (if the Version PR was merged).

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: https://registry.npmjs.org
      - run: pnpm install --frozen-lockfile
      - uses: changesets/action@v1
        with:
          publish: pnpm changeset publish
          version: pnpm changeset version
          commit: "chore: version packages"
          title: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Snapshot Releases

For pre-release testing without bumping the main version:

```bash
pnpm changeset version --snapshot canary
pnpm changeset publish --tag canary
# Publishes as 0.0.0-canary-20260312120000
```

Consumers install with `pnpm add @myorg/button@canary`.

## Lerna v7+ Publishing

Lerna is the most mature npm publishing workflow for monorepos, now maintained by Nx. Version 7+ dropped its own task runner in favor of Nx or Turborepo, focusing on versioning and publishing.

### Conventional Commits Integration

Lerna reads conventional commit messages to determine version bumps automatically:

| Commit prefix | Version bump |
|---------------|-------------|
| `fix:` | patch |
| `feat:` | minor |
| `feat!:` or `BREAKING CHANGE:` | major |
| `chore:`, `docs:`, `style:` | no bump |

Enable in `lerna.json`:

```json
{
  "version": "independent",
  "conventionalCommits": true,
  "changelogPreset": "angular",
  "npmClient": "pnpm",
  "useWorkspaces": true,
  "createRelease": "github"
}
```

### Version and Publish Commands

```bash
# Determine version bumps from commits, update package.json files, create git tags
lerna version --conventional-commits

# Publish all packages that have changed since last release
lerna publish from-git

# Combined: version + publish in one step
lerna publish --conventional-commits
```

**`from-git` vs `from-package`:**

- `from-git`: publishes packages whose git tags don't match npm. Reliable when tags are authoritative.
- `from-package`: publishes packages whose `package.json` version isn't on npm. Use when tags are unreliable or in CI environments without full git history.

## semantic-release and multi-semantic-release

semantic-release automates the entire release process from commit messages with no manual version decisions. It runs in CI, analyzes commits since the last release, determines the version bump, publishes, and creates GitHub releases.

### Plugin System

semantic-release is plugin-driven. The default plugin chain:

| Plugin | Role |
|--------|------|
| `@semantic-release/commit-analyzer` | Reads commits, determines bump type |
| `@semantic-release/release-notes-generator` | Generates changelog content |
| `@semantic-release/changelog` | Writes `CHANGELOG.md` |
| `@semantic-release/npm` | Bumps `package.json`, runs `npm publish` |
| `@semantic-release/git` | Commits version bump back to repo |
| `@semantic-release/github` | Creates GitHub release with notes |

Configure in `.releaserc.json` with `branches` (supports `beta` pre-release channels) and a `plugins` array listing the chain above.

### multi-semantic-release

`multi-semantic-release` extends semantic-release to monorepos. It runs semantic-release for each package, respects internal dependencies (if `@myorg/utils` releases, packages that depend on it get a patch bump), and handles topological ordering.

Install with `pnpm add -D multi-semantic-release` and run from the repo root — it discovers packages via workspaces config.

**When to prefer over Changesets:** When you need fully automated releases with no human PR review step. Changesets requires a human to merge the Version PR; multi-semantic-release does not.

## Publishing Targets

### npm

**OIDC Trusted Publishing (2025+ standard):** Eliminates long-lived `NPM_TOKEN` secrets. Configure on npmjs.com under package settings, then publish with:

```bash
npm publish --provenance --access public
```

`--provenance` links the published package to its source commit and CI run. Consumers can verify the package was built from the expected source. Requires GitHub Actions or another supported CI provider.

**Workspace publishing:**

```bash
npm publish --workspaces --access public   # npm workspaces
pnpm -r publish --access public            # pnpm workspaces
```

Always run `npm publish --dry-run` first to confirm the `files` field is correct.

### PyPI

**Trusted Publishing with OIDC:** Configure on pypi.org under the project's Publishing settings. Add the GitHub Actions environment and workflow path. Then in CI:

```yaml
- uses: pypa/gh-action-pypi-publish@release/v1
  # No API token needed — OIDC handles auth
```

**uv publish (2025+):** uv is significantly faster than twine for building and publishing.

```bash
uv build
uv publish   # with trusted publishing, no token needed
```

Each package in a Python monorepo has its own `pyproject.toml`. Build and publish each independently. Tools like `hatch` support workspace-style multi-package repos.

### crates.io

```bash
cargo publish -p my-crate                  # single crate
cargo workspaces publish                   # all crates in dependency order
                                           # (cargo install cargo-workspaces)
cargo publish -p my-crate --dry-run        # verify before publishing
```

Publish dependencies before dependents — `cargo workspaces publish` handles ordering automatically. crates.io does not support OIDC as of 2026; use a `CARGO_REGISTRY_TOKEN` secret.

### Docker and OCI

Build multi-platform images from a monorepo using Docker Buildx:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag myorg/myapp:latest \
  --push \
  -f apps/myapp/Dockerfile \
  .
```

Run `docker build` from the repo root so the Dockerfile can `COPY` from sibling packages:

```dockerfile
COPY packages/shared /app/packages/shared
COPY apps/myapp /app/apps/myapp
```

Tag images with the package version extracted from `package.json`:

```bash
VERSION=$(node -p "require('./apps/myapp/package.json').version")
docker buildx build --tag myorg/myapp:$VERSION --tag myorg/myapp:latest ...
```

## Dependency Management in Monorepos

### Renovate vs Dependabot

| Criterion | Renovate | Dependabot |
|-----------|----------|------------|
| Monorepo awareness | Native — groups related updates | Limited — treats each package independently |
| Package manager support | 90+ managers (npm, pip, cargo, go, docker, helm, ...) | ~20 managers |
| Automerge | Configurable per-package, per-update-type | Basic |
| Update grouping | Flexible — group by scope, type, or regex | Limited |
| Scheduling | Cron-based, configurable | Basic |
| Config location | `renovate.json` or `.github/renovate.json` | `.github/dependabot.yml` |
| Self-hosted | Yes (Mend Renovate) | No |
| Monorepo verdict | Strongly preferred | Adequate for simple repos |

Renovate wins for monorepos because it understands workspace relationships, groups related updates (e.g., all `@testing-library/*` into one PR), and supports automerge for patch updates with passing CI. Configure with `"extends": ["config:recommended"]` and add `packageRules` for grouping and automerge behavior.

### pnpm `workspace:` Protocol

When a package depends on a sibling, use the `workspace:` protocol:

```json
{ "dependencies": { "@myorg/utils": "workspace:*" } }
```

On publish, pnpm replaces `workspace:*` with the actual version number. This replacement happens automatically during `pnpm publish` or `changesets publish`.

| Protocol | Meaning | Replaced with on publish |
|----------|---------|--------------------------|
| `workspace:*` | Any version in workspace | Exact version (`1.2.3`) |
| `workspace:^` | Any compatible version | `^1.2.3` |
| `workspace:~` | Patch-compatible version | `~1.2.3` |

Use `workspace:*` for internal dependencies — it ensures you always test against the local version, and consumers get a pinned range on publish.

### pnpm Overrides

Force a specific version of a transitive dependency across the entire monorepo:

```json
{
  "pnpm": {
    "overrides": {
      "lodash": "^4.17.21",
      "semver@<7.5.2": "^7.5.2"
    }
  }
}
```

Use overrides to patch security vulnerabilities before upstream fixes land, deduplicate packages at multiple versions, or pin a dep with a broken release.

### Nx Module Boundaries

`@nx/enforce-module-boundaries` is an ESLint rule that enforces architectural constraints between packages. Tag projects in `project.json` with `"tags": ["scope:lib", "type:ui"]`, then define `depConstraints` in the ESLint config:

- `scope:app` can only depend on `scope:lib` and `scope:shared`
- `scope:lib` can only depend on `scope:shared`
- `type:feature` can only depend on `type:ui`, `type:data-access`, `type:util`

This prevents apps from importing other apps, enforces layered architecture, and catches circular dependencies at lint time rather than runtime.

### Sherif

Sherif enforces consistency rules across all `package.json` files. Run `pnpm sherif` to catch:

| Rule | What it catches |
|------|----------------|
| `root-package-manager-field` | Missing `packageManager` field in root |
| `packages-without-name` | Packages missing the `name` field |
| `duplicate-dependency` | Same dep at different versions across packages |
| `packages-without-description` | Published packages missing description |
| `non-existant-packages` | Workspace globs that match no directories |

Run Sherif in CI to prevent version drift and configuration inconsistency from accumulating.

## Anti-Patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Manual version bumps | Error-prone, inconsistent, no changelog | Use Changesets, Lerna, or semantic-release |
| Publishing without building | Consumers get source, not dist | Add `"prepublishOnly": "pnpm build"` to each package |
| Forgetting to publish dependents | `@myorg/button` releases but `@myorg/form` (which depends on it) doesn't | Use `updateInternalDependencies` in Changesets; Lerna handles this automatically |
| No changelog | Consumers can't understand what changed | Changesets and Lerna both generate `CHANGELOG.md` automatically |
| Inconsistent versions across packages | Same dep at 1.0.0 in one package, 2.0.0 in another | Sherif `duplicate-dependency` rule; Renovate grouping |
| Publishing from local machine | Unpredictable environment, no audit trail | Publish only from CI; use OIDC trusted publishing |
| Missing `files` field | Entire repo contents published to npm | Set `"files": ["dist", "README.md"]` in every published package |
| `workspace:*` left in published package | Consumers can't install — not a valid npm range | pnpm replaces it automatically; verify with `--dry-run` |
| No pre-release channel | Breaking changes go straight to stable | Use Changesets snapshots or semantic-release `beta` branch |
| Circular internal dependencies | Build order undefined, version bumps cascade infinitely | Enforce with `@nx/enforce-module-boundaries`; detect with `madge` |

## Release Checklist

Before any publish run, verify:

1. All tests pass on the target branch.
2. `pnpm changeset status` (or `lerna changed`) shows expected packages.
3. `npm publish --dry-run` (or equivalent) shows expected files.
4. `files` field in `package.json` excludes test files, source maps (unless intentional), and internal tooling.
5. Internal `workspace:` dependencies will be replaced — confirm with dry run output.
6. Registry credentials are valid (token not expired, OIDC configured).
7. Git tag will be created — confirm tag format matches what CI expects for `from-git` publishing.
