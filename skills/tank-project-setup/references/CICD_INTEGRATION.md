# CI/CD Integration for Tank Skills

How to add `tank install` to CI/CD pipelines so every build and every developer
gets the same skills deterministically — like `npm ci` for agent skills.

## Key Principle

`tank install` (without arguments) reads from `skills.lock` and installs
exact versions with integrity verification. **No authentication required** for
installs — only `tank publish` needs auth.

This means CI/CD setup is simple: install the CLI, run `tank install`, done.

## GitHub Actions

### Minimal Setup

Add to an existing workflow or create `.github/workflows/tank-install.yml`:

```yaml
- name: Install Tank CLI
  run: npm install -g @tankpkg/cli

- name: Install Tank skills
  run: tank install

- name: Verify integrity
  run: tank verify
```

### Complete Standalone Workflow

See `assets/github-action-tank-install.yml` for a drop-in workflow file.

```yaml
name: Tank Skills

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  install-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Cache Tank skills
        uses: actions/cache@v4
        with:
          path: .tank
          key: tank-skills-${{ hashFiles('skills.lock') }}
          restore-keys: |
            tank-skills-

      - name: Install Tank CLI
        run: npm install -g @tankpkg/cli

      - name: Install skills
        run: tank install

      - name: Verify integrity
        run: tank verify
```

### Integration with Existing Workflow

If you already have a CI workflow, add Tank install as a step.
Place it **after checkout** and **before your main build/test steps**:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      # --- Tank skills setup ---
      - name: Install Tank CLI
        run: npm install -g @tankpkg/cli

      - name: Install Tank skills
        run: tank install

      # --- Your existing steps ---
      - run: npm ci
      - run: npm test
```

### Caching Strategy

Cache `.tank/` directory to avoid re-downloading skills on every run.
Key on `skills.lock` hash for cache invalidation:

```yaml
- uses: actions/cache@v4
  with:
    path: .tank
    key: tank-${{ hashFiles('skills.lock') }}
    restore-keys: tank-
```

**Why this works**: `skills.lock` changes only when skill versions change.
Same lockfile = same skills = cache hit.

## GitLab CI

### Minimal Setup

Add to `.gitlab-ci.yml`:

```yaml
stages:
  - setup
  - build
  - test

install-skills:
  stage: setup
  image: node:20
  script:
    - npm install -g @tankpkg/cli
    - tank install
    - tank verify
  cache:
    key:
      files:
        - skills.lock
    paths:
      - .tank/
  artifacts:
    paths:
      - .tank/
    expire_in: 1 hour
```

### Integration with Existing Pipeline

```yaml
before_script:
  - npm install -g @tankpkg/cli
  - tank install

build:
  stage: build
  script:
    - npm ci
    - npm run build

test:
  stage: test
  script:
    - npm test
```

## CircleCI

```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: cimg/node:20.0
    steps:
      - checkout
      - restore_cache:
          keys:
            - tank-{{ checksum "skills.lock" }}
            - tank-
      - run:
          name: Install Tank CLI
          command: npm install -g @tankpkg/cli
      - run:
          name: Install skills
          command: tank install
      - save_cache:
          key: tank-{{ checksum "skills.lock" }}
          paths:
            - .tank
      - run:
          name: Verify
          command: tank verify
```

## Azure Pipelines

```yaml
steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '20.x'

  - script: npm install -g @tankpkg/cli
    displayName: 'Install Tank CLI'

  - script: tank install
    displayName: 'Install Tank skills'

  - script: tank verify
    displayName: 'Verify skill integrity'
```

## Docker

For Docker-based builds, add Tank install to Dockerfile or entrypoint:

```dockerfile
# In a multi-stage build
FROM node:20-alpine AS base

# Install Tank CLI
RUN npm install -g @tankpkg/cli

# Copy lockfile first for layer caching
COPY skills.json skills.lock ./
RUN tank install

# Then copy the rest of the project
COPY . .
```

Or in `docker-compose.yml` as an init step:

```yaml
services:
  app:
    build: .
    volumes:
      - .:/app
    command: sh -c "tank install && npm start"
```

## What to Commit vs Ignore

### MUST commit (tracked in git)

| File | Purpose |
|------|---------|
| `skills.json` | Declares skill dependencies (like package.json) |
| `skills.lock` | Locks exact versions + integrity hashes (like package-lock.json) |

### MUST ignore (add to .gitignore)

| Path | Purpose |
|------|---------|
| `.tank/` | Downloaded skill packages (like node_modules) |

### .gitignore entry

```
# Tank skills (installed via tank install)
.tank/
```

## Lockfile Management

### How skills.lock works

- Created/updated when you run `tank install @org/skill` (adding a skill)
- Read (not modified) when you run `tank install` (installing from lockfile)
- Contains SHA-512 integrity hashes for every installed skill
- `tank verify` checks installed files against lockfile hashes

### Keeping lockfile in sync

| Scenario | Action |
|----------|--------|
| Add new skill | `tank install @org/skill` → updates skills.json + skills.lock |
| Update skills | `tank update` → updates skills.lock |
| Fresh clone | `tank install` → reads skills.lock, installs exact versions |
| CI/CD build | `tank install` + `tank verify` → deterministic + verified |

### Lockfile conflicts (merge conflicts)

If `skills.lock` has merge conflicts:

```bash
# Accept either version, then regenerate
git checkout --theirs skills.lock   # or --ours
tank install                        # regenerates from skills.json
```

## Troubleshooting CI/CD

### Problem: `tank: command not found`

Tank CLI not installed in CI environment.

```yaml
- run: npm install -g @tankpkg/cli
```

### Problem: `No skills.json found`

Working directory doesn't contain skills.json.

```yaml
- run: tank install
  working-directory: ./path/to/project  # if not at repo root
```

### Problem: Slow installs

Cache the `.tank/` directory:

```yaml
- uses: actions/cache@v4
  with:
    path: .tank
    key: tank-${{ hashFiles('skills.lock') }}
```

### Problem: Integrity verification fails

Lockfile and installed files don't match. Usually caused by
cached `.tank/` from a different lockfile version:

```yaml
# Clear cache and reinstall
- run: rm -rf .tank && tank install
```

### Problem: Version not found in registry

The skill version in skills.lock may have been yanked or registry is unreachable.

```bash
# Check skill availability
tank info @org/skill

# If version was yanked, update to latest
tank update @org/skill
```
