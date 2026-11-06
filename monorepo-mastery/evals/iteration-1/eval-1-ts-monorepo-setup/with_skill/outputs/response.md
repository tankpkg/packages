# Short answer

For your exact shape (JS/TS-only, 8 packages), use **pnpm workspaces + Turborepo**.

- From the skill decision tree: JS/TS-only and under ~20 packages favors **Turborepo** for lower config overhead.
- From workspace guidance: default package manager should be **pnpm v10** (strict workspace behavior + catalogs to kill version drift).
- For CI, use **affected-only Turborepo filters** (`--filter=...[origin/main]`) plus remote cache.

---

## Why this stack for your case

You have 8 packages:

- shared utils
- 3 microservices
- 2 React apps
- a CLI
- a types package

That is large enough to benefit from orchestration/caching, but still small enough that Nx would add extra config burden unless you specifically need Nx features (code generators, module-boundary lint rules, distributed task execution).

So the practical recommendation is:

1. **pnpm** for workspace dependency management and version catalogs
2. **Turborepo** for task graph + caching + changed-only runs
3. **GitHub Actions** with a single reusable pipeline and affected-only commands

---

## Target repo layout

```text
.
├─ apps/
│  ├─ web/
│  ├─ admin/
│  └─ cli/
├─ services/
│  ├─ auth-service/
│  ├─ billing-service/
│  └─ notifications-service/
├─ packages/
│  ├─ shared-utils/
│  └─ types/
├─ package.json
├─ pnpm-workspace.yaml
├─ turbo.json
├─ tsconfig.base.json
├─ .npmrc
└─ .github/workflows/ci.yml
```

---

## 1) Bootstrap the monorepo

```bash
mkdir company-monorepo && cd company-monorepo
git init

# root package.json
pnpm init

# add turbo + typescript at root
pnpm add -D turbo typescript
```

### Root `package.json`

```json
{
  "name": "company-monorepo",
  "private": true,
  "packageManager": "pnpm@10.0.0",
  "scripts": {
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "dev": "turbo run dev --parallel"
  },
  "devDependencies": {
    "turbo": "^2.0.0",
    "typescript": "^5.7.0"
  }
}
```

### `pnpm-workspace.yaml` (critical for version drift)

```yaml
packages:
  - "apps/*"
  - "services/*"
  - "packages/*"

catalog:
  typescript: "^5.7.0"
  react: "^19.0.0"
  "@types/node": "^22.0.0"
```

### `.npmrc` (strict mode)

```ini
strict-peer-dependencies=true
auto-install-peers=true
shamefully-hoist=false
```

### `turbo.json`

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["$TURBO_DEFAULT$", ".env*"],
      "outputs": ["dist/**", "build/**", ".next/**"]
    },
    "typecheck": {
      "dependsOn": ["^typecheck"],
      "inputs": ["$TURBO_DEFAULT$", "tsconfig*.json"],
      "outputs": []
    },
    "lint": {
      "dependsOn": ["^lint"],
      "outputs": []
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

---

## 2) Internal dependency conventions (stop drift + keep local linking)

In each package that depends on another internal package, use `workspace:*`.

Example: `services/auth-service/package.json`

```json
{
  "name": "@acme/auth-service",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "test": "vitest run"
  },
  "dependencies": {
    "@acme/shared-utils": "workspace:*",
    "@acme/types": "workspace:*"
  },
  "devDependencies": {
    "typescript": "catalog:",
    "@types/node": "catalog:"
  }
}
```

Key points:

- `workspace:*` guarantees local package linking in dev/CI.
- `catalog:` keeps common versions centralized in root `pnpm-workspace.yaml`.

---

## 3) Bring your 8 repos into one repo

You have two valid migration paths from the skill:

### A) Keep full git history (`git-filter-repo`) — recommended

```bash
# For each source repo
git clone --no-local git@github.com:your-org/auth-service.git /tmp/auth-service-filtered
cd /tmp/auth-service-filtered
git filter-repo --to-subdirectory-filter services/auth-service

cd /path/to/company-monorepo
git remote add auth-service-filtered /tmp/auth-service-filtered
git fetch auth-service-filtered --no-tags
git merge --allow-unrelated-histories auth-service-filtered/main --no-edit
git remote remove auth-service-filtered
```

Repeat for each repo, mapping it to `apps/*`, `services/*`, or `packages/*`.

### B) Simpler import with squashed history (`git subtree add`)

```bash
git remote add auth-service git@github.com:your-org/auth-service.git
git fetch auth-service --no-tags
git subtree add --prefix=services/auth-service auth-service main --squash
git remote remove auth-service
```

---

## 4) Monorepo CI that builds only what changed

This is the most important part for your requirement.

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    env:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - name: Install
        run: pnpm install --frozen-lockfile

      - name: Lint affected
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            pnpm turbo run lint --filter=...[origin/main]
          else
            pnpm turbo run lint --filter=...[HEAD^1]
          fi

      - name: Typecheck affected
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            pnpm turbo run typecheck --filter=...[origin/main]
          else
            pnpm turbo run typecheck --filter=...[HEAD^1]
          fi

      - name: Test affected
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            pnpm turbo run test --filter=...[origin/main]
          else
            pnpm turbo run test --filter=...[HEAD^1]
          fi

      - name: Build affected
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            pnpm turbo run build --filter=...[origin/main]
          else
            pnpm turbo run build --filter=...[HEAD^1]
          fi
```

Why this works:

- `--filter=...[origin/main]` = changed packages since main **plus dependents**.
- Remote cache via `TURBO_TOKEN`/`TURBO_TEAM` avoids recomputing unchanged tasks across runners.
- One centralized workflow removes duplicated CI definitions across the old repos.

---

## 5) Optional: Workflow-level path optimization

If you want to avoid running even the monorepo CI workflow for docs-only changes, add path filters:

```yaml
on:
  pull_request:
    paths:
      - "apps/**"
      - "services/**"
      - "packages/**"
      - "package.json"
      - "pnpm-lock.yaml"
      - "pnpm-workspace.yaml"
      - "turbo.json"
```

Use this as an extra optimization; affected filtering is still your main mechanism.

---

## 6) Immediate post-migration verification commands

Run these after each imported package:

```bash
pnpm install --frozen-lockfile
pnpm turbo run build
pnpm turbo run test
pnpm turbo run lint
pnpm turbo run typecheck

# Package-level checks
pnpm --filter @acme/auth-service build
pnpm --filter @acme/auth-service test
```

---

## 7) If you outgrow Turborepo later

Switch to Nx when you need:

- enforced module boundaries at lint time,
- code generators/scaffolding,
- distributed task execution.

Given your current size (8 TS packages), starting with Turbo keeps migration risk and complexity lower.

---

## Final recommendation

Use **pnpm + Turborepo** now, with:

1. `workspace:*` for internal package links,
2. `catalog:` for centralized dependency versions,
3. `turbo run <task> --filter=...[origin/main]` in GitHub Actions,
4. remote cache enabled from day one.

That combination directly solves your three current pains: duplicated CI, version drift, and slow/full rebuild pipelines.
