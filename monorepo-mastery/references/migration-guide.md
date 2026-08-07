# Migration Guide

Sources: git-filter-repo docs, git subtree docs, Nx migration guides, 2024-2026 migration case studies

Covers: polyrepo-to-monorepo migration, monorepo-to-polyrepo extraction, tool migration within a monorepo, decision frameworks, pitfall tables, incremental strategies.

## Pre-Migration Checklist

Complete every item before moving a single repository. Skipping steps here causes rework.

- Audit all repos for secrets in history — run `git log --all --full-history -- '*.env'` and purge before migrating
- Confirm CI system supports monorepo path filtering (GitHub Actions `paths:`, GitLab `changes:`, Buildkite `diff`)
- Define workspace root config: `pnpm-workspace.yaml`, `nx.json`, or `turbo.json` committed and tested with a placeholder package
- Establish package naming convention before first import (`@scope/package-name`, no collisions with npm registry)
- Write CODEOWNERS for each incoming package directory — do this before migration so ownership is never ambiguous
- Set up dependency boundary rules (Nx `enforce-module-boundaries`, Turborepo `--filter`) and verify they run in CI
- Agree on a shared lint/format config that all packages will inherit — retrofitting after migration is painful
- Identify circular dependencies in existing repos using `madge` or `depcruise` — resolve before migrating
- Document the rollback plan: which commit SHA to revert to, who approves rollback, how long the window is

## Polyrepo to Monorepo Migration

### Method 1: git subtree add (Simple, Squashed History)

Use when: team does not need per-file blame across the migration boundary, or history is noisy and a clean cut is acceptable.

```bash
# In the monorepo root
git remote add <repo-name> https://github.com/org/<repo-name>.git
git fetch <repo-name> --no-tags

# Import as a subdirectory, squashing all history into one commit
git subtree add --prefix=packages/<repo-name> <repo-name> main --squash

# Remove the remote — it is no longer needed
git remote remove <repo-name>
```

The `--squash` flag collapses the entire imported history into two commits: one merge commit and one squash commit. `git log packages/<repo-name>` will show only those two commits. This is acceptable when the old repo remains archived and searchable.

After import, update the package's `package.json` to use the workspace protocol for internal dependencies:

```bash
# Replace version ranges with workspace references
sed -i 's/"@scope\/shared": ".*"/"@scope\/shared": "workspace:*"/g' packages/<repo-name>/package.json
```

Run the full build and test suite before committing. If it passes, delete the old repo's CI pipelines and redirect its README to the monorepo.

### Method 2: git-filter-repo (Preserves Full History)

Use when: team needs `git blame` and `git log` to work across the migration boundary, or the repo has significant history worth preserving.

Install git-filter-repo first — it is not bundled with git:

```bash
pip install git-filter-repo
# or: brew install git-filter-repo
```

Rewrite the source repo so all its files live under a subdirectory path:

```bash
# Clone a fresh copy — filter-repo rewrites in place and is destructive
git clone --no-local /path/to/source-repo /tmp/source-repo-filtered
cd /tmp/source-repo-filtered

# Move all content under packages/<repo-name>/
git filter-repo --to-subdirectory-filter packages/<repo-name>
```

Fetch and merge the rewritten history into the monorepo:

```bash
cd /path/to/monorepo
git remote add <repo-name>-filtered /tmp/source-repo-filtered
git fetch <repo-name>-filtered --no-tags

# Merge with unrelated histories allowed
git merge --allow-unrelated-histories <repo-name>-filtered/main --no-edit

git remote remove <repo-name>-filtered
```

Verify history is intact:

```bash
git log --oneline packages/<repo-name> | head -20
git blame packages/<repo-name>/src/index.ts | head -10
```

The full commit history from the source repo is now part of the monorepo's graph. Authors, timestamps, and commit messages are preserved.

### Incremental "Strangler Fig" Approach

Migrate one repository at a time rather than all at once. This limits blast radius and lets the team build confidence with the tooling before handling critical packages.

