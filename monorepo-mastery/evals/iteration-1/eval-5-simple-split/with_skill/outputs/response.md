You can keep this very simple with **npm workspaces** and just 2 packages:

- `apps/main-app` (your Node.js app)
- `packages/shared` (your shared library)

For a 2-package split, this is the lowest-friction setup (no orchestrator, no extra monorepo tooling).

## Simple structure

```text
my-repo/
├─ package.json
├─ apps/
│  └─ main-app/
│     ├─ package.json
│     └─ src/
│        └─ index.js
└─ packages/
   └─ shared/
      ├─ package.json
      └─ src/
         └─ index.js
```

## Root config

`package.json` (root):

```json
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "dev": "npm run dev -w @acme/main-app",
    "build": "npm run build --workspaces"
  }
}
```

Notes:
- `private: true` prevents accidental publish of the repo root.
- `workspaces` tells npm where your two package folders live.

## Shared package

`packages/shared/package.json`:

```json
{
  "name": "@acme/shared",
  "version": "0.0.0",
  "private": true,
  "main": "src/index.js"
}
```

`packages/shared/src/index.js`:

```js
function greet(name) {
  return `Hello, ${name}`;
}

module.exports = { greet };
```

## Main app package

`apps/main-app/package.json`:

```json
{
  "name": "@acme/main-app",
  "version": "0.0.0",
  "private": true,
  "main": "src/index.js",
  "scripts": {
    "dev": "node src/index.js",
    "build": "node -e \"console.log('build step placeholder')\""
  },
  "dependencies": {
    "@acme/shared": "workspace:*"
  }
}
```

`apps/main-app/src/index.js`:

```js
const { greet } = require("@acme/shared");

console.log(greet("world"));
```

## Commands

From repo root:

```bash
npm install
npm run dev
```

Useful workspace commands:

```bash
npm run dev -w @acme/main-app
npm run build --workspaces
```

## Why this is the simplest good setup

- Uses only what ships with Node (`npm` + workspaces).
- Keeps code split clean (`app` depends on `shared`).
- No heavy monorepo tool needed for 2 packages.
- Easy to upgrade later (for example to `pnpm`) if you grow.

## Optional small upgrade path (later)

If you eventually want stricter dependency boundaries and faster installs, move to `pnpm` workspaces. But for "just split into app + shared lib", npm workspaces are perfectly fine.
