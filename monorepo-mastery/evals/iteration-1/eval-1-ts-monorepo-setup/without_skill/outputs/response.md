You’re a great fit for a **TypeScript monorepo with Turborepo + pnpm workspaces**.

Given your setup (shared utils, microservices, React apps, CLI, shared types), this combo gives you:

- one dependency graph across all packages
- deterministic installs and better workspace linking (`pnpm`)
- fast task orchestration and caching (`turbo`)
- CI that can run only what changed (`turbo --filter=...[origin/main]`)

---

## Recommendation

Use:

- **Package manager:** `pnpm`
- **Monorepo task runner:** `Turborepo`
- **Versioning & releases:** `Changesets` (optional but highly recommended)
- **Build tooling per package:** keep what each project already uses (e.g., `tsup`, `vite`, `tsc`, `tsx`)

Why this stack:

- lower migration friction than Nx when you already know your tools
- excellent cache behavior for TS + React + services
- clean changed-only CI with simple filters

---

## Target Structure

```text
repo/
  apps/
    web-app-1/
    web-app-2/
    service-a/
    service-b/
    service-c/
    cli/
  packages/
    utils/
    types/
  package.json
  pnpm-workspace.yaml
  turbo.json
  tsconfig.base.json
  .github/workflows/ci.yml
```

---

## 1) Bootstrap the Monorepo

```bash
mkdir ts-platform-monorepo && cd ts-platform-monorepo
git init
pnpm init
pnpm add -D turbo typescript @changesets/cli
```

Root `package.json`:

```json
{
  "name": "ts-platform-monorepo",
  "private": true,
  "packageManager": "pnpm@9.0.0",
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev --parallel",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "clean": "turbo run clean",
    "changeset": "changeset",
    "version-packages": "changeset version",
    "release": "changeset publish"
  },
  "devDependencies": {
    "@changesets/cli": "^2.27.0",
    "turbo": "^2.0.0",
    "typescript": "^5.6.0"
  }
}
```

`pnpm-workspace.yaml`:

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

`turbo.json`:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**", "!.next/cache/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "outputs": []
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "typecheck": {
      "dependsOn": ["^typecheck"],
      "outputs": []
    },
    "clean": {
      "cache": false
    }
  }
}
```

`tsconfig.base.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@acme/types": ["packages/types/src/index.ts"],
      "@acme/utils": ["packages/utils/src/index.ts"]
    }
  }
}
```

---

## 2) Migrate the 8 Repos Into `apps/` and `packages/`

For preserving history, use one of:

- `git subtree` (simpler)
- `git filter-repo` + merge (more control)

Simple no-history copy (fastest first pass):

```bash
mkdir -p apps packages
# copy your projects into target dirs:
# apps/web-app-1, apps/web-app-2, apps/service-a, apps/service-b, apps/service-c, apps/cli
# packages/utils, packages/types
```

Then in each workspace package, ensure a proper `name` and scripts.

Example `packages/utils/package.json`:

```json
{
  "name": "@acme/utils",
  "version": "0.1.0",
  "private": true,
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": ["dist"],
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "clean": "rimraf dist"
  }
}
```

Example `apps/service-a/package.json`:

```json
{
  "name": "@acme/service-a",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc -p tsconfig.build.json",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "clean": "rimraf dist"
  },
  "dependencies": {
    "@acme/types": "workspace:*",
    "@acme/utils": "workspace:*"
  }
}
```

Example `apps/web-app-1/package.json`:

```json
{
  "name": "@acme/web-app-1",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "clean": "rimraf dist"
  },
  "dependencies": {
    "@acme/types": "workspace:*",
    "@acme/utils": "workspace:*"
  }
}
```

Workspace linking rule: always reference internal packages with `workspace:*`.

---

## 3) Standardize TypeScript Config In Every Package

Each package tsconfig should extend root:

`apps/service-a/tsconfig.json`

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

For `packages/types`, use pure declaration emit if needed:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "emitDeclarationOnly": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

---

## 4) Install + Validate Locally

```bash
pnpm install
pnpm build
pnpm lint
pnpm test
pnpm typecheck
```

You should now have one command surface for all projects.

---

## 5) CI That Builds Only What Changed

Here is a production-ready GitHub Actions workflow using Turborepo filtering.

`.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  changed-only:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 9

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm

      - name: Install
        run: pnpm install --frozen-lockfile

      - name: Lint changed workspaces
        run: pnpm turbo run lint --filter=...[origin/main]

      - name: Typecheck changed workspaces
        run: pnpm turbo run typecheck --filter=...[origin/main]

      - name: Test changed workspaces
        run: pnpm turbo run test --filter=...[origin/main]

      - name: Build changed workspaces
        run: pnpm turbo run build --filter=...[origin/main]
```

How `--filter=...[origin/main]` works:

- selects workspaces changed since `origin/main`
- includes dependents where needed based on graph/task deps
- avoids rebuilding untouched packages

If you use Turborepo remote cache (Vercel or self-hosted), CI gets much faster:

```yaml
      - name: Build with remote cache
        env:
          TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
          TURBO_TEAM: ${{ secrets.TURBO_TEAM }}
        run: pnpm turbo run build --filter=...[origin/main]
```

---

## 6) Version Drift Fix (Releases)

Use Changesets so internal package versions move coherently.

```bash
pnpm changeset init
```

Then when changing shared packages:

```bash
pnpm changeset
pnpm version-packages
```

Recommended release workflow (`.github/workflows/release.yml`):

```yaml
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
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          registry-url: https://registry.npmjs.org

      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run build
      - run: pnpm changeset publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## 7) Common Migration Pitfalls (Avoid These)

- **Duplicate TS path aliases** across repos: centralize in `tsconfig.base.json`.
- **Inconsistent Node versions**: pin in `.nvmrc` and CI.
- **Mixed ESM/CJS confusion**: decide package-by-package and declare `"type"` explicitly.
- **Cross-package imports by relative paths** (`../../utils/src`): replace with workspace package imports.
- **Per-repo lint/test config drift**: move to shared root config where possible.

---

## 8) Minimal Command Checklist

```bash
# root
pnpm install
pnpm turbo run build
pnpm turbo run test

# changed-only local check versus main
pnpm turbo run build --filter=...[origin/main]
pnpm turbo run test --filter=...[origin/main]
```

---

## Short answer

If you want the practical, low-risk path: **use pnpm workspaces + Turborepo + Changesets**. It solves your duplicated CI and version drift, and gives you changed-only CI with a single filter flag.
