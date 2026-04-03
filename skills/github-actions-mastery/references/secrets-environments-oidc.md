# Secrets, Environments, and OIDC

Sources: GitHub Actions security documentation (2026), GitHub OIDC documentation, AWS/GCP/Azure OIDC integration guides, GitHub deployment environments reference

Covers: secrets hierarchy, GITHUB_TOKEN permissions, configuration variables, environment protection rules, OIDC federation for cloud providers, and deployment workflow patterns.

## Secrets Hierarchy

Secrets are encrypted environment variables. They are masked in logs automatically.

### Secret Scopes

| Scope | Set By | Available To |
|-------|--------|-------------|
| Repository secrets | Repo admin | All workflows in the repo |
| Environment secrets | Repo admin | Workflows referencing that environment |
| Organization secrets | Org admin | Selected repos in the org |
| Dependabot secrets | Repo admin | Dependabot-triggered workflows only |

### Precedence

When names collide: environment secret > repository secret > organization secret. More specific scope wins.

### Creating Secrets

```bash
# Repository secret
gh secret set AWS_ACCOUNT_ID --body "123456789012"

# From a file
gh secret set SSH_KEY < ~/.ssh/deploy_key

# Environment secret
gh secret set DATABASE_URL --env production --body "postgres://..."

# Organization secret (visible to selected repos)
gh secret set NPM_TOKEN --org myorg --visibility selected --repos repo1,repo2
```

### Using Secrets

```yaml
steps:
  - run: npm publish
    env:
      NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Never** echo or log secrets. GitHub masks known secret values, but transformations (base64, substring) bypass masking. Never interpolate secrets directly in `run:` commands — use `env:` mapping.

```yaml
# WRONG — secret visible in process table and shell history
- run: curl -H "Authorization: Bearer ${{ secrets.TOKEN }}" https://api.example.com

# CORRECT — mapped to environment variable
- run: curl -H "Authorization: Bearer $TOKEN" https://api.example.com
  env:
    TOKEN: ${{ secrets.TOKEN }}
```

## GITHUB_TOKEN

Automatically created for each workflow run. Scoped to the repository.

### Default Permissions

| Permission | Default (permissive) | Default (restricted) |
|-----------|---------------------|---------------------|
| `contents` | `write` | `read` |
| `packages` | `write` | `read` |
| `issues` | `write` | `read` |
| `pull-requests` | `write` | `read` |
| `actions` | `write` | `read` |
| `deployments` | `write` | `read` |
| `id-token` | `none` | `none` |

Set repository default to **restricted** (Settings > Actions > General > Workflow permissions > "Read repository contents and packages permissions"). Then grant per-job.

### Per-Job Permissions

```yaml
permissions: {}                    # Top-level: deny all

jobs:
  test:
    permissions:
      contents: read               # Only read code
    runs-on: ubuntu-latest

  deploy:
    permissions:
      contents: read
      id-token: write              # OIDC token for cloud auth
      deployments: write           # Create deployment status
    runs-on: ubuntu-latest
```

### All Available Permissions

| Permission | Controls |
|-----------|---------|
| `actions` | Workflow management |
| `contents` | Repository contents, commits, branches |
| `deployments` | Deployment statuses |
| `id-token` | OIDC JWT for cloud federation |
| `issues` | Issues |
| `packages` | GitHub Packages |
| `pages` | GitHub Pages |
| `pull-requests` | Pull requests |
| `security-events` | Code scanning alerts |
| `statuses` | Commit statuses |
| `attestations` | Artifact attestations |

Set each to `read`, `write`, or `none`.

## Configuration Variables

Non-secret configuration values. Not encrypted. Visible in logs. Use for non-sensitive config.

```bash
# Set variable
gh variable set NODE_VERSION --body "20"
gh variable set DEPLOY_REGION --env production --body "us-east-1"
```

```yaml
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: ${{ vars.NODE_VERSION }}
```

| Feature | Secrets | Variables |
|---------|---------|-----------|
| Encrypted | Yes | No |
| Masked in logs | Yes | No |
| Max size | 48 KB | 48 KB |
| Max count (repo) | 1000 | 1000 |
| Use for | API keys, tokens, passwords | Versions, regions, feature flags |

## Environments

Environments group secrets and protection rules for deployment targets.

### Creating Environments

Settings > Environments > New environment. Common: `development`, `staging`, `production`.

### Referencing Environments

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
    steps:
      - run: deploy --env production
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # Environment-scoped secret
```

### Protection Rules

| Rule | Purpose | Configuration |
|------|---------|--------------|
| Required reviewers | Manual approval before deploy | 1-6 reviewers, any one approves |
| Wait timer | Delay after approval | 0-43200 minutes (up to 30 days) |
| Deployment branches | Limit which branches can deploy | Selected branches or patterns |
| Custom protection rules | Third-party checks (e.g., change management) | GitHub App integration |

### Approval Workflow

```yaml
jobs:
  deploy-staging:
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - run: deploy-to-staging.sh

  deploy-production:
    needs: deploy-staging
    environment: production          # Triggers approval gate
    runs-on: ubuntu-latest
    steps:
      - run: deploy-to-production.sh
```

When `deploy-production` reaches the `environment: production` reference, GitHub pauses the job and notifies reviewers. The job resumes only after approval.

## OIDC Federation

OIDC eliminates long-lived cloud credentials. GitHub issues a short-lived JWT that the cloud provider trusts directly.

### How It Works

```
1. Workflow requests OIDC token from GitHub
2. GitHub issues JWT with claims (repo, branch, workflow, actor)
3. Workflow sends JWT to cloud provider's token endpoint
4. Cloud provider validates JWT against GitHub's OIDC issuer
5. Cloud provider returns short-lived cloud credentials
6. Workflow uses cloud credentials for deployment
```

### JWT Claims

| Claim | Example | Use |
|-------|---------|-----|
| `iss` | `https://token.actions.githubusercontent.com` | Issuer validation |
| `sub` | `repo:owner/repo:ref:refs/heads/main` | Trust policy matching |
| `aud` | `https://github.com/owner` | Audience validation |
| `repository` | `owner/repo` | Repo filter |
| `ref` | `refs/heads/main` | Branch filter |
| `environment` | `production` | Environment filter |
| `workflow` | `.github/workflows/deploy.yml` | Workflow filter |

### AWS OIDC Setup

1. Create OIDC identity provider in AWS IAM:
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`

2. Create IAM role with trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main"
      }
    }
  }]
}
```

3. Use in workflow:

```yaml
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      - run: aws s3 sync dist/ s3://my-bucket/
```

### GCP OIDC Setup

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/PROJECT_NUM/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
    service_account: deploy@project.iam.gserviceaccount.com
```

### Azure OIDC Setup

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### OIDC Trust Policy Best Practices

| Practice | Why |
|----------|-----|
| Restrict `sub` to specific repo + branch | Prevent other repos from assuming the role |
| Add environment claim filter | Limit to production environment only |
| Use `StringEquals` not `StringLike` when possible | Prevent wildcard abuse |
| Audit trust policies regularly | Repos get renamed, teams change |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Secrets in `run:` interpolation | Visible in process table | Map to `env:` variable |
| Broad GITHUB_TOKEN permissions | Unnecessary write access | Set `permissions: {}` top-level, grant per-job |
| Long-lived cloud credentials | Rotation burden, leak risk | Use OIDC federation |
| No branch restriction on OIDC | Any branch can deploy to production | Add branch/environment claim to trust policy |
| Same secrets for all environments | Staging can access production credentials | Use environment-scoped secrets |
| Missing `id-token: write` | OIDC token request fails | Add to job permissions |