Sequence for each repo:

1. Import the repo using Method 1 or Method 2 above
2. Add the package to the workspace and verify it builds in isolation: `pnpm --filter <package-name> build`
3. Wire up CI path filtering so only changed packages trigger their pipelines
4. Run both the old repo's CI and the monorepo CI in parallel for one sprint — compare results
5. Redirect the old repo's CI to fail with a message pointing to the monorepo
6. Archive the old repo after two weeks of stable monorepo CI

Maintain a migration tracker (a simple markdown table in the monorepo root) listing each repo, its status, and the target migration date. This keeps the team aligned and surfaces blockers early.

```markdown
| Repo | Status | Target Date | Owner |
|------|--------|-------------|-------|
| auth-service | migrated | 2025-01-15 | @alice |
| payment-api | in-progress | 2025-02-01 | @bob |
| analytics | pending | 2025-03-01 | @carol |
```

### Post-Migration Verification

Run these checks after each repo import before declaring it complete:

```bash
# Verify package resolves in workspace
pnpm list --filter <package-name>

# Verify internal dependencies resolve
pnpm --filter <package-name> install --frozen-lockfile

# Verify build passes
pnpm --filter <package-name> build

# Verify tests pass
pnpm --filter <package-name> test

# Verify lint passes with shared config
pnpm --filter <package-name> lint

# Verify no circular dependencies introduced
npx depcruise packages/<package-name>/src --include-only "^packages" --output-type err
```

Check that CODEOWNERS entries resolve to real GitHub teams:

```bash
gh api repos/org/monorepo/codeowners/errors
```

## Monorepo to Polyrepo Extraction

Extract a package when: a team needs independent release cadence, regulatory requirements mandate separate repositories, or a package is being open-sourced.

### Method 1: git subtree split

```bash
# Create a branch containing only the history for packages/<package-name>
git subtree split --prefix=packages/<package-name> -b extract/<package-name>

# Push that branch to a new empty repository
git push git@github.com:org/<new-repo>.git extract/<package-name>:main

# Clean up the local branch
git branch -D extract/<package-name>
```

The new repository contains only commits that touched `packages/<package-name>`. History is preserved but may include merge commits from the monorepo that look odd in isolation.

### Method 2: git-filter-repo --subdirectory-filter

```bash
# Clone the monorepo
git clone --no-local /path/to/monorepo /tmp/extracted-<package-name>
cd /tmp/extracted-<package-name>

# Keep only the subdirectory, rewriting paths to root
git filter-repo --subdirectory-filter packages/<package-name>

# Push to new repository
git remote set-url origin git@github.com:org/<new-repo>.git
git push --force origin main
```

This produces a cleaner history than `git subtree split` — paths are rewritten to root and monorepo-only merge commits are excluded.

After extraction, update the monorepo to consume the extracted package as an external dependency rather than a workspace package. Remove the directory from the monorepo and update all internal references.

### When to Extract vs. When to Keep

| Signal | Extract | Keep |
|--------|---------|------|
| Team deploys independently on different cadence | Yes | |
| Package has external consumers outside the org | Yes | |
| Regulatory audit requires separate access controls | Yes | |
| Package is being open-sourced | Yes | |
| Team shares >50% of dependencies with monorepo | | Yes |
| Package is actively co-developed with other packages | | Yes |
| Extraction would require duplicating shared tooling | | Yes |

## Tool Migration Within a Monorepo

### Lerna to Nx

Lerna 6+ already delegates task running to Nx. If the monorepo uses Lerna 6+, Nx is already installed. The migration is primarily about shifting configuration ownership.

```bash
# Install Nx if not already present
npx nx@latest init

# Nx will detect existing lerna.json and package.json workspaces
# It generates nx.json with inferred targets from package.json scripts
```

Move task configuration from `lerna.json` to `nx.json`:

```json
// nx.json
{
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["{projectRoot}/dist"]
    },
    "test": {
      "dependsOn": ["build"]
    }
  }
}
```

