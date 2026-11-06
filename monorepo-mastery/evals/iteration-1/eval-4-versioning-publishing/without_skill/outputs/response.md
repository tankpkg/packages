# Great setup for your Nx monorepo: use **hybrid versioning**

For your mix of independent libs and tightly coupled UI packages, the cleanest model is:

- **Independent versioning** for unrelated packages (each package bumps on its own)
- **Fixed/lockstep versioning groups** for tightly coupled packages (component library + theme + icon set share one version)

This gives you:

- Fast releases for independent libs
- Guaranteed compatibility inside coupled sets
- Clearer changelogs and fewer accidental breakages

---

## Recommended release model

Assume packages like:

- Coupled group: `@acme/ui`, `@acme/ui-theme`, `@acme/ui-icons`
- Independent libs: `@acme/utils`, `@acme/http`, `@acme/date`, etc.

Use **Nx Release groups** so you can declare:

- Group A (`ui-stack`) => fixed versioning
- Group B (`independent-libs`) => independent versioning

### Why this beats all-independent or all-lockstep

- All-independent hurts consumer DX for coupled packages (version mismatch risk)
- All-lockstep over-releases everything and creates version noise
- Hybrid keeps coupling where it is real and avoids coupling where it is artificial

---

## Semantic versioning policy (enforce this)

- `feat:` => **minor**
- `fix:` => **patch**
- `BREAKING CHANGE:` (or `!`) => **major**

For grouped packages (`ui-stack`):

- Any breaking change in one member bumps the whole group major
- Non-breaking change in one member still bumps all members to the same new group version

For independent packages:

- Bump only the changed package, plus dependents if version ranges require updates

---

## Nx configuration example (`nx.json`)

Use `nx release` with release groups and conventional commits.

```json
{
  "$schema": "./node_modules/nx/schemas/nx-schema.json",
  "release": {
    "projectsRelationship": "independent",
    "releaseTagPattern": "{projectName}@{version}",
    "version": {
      "conventionalCommits": true
    },
    "changelog": {
      "workspaceChangelog": false,
      "projectChangelogs": true
    },
    "groups": {
      "ui-stack": {
        "projects": [
          "ui",
          "ui-theme",
          "ui-icons"
        ],
        "projectsRelationship": "fixed",
        "releaseTagPattern": "ui-stack@{version}"
      },
      "independent-libs": {
        "projects": [
          "utils",
          "http",
          "date",
          "forms",
          "analytics",
          "state",
          "cli",
          "eslint-config",
          "tsconfig",
          "testing"
        ],
        "projectsRelationship": "independent"
      }
    }
  }
}
```

Notes:

- Top-level `projectsRelationship: independent` is your default
- `ui-stack` overrides to `fixed`
- Use explicit tag patterns so rollback/debugging is easy

---

## Package dependency rules for coupled packages

In `@acme/ui`, pin compatibility to its coupled siblings:

```json
{
  "name": "@acme/ui",
  "version": "2.4.0",
  "peerDependencies": {
    "@acme/ui-theme": "2.4.x",
    "@acme/ui-icons": "2.4.x"
  }
}
```

Or if you want strict lockstep:

```json
{
  "peerDependencies": {
    "@acme/ui-theme": "2.4.0",
    "@acme/ui-icons": "2.4.0"
  }
}
```

Recommendation:

- Use `2.4.x` for less friction
- Use exact versions only if runtime/style breakage risk is high

---

## Required npm publish settings

In each publishable package:

```json
{
  "name": "@acme/ui",
  "version": "2.4.0",
  "publishConfig": {
    "access": "public",
    "provenance": true
  },
  "files": [
    "dist",
    "README.md",
    "LICENSE"
  ]
}
```

And ensure:

- Package is not accidentally private (`"private": false` or omit)
- `exports`, `types`, `main/module` are valid in packed artifact

---

## Root scripts (`package.json`)

