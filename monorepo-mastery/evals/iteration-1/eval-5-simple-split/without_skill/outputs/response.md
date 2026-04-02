# Yep — use npm workspaces (2 packages, zero fancy tooling)

For your case (just **main app + shared lib**), the simplest setup is:

- one repo
- npm workspaces
- `packages/shared` for reusable code
- `packages/app` for the main app

No Bazel/Rush/Pants/etc. needed.

## Directory structure

```text
my-repo/
  package.json
  .gitignore
  packages/
    shared/
      package.json
      index.js
    app/
      package.json
      index.js
```

## 1) Root `package.json`

```json
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "dev": "npm run dev -w app",
    "start": "npm run start -w app",
    "test": "npm run test --workspaces --if-present"
  }
}
```

`private: true` prevents accidentally publishing the repo root.

## 2) Shared library package

`packages/shared/package.json`

```json
{
  "name": "@acme/shared",
  "version": "1.0.0",
  "main": "index.js",
  "type": "commonjs"
}
```

`packages/shared/index.js`

```js
function formatUser(name) {
  return `User: ${name.trim()}`;
}

module.exports = {
  formatUser
};
```

## 3) Main app package

`packages/app/package.json`

```json
{
  "name": "app",
  "version": "1.0.0",
  "private": true,
  "type": "commonjs",
  "main": "index.js",
  "dependencies": {
    "@acme/shared": "*"
  },
  "scripts": {
    "dev": "node index.js",
    "start": "node index.js"
  }
}
```

`packages/app/index.js`

```js
const { formatUser } = require("@acme/shared");

console.log(formatUser("  Elad  "));
```

## 4) Install and run

From repo root:

```bash
npm install
npm run dev
```

That’s it. npm links the workspace package automatically.

## Why this is the simplest good setup

- **Single install** at root
- **Clean split** between app and reusable code
- **No build step** needed for plain Node.js shared code
- Easy to grow later (add TypeScript, tests, linting when you actually need them)

## Optional tiny upgrades (later)

If you outgrow this, add only what hurts:

1. TypeScript in both packages
2. Shared ESLint config package
3. Changesets for versioning/publishing (only if you publish `shared`)

But for now, the config above is the right level of simplicity for 2 packages.