Replace `lerna run build` with `nx run-many -t build` in CI. Verify caching works:

```bash
nx run-many -t build
nx run-many -t build  # Second run should show cache hits
```

Remove `lerna.json` only after all CI pipelines use `nx` commands and the team has validated caching behavior for two weeks.

### Turborepo to Nx

Turborepo and Nx overlap significantly. Migrate when the team needs Nx's project graph, code generation, or module boundary enforcement.

```bash
npx nx@latest init
# Select "Integrated monorepo" when prompted
# Nx reads turbo.json pipeline and generates equivalent nx.json targetDefaults
```

Map Turborepo concepts to Nx equivalents:

| Turborepo | Nx Equivalent |
|-----------|---------------|
| `turbo.json` pipeline | `nx.json` targetDefaults |
| `--filter=<package>` | `--projects=<package>` or `-p <package>` |
| `--filter=...<package>` | `--projects=<package> --withDeps` |
| Remote cache (Vercel) | Nx Cloud or self-hosted |
| `outputs` | `outputs` in targetDefaults |
| `dependsOn` | `dependsOn` in targetDefaults |

Run both `turbo run build` and `nx run-many -t build` in parallel for one sprint to validate output parity before removing Turborepo.

### npm/Yarn Workspaces to pnpm

The primary change is the workspace protocol syntax and the lockfile format.

```bash
# Install pnpm
npm install -g pnpm

# Delete existing lockfiles and node_modules
find . -name 'package-lock.json' -delete
find . -name 'yarn.lock' -delete
find . -name 'node_modules' -type d -prune -exec rm -rf {} +

# Create pnpm-workspace.yaml
cat > pnpm-workspace.yaml << 'EOF'
packages:
  - 'packages/*'
  - 'apps/*'
EOF

# Install with pnpm
pnpm install
```

Update internal dependency references from version ranges to workspace protocol:

```bash
# Find all internal @scope/ references and update to workspace:*
# Run this for each package that references internal packages
find packages -name 'package.json' -exec \
  sed -i 's/"@scope\/\([^"]*\)": "[^"]*"/"@scope\/\1": "workspace:*"/g' {} \;
```

Verify no phantom dependencies exist — pnpm's strict hoisting will surface them:

```bash
pnpm install
pnpm --filter '*' build 2>&1 | grep "Cannot find module"
```

Each "Cannot find module" error indicates a phantom dependency that must be added explicitly to the package's `package.json`.

### Any Tool to Bazel

Bazel migration is a multi-year effort. The Airbnb migration took 4.5 years and required a dedicated build infrastructure team. Approach it as a parallel build system, not a replacement.

Phase 1 — Instrument (months 1-6): Add Bazel BUILD files alongside existing build configs. Do not replace anything. Use `gazelle` for Go or `rules_js` for JavaScript to auto-generate BUILD files.

```bash
# Install Bazel
brew install bazel

# For JavaScript: install rules_js
# Add to MODULE.bazel or WORKSPACE
# Run gazelle to generate BUILD files
bazel run //:gazelle
```

Phase 2 — Validate parity (months 6-18): Run Bazel builds in CI alongside existing builds. Compare outputs. Fix discrepancies. Do not switch CI to Bazel-only until parity is confirmed for all packages.

Phase 3 — Cut over incrementally (months 18-36+): Switch packages to Bazel-only one team at a time. Keep the old build system working for teams not yet migrated.

Phase 4 — Decommission (months 36+): Remove old build configs only after all teams have validated Bazel for at least one full release cycle.

The Airbnb case study (2019-2024) shows that the primary cost is not the tooling but the cultural change — engineers must learn Bazel's hermetic build model, and every new dependency requires explicit BUILD file updates.

## Migration Decision Framework

