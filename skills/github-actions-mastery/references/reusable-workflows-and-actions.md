# Reusable Workflows and Actions

Sources: GitHub Actions documentation (2026), actions toolkit (@actions/core, @actions/github), Docker container actions guide, composite actions guide

Covers: reusable workflows (inputs, outputs, secrets), composite actions, JavaScript actions, Docker actions, action versioning, and selection guidance.

## Reusable Workflows

A reusable workflow is a complete workflow file called by other workflows using `uses:`. It runs as a full job with its own runner.

### Defining a Reusable Workflow

```yaml
# .github/workflows/ci-reusable.yml
name: Reusable CI

on:
  workflow_call:
    inputs:
      node-version:
        description: 'Node.js version'
        required: false
        type: string
        default: '20'
      working-directory:
        description: 'Package directory'
        required: false
        type: string
        default: '.'
    outputs:
      coverage:
        description: 'Coverage percentage'
        value: ${{ jobs.test.outputs.coverage }}
    secrets:
      NPM_TOKEN:
        required: false
      CODECOV_TOKEN:
        required: true

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      coverage: ${{ steps.cov.outputs.pct }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - id: cov
        run: echo "pct=$(jq '.total.lines.pct' coverage/coverage-summary.json)" >> "$GITHUB_OUTPUT"
```

### Calling a Reusable Workflow

```yaml
# .github/workflows/ci.yml
jobs:
  test-api:
    uses: ./.github/workflows/ci-reusable.yml
    with:
      node-version: '20'
      working-directory: 'packages/api'
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  test-web:
    uses: ./.github/workflows/ci-reusable.yml
    with:
      working-directory: 'packages/web'
    secrets: inherit    # Pass all secrets from caller
```

### Reusable Workflow Constraints

| Constraint | Detail |
|-----------|--------|
| Nesting depth | Max 4 levels of reusable workflow calls |
| Matrix support | Caller can use matrix; called workflow cannot define its own |
| Env vars | Caller `env:` is NOT inherited — pass as inputs |
| Permissions | Caller's permissions apply (called workflow cannot escalate) |
| Concurrency | Caller job concurrency applies; called workflow can define its own |
| Location | Same repo, same org (private), or public repo |

### secrets: inherit

Pass all caller secrets to the reusable workflow without listing each one:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    secrets: inherit
```

Convenient but reduces visibility. Prefer explicit `secrets:` mapping for security-sensitive workflows.

## Composite Actions

A composite action is a sequence of steps packaged as a single action. It runs inline within the caller's job (not a separate runner).

### action.yml Structure

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: 'Install dependencies and build'
inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  install-command:
    description: 'Install command'
    required: false
    default: 'npm ci'
outputs:
  cache-hit:
    description: 'Whether cache was hit'
    value: ${{ steps.cache.outputs.cache-hit }}
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
    - id: cache
      uses: actions/cache@v4
      with:
        path: node_modules
        key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    - if: steps.cache.outputs.cache-hit != 'true'
      run: ${{ inputs.install-command }}
      shell: bash
    - run: npm run build
      shell: bash
```

### Calling a Composite Action

```yaml
# From same repo
- uses: ./.github/actions/setup-project
  with:
    node-version: '22'

# From another repo
- uses: myorg/shared-actions/setup-project@v1
  with:
    node-version: '22'
```

### Composite Action Rules

| Rule | Detail |
|------|--------|
| Shell required | Every `run:` step must specify `shell:` explicitly |
| No `env:` inheritance | Set env per step, not at action level |
| No services | Cannot define service containers |
| No `defaults:` | Cannot set default shell/working-directory at action level |
| Nesting | Composites can call other actions (including other composites) |
| Outputs | Use `${{ steps.id.outputs.name }}` in the `outputs:` section |

## JavaScript Actions

JavaScript actions run Node.js code with access to the Actions toolkit. Best for complex logic, API calls, or leveraging npm ecosystem.

