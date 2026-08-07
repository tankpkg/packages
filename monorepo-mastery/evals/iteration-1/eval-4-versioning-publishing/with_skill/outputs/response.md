# Recommended Versioning and Publishing Strategy for Your Nx Monorepo

Given your mix (independent libs + tightly coupled component/theme/icon packages), use a **hybrid strategy with Changesets**:

- **Independent versioning** for standalone libraries.
- **Fixed version group** for the coupled UI suite (`component-library`, `theme`, `icons`) so they always move together.

This maps directly to the monorepo skill decision tree:

- Independent libs -> independent versioning
- Tightly coupled packages -> fixed/locked versioning
- Mixed repo -> **hybrid** (grouped Changesets)

## Why this is the right fit

- You avoid unnecessary releases of all 12 packages (a pure fixed train would over-release).
- You avoid version skew in your tightly coupled UI trio (a pure independent strategy would drift).
- You still get per-package changelogs and controlled release cadence.
- Changesets is the recommended modern JS/TS monorepo release workflow.

---

## 1) Concrete versioning model

Assume packages:

- Coupled group: `@acme/ui`, `@acme/theme`, `@acme/icons`
- Independent libs: `@acme/utils`, `@acme/forms`, `@acme/date`, etc.

Rules:

1. Any change to one coupled package releases all three at the same version.
2. Independent libs release only when changed.
3. Internal dependencies use `workspace:*` (or `workspace:^`), then publish rewrites to semver.

---

## 2) Changesets configuration

### Install and initialize

```bash
pnpm add -D @changesets/cli
pnpm changeset init
```

### `.changeset/config.json`

Use `fixed` to lock the coupled set while leaving everything else independent.

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [["@acme/ui", "@acme/theme", "@acme/icons"]],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

Notes:

- `fixed` gives you the hybrid grouping behavior you need.
- `updateInternalDependencies: "patch"` prevents forgotten dependent bumps.
- If packages are private, use `"access": "restricted"`.

---

## 3) Package-level publish safety

Each publishable package should include:

### `packages/ui/package.json` (pattern for all published packages)

```json
{
  "name": "@acme/ui",
  "version": "0.0.0",
  "private": false,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "files": ["dist", "README.md", "LICENSE"],
  "scripts": {
    "build": "nx build ui",
    "prepublishOnly": "pnpm build"
  },
  "dependencies": {
    "@acme/theme": "workspace:*",
    "@acme/icons": "workspace:*"
  },
  "publishConfig": {
    "access": "public",
    "provenance": true
  }
}
```

Why:

- `files` prevents leaking source/tests/tooling into npm.
- `prepublishOnly` prevents publishing unbuilt output.
- `workspace:*` keeps local development correct and rewrites during publish.

---

## 4) Contributor workflow

### On feature/fix PRs

```bash
pnpm changeset add
```

This creates `.changeset/*.md`, for example:

```md
---
"@acme/ui": minor
"@acme/theme": patch
---

Add compact button variant and update theme spacing tokens.
```

For a coupled set change, selecting one member is enough; fixed grouping will align versions across the group.

---

## 5) CI release workflow (GitHub Actions)

This is the baseline release automation: version PR + publish on merge.

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: pnpm/action-setup@v4
        with:
          version: 10

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
          registry-url: https://registry.npmjs.org

      - run: pnpm install --frozen-lockfile

      # Optional but recommended: verify only affected projects before publishing
      - name: Validate affected
        run: |
          pnpm nx affected --target=lint --base=origin/main --parallel=3
          pnpm nx affected --target=test --base=origin/main --parallel=3
          pnpm nx affected --target=build --base=origin/main --parallel=3

      - uses: changesets/action@v1
        with:
          version: pnpm changeset version
          publish: pnpm changeset publish
          commit: "chore: version packages"
          title: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # If npm trusted publishing OIDC is not configured yet, use token fallback.
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Implementation notes:

- Long-term, use npm trusted publishing (OIDC + provenance) to avoid long-lived tokens.
- Keep publish in CI only; do not publish from laptops.

---

## 6) Optional canary/pre-release channel

For integration testing before stable:

```bash
pnpm changeset version --snapshot canary
pnpm changeset publish --tag canary
```

Consumers can test with:

```bash
pnpm add @acme/ui@canary @acme/theme@canary @acme/icons@canary
```

---

## 7) Nx guardrails to reduce release risk

Add module boundary rules so independent packages do not accidentally couple over time.

### ESLint rule (Nx)

```json
{
  "rules": {
    "@nx/enforce-module-boundaries": [
      "error",
      {
        "depConstraints": [
          {
            "sourceTag": "scope:independent",
            "onlyDependOnLibsWithTags": ["scope:independent", "scope:shared"]
          },
          {
            "sourceTag": "scope:ui-suite",
            "onlyDependOnLibsWithTags": ["scope:ui-suite", "scope:shared"]
          }
        ]
      }
    ]
  }
}
```

Tag your coupled trio with `scope:ui-suite` and others as `scope:independent`.

---

## 8) Root scripts to standardize operations

### root `package.json`

```json
{
  "scripts": {
    "changeset:add": "changeset add",
    "changeset:status": "changeset status",
    "release:version": "changeset version",
    "release:publish": "changeset publish",
    "release:canary": "changeset version --snapshot canary && changeset publish --tag canary"
  }
}
```

---

## 9) What to avoid

- Do not manually bump versions across 12 packages.
- Do not release all packages on every change unless they are truly a single release train.
- Do not skip `files` and `prepublishOnly`.
- Do not let internal `workspace:*` usage go unverified; run dry-runs regularly.

Dry-run checks before first live publish:

```bash
pnpm changeset status
npm publish --dry-run
```

---

## 10) If you want Lerna instead

Lerna is still valid (especially in Nx ecosystems), but for your mixed coupling model, Changesets `fixed` groups are usually cleaner.

If you choose Lerna anyway, run independent mode globally and enforce group lockstep with process/policy, but this is generally more brittle than Changesets fixed groups.

---

## Bottom line

For your Nx monorepo with 12 npm packages and mixed coupling, implement:

- **Changesets hybrid strategy** (independent by default + one fixed group for UI/theme/icons)
- **CI-only publishing** with Changesets action
- **Affected validation via Nx** before release
- **Package hardening** (`files`, `prepublishOnly`, `workspace:*`, provenance)

That gives you accurate semver signals for consumers, no version skew in tightly coupled packages, and scalable release operations as the repo grows.