```json
{
  "scripts": {
    "release:plan": "nx release --dry-run",
    "release:version": "nx release version",
    "release:changelog": "nx release changelog",
    "release:publish": "nx release publish",
    "release": "nx release",
    "release:pre": "nx release --preid=next",
    "release:ui-stack": "nx release --groups=ui-stack",
    "release:libs": "nx release --groups=independent-libs"
  }
}
```

Typical flow:

1. `npm run release:plan`
2. `npm run release` (version + changelog + publish in configured order)

---

## CI workflow (GitHub Actions)

Use two workflows:

- PR workflow => dry-run validation only
- Main/manual workflow => actual publish

### 1) PR release validation (`.github/workflows/release-dry-run.yml`)

```yaml
name: Release Dry Run

on:
  pull_request:
    branches: [main]

jobs:
  dry-run:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install
        run: npm ci

      - name: Build/Test Affected
        run: npx nx affected -t lint,test,build --base=origin/main --head=HEAD

      - name: Validate Release Plan
        run: npx nx release --dry-run
```

### 2) Publish on main/manual (`.github/workflows/release-publish.yml`)

```yaml
name: Release Publish

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      channel:
        description: npm dist-tag
        required: false
        default: latest

concurrency:
  group: release-main
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org
          cache: npm

      - name: Install
        run: npm ci

      - name: Verify
        run: npx nx run-many -t lint,test,build

      - name: Configure npm auth
        run: echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > ~/.npmrc
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Release
        run: |
          if [ "${{ github.event.inputs.channel }}" = "next" ]; then
            npx nx release publish --tag=next
          else
            npx nx release
          fi
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_CONFIG_PROVENANCE: true
```

Why this is production-safe:

- `concurrency` prevents parallel publish races
- `id-token: write` + `NPM_CONFIG_PROVENANCE=true` supports npm provenance
- `fetch-depth: 0` is required for changelog/versioning against git history

---

## Dist-tag strategy

Use channels intentionally:

- `latest` => stable releases
- `next` => prereleases / canaries

Examples:

```bash
# Publish prerelease versions like 3.0.0-next.1
npx nx release --preid=next

# Or publish computed version to next tag
npx nx release publish --tag=next

# Promote a tested version later
npm dist-tag add @acme/ui@3.0.0-next.4 latest
```

---

## Change management rules for your team

1. **Every PR touching publishable packages must use conventional commits**
2. **No direct `npm publish` from laptops** (CI only)
3. **Release dry-run must pass in PR**
4. **Coupled packages can only be released through `ui-stack` group**
5. **Breaking changes require migration notes in changelog**

---

## Practical release scenarios

### Scenario A: Fix only in `@acme/http`

- Bump: `@acme/http` patch only
- No changes to `ui-stack`

### Scenario B: New icon added in `@acme/ui-icons`

- Because `ui-icons` is in fixed `ui-stack`, bump all:
  - `@acme/ui`
  - `@acme/ui-theme`
  - `@acme/ui-icons`

### Scenario C: Breaking token change in `@acme/ui-theme`

- Entire `ui-stack` gets major bump
- Changelog includes migration section and code examples

---

## Optional improvement: Changesets as authoring UX

If your team wants very explicit PR-level intent, add Changesets for human-authored bump notes, while still executing with Nx in CI.

Example `.changeset/config.json`:

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": ["@changesets/changelog-github", { "repo": "acme/monorepo" }],
  "commit": false,
  "fixed": [["@acme/ui", "@acme/ui-theme", "@acme/ui-icons"]],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

Then contributors run:

```bash
npx changeset
```

This is optional, but it improves release-note quality in larger teams.

---

## Bottom line

For your 12-package Nx monorepo, implement **hybrid versioning with release groups**:

- Fixed group for truly coupled UI packages
- Independent versioning for everything else
- CI-only publishing with dry-run on PRs and publish on main
- Conventional commits + semver + dist-tag discipline

That gives you predictable compatibility, minimal release noise, and a workflow that scales as package count grows.