| Migration | Effort | Risk | Primary Benefit | When to Proceed |
|-----------|--------|------|-----------------|-----------------|
| Polyrepo to monorepo (git subtree, squash) | Low (1-2 days/repo) | Low | Unified tooling, shared deps | Team shares >3 packages |
| Polyrepo to monorepo (filter-repo, full history) | Medium (2-4 days/repo) | Low-Medium | Full git history preserved | Compliance or blame requirements |
| Monorepo to polyrepo extraction | Medium (1-3 days) | Medium | Team independence | Regulatory or open-source |
| Lerna to Nx | Low (1-2 days) | Low | Better caching, project graph | Lerna 6+ already uses Nx |
| Turborepo to Nx | Medium (1-2 weeks) | Medium | Code generation, boundaries | Need module enforcement |
| npm/Yarn to pnpm | Medium (1-2 weeks) | Medium | Strict hoisting, disk efficiency | Phantom dep problems |
| Any tool to Bazel | Very High (2-5 years) | Very High | Hermetic builds, massive scale | >500 engineers, build times >30min |

## Common Migration Pitfalls

| Pitfall | Symptom | Prevention |
|---------|---------|------------|
| Lost git history | `git blame` shows migration commit, not original author | Use `git-filter-repo --to-subdirectory-filter` instead of `git subtree --squash` |
| Broken CI on unrelated packages | Every PR triggers all pipelines | Add path filtering before migrating first repo |
| Phantom dependencies surface | Build fails with "Cannot find module" after pnpm migration | Run `pnpm install` and fix all phantom deps before cutting over |
| Circular dependency introduced | Build hangs or fails with cycle error | Run `depcruise` before and after each import |
| Secrets in imported history | Security scanner flags old commits | Audit and purge secrets before migration using `git-filter-repo --strip-blobs-with-ids` |
| CODEOWNERS gaps | PRs merge without required review | Write CODEOWNERS entries before migration, not after |
| Dependency version conflicts | Two packages require incompatible versions of a shared dep | Audit `package.json` files across all repos before migrating; resolve conflicts first |
| Team resistance | Engineers continue using old repos | Archive old repos immediately after migration; do not leave them writable |
| Lockfile conflicts | `pnpm-lock.yaml` conflicts on every PR | Establish a single lockfile owner process; use `pnpm install --frozen-lockfile` in CI |
| Monorepo build times balloon | CI takes 3x longer after migration | Set up remote caching before migrating more than 3 repos |

## Incremental Migration Strategy

Run old and new systems in parallel during the transition window. Never force a hard cutover.

### Parallel Validation Pattern

For each migrated package, run both the old repo's CI and the monorepo CI for a defined validation window (minimum one sprint, recommended two weeks):

1. Old repo CI: continues to run on pushes to the old repo's main branch
2. Monorepo CI: runs on pushes to the monorepo's main branch, scoped to the migrated package's path
3. Compare test results, build outputs, and deployment artifacts daily
4. If results diverge, investigate before proceeding with the next migration

### Cutover Criteria

Declare a package fully migrated only when all of the following are true:

- Monorepo CI has passed for 10 consecutive builds without intervention
- All internal consumers have updated their dependency references to workspace protocol
- CODEOWNERS entries are verified and tested
- The old repo's README has been updated to redirect to the monorepo
- The old repo's CI has been disabled or set to fail with a redirect message
- At least one full release has been cut from the monorepo for this package

### Rollback Procedure

Document the rollback procedure before starting any migration:

```bash
# Identify the commit before the migration merge
git log --oneline --merges | grep "Merge.*<repo-name>"

# Revert the merge commit
git revert -m 1 <merge-commit-sha>

# Re-enable the old repo's CI
# Update internal consumers to point back to the old repo
```

Keep the old repo's CI configuration intact (but disabled) for 90 days after migration. This makes rollback feasible without archaeology.

For tool migrations (Lerna to Nx, Turborepo to Nx), keep the old tool's config files in place until the new tool has been validated in production. Remove old configs only after two full release cycles with the new tool.

For CI setup details specific to each tool, see `references/ci-cd-patterns.md`.
For tool selection rationale and comparison, see `references/tool-selection.md`.