### Project Structure

```
my-action/
  action.yml
  index.js        # Entry point
  package.json
  node_modules/    # Must be committed or bundled
```

### action.yml

```yaml
name: 'My Custom Action'
description: 'Does something useful'
inputs:
  token:
    description: 'GitHub token'
    required: true
outputs:
  result:
    description: 'Action result'
runs:
  using: 'node20'
  main: 'dist/index.js'         # Bundled entry point
  post: 'dist/cleanup.js'       # Optional cleanup step
```

### Using the Toolkit

```javascript
const core = require('@actions/core');
const github = require('@actions/github');
const exec = require('@actions/exec');

async function run() {
  try {
    const token = core.getInput('token', { required: true });
    const octokit = github.getOctokit(token);

    // Execute a command
    await exec.exec('npm', ['test']);

    // Set output
    core.setOutput('result', 'success');

    // Write summary
    await core.summary
      .addHeading('Results')
      .addTable([['Test', 'Status'], ['Unit', 'Pass']])
      .write();
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
```

### Bundling

Commit `node_modules` or bundle with `ncc`:

```bash
npx @vercel/ncc build index.js -o dist
```

Bundle to `dist/index.js` and reference that in `action.yml`. This avoids committing `node_modules/` and reduces the action size.

## Docker Actions

Docker actions run in an isolated container. Use when the action needs a specific OS environment, non-Node.js tools, or full isolation.

### action.yml

```yaml
name: 'Docker Lint Action'
description: 'Lints code in a Docker container'
inputs:
  config:
    description: 'Linter config file'
    required: false
    default: '.lintrc'
runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.config }}
```

### Dockerfile

```dockerfile
FROM alpine:3.19
RUN apk add --no-cache bash jq
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

### Docker Action Constraints

| Constraint | Detail |
|-----------|--------|
| Runner OS | Linux only (Docker actions do not run on Windows/macOS runners) |
| Performance | Container build adds startup time unless using pre-built image |
| Pre-built image | `image: 'docker://ghcr.io/owner/action:v1'` — skips build step |
| Environment | Inputs passed as `INPUT_<NAME>` env vars (uppercased) |

## Action Type Selection

| Need | Type | Why |
|------|------|-----|
| Reuse full job (runner, services, matrix) | Reusable workflow | Complete job isolation |
| Reuse step sequence within a job | Composite action | Inline, no extra runner |
| Complex logic, npm ecosystem | JavaScript action | Full Node.js API access |
| Non-Node.js toolchain, isolation | Docker action | Any language, clean environment |
| Simple shell commands shared across repos | Composite action | Minimal overhead |

## Versioning Actions

### Semantic Version Tags

```yaml
# Users reference major version tag
- uses: actions/checkout@v4

# Behind the scenes, v4 points to latest v4.x.y
```

### Maintaining Version Tags

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# Update major version tag
git tag -fa v1 -m "Update v1 to v1.2.3"
git push origin v1 --force
```

### SHA Pinning for Security

```yaml
# Tag reference (mutable — can be compromised)
- uses: actions/checkout@v4

# SHA reference (immutable — supply chain safe)
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.7
```

Always pin third-party actions to SHA in production workflows. Use Dependabot or Renovate to update automatically. See `references/security-hardening.md`.

## Publishing Actions to Marketplace

1. Create a public repository with `action.yml` at the root
2. Add a descriptive README.md with usage examples
3. Create a release with semantic version tag
4. GitHub auto-detects `action.yml` and lists on Marketplace

### Action Metadata Best Practices

| Field | Recommendation |
|-------|---------------|
| `name` | Unique, descriptive (shows in Marketplace search) |
| `description` | Concise — what the action does |
| `branding.icon` | Choose from Feather icons |
| `branding.color` | Pick a distinct color |
| `inputs` | Document every input with description |
| `outputs` | Document every output with description |
