# CI/CD Pipelines

Sources: HashiCorp Terraform CI/CD Documentation, AWS DevOps Blog (Terraform CI/CD with Test Framework), Buildkite Terraform Best Practices Guide, Atlantis Documentation, Infracost Documentation, GitHub Actions Documentation

Covers: Plan-on-PR and apply-on-merge workflows, GitHub Actions and GitLab CI pipelines, Atlantis setup, OIDC authentication in CI, cost estimation with Infracost, approval gates, and pipeline security.

## Pipeline Architecture

### Standard Workflow

```
PR Created/Updated:
  1. terraform fmt -check
  2. terraform validate
  3. tflint
  4. checkov (security scan)
  5. terraform plan
  6. Infracost (cost estimate)
  7. Post plan + cost as PR comment

PR Approved + Merged:
  8. terraform plan (re-plan on main)
  9. Manual approval gate
  10. terraform apply
  11. Post-apply verification
```

### Principles

| Principle | Reason |
|-----------|--------|
| Plan on PR, apply on merge | Reviewers see exactly what changes |
| Re-plan before apply | Config may have changed since PR |
| No auto-apply to production | Human approval prevents accidents |
| Use OIDC, not static credentials | No long-lived secrets in CI |
| Pin Terraform version | Reproducible across team and CI |
| Cache provider plugins | Faster pipeline execution |

## GitHub Actions

### Full Pipeline

```yaml
name: Terraform

on:
  pull_request:
    branches: [main]
    paths: ["terraform/**"]
  push:
    branches: [main]
    paths: ["terraform/**"]

permissions:
  id-token: write
  contents: read
  pull-requests: write

env:
  TF_VERSION: "1.9.0"
  WORKING_DIR: "terraform/environments/production"

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Format Check
        run: terraform fmt -check -recursive
        working-directory: terraform/

      - name: Init
        run: terraform init -backend=false
        working-directory: ${{ env.WORKING_DIR }}

      - name: Validate
        run: terraform validate
        working-directory: ${{ env.WORKING_DIR }}

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest

      - run: tflint --init
        working-directory: ${{ env.WORKING_DIR }}

      - run: tflint --recursive
        working-directory: ${{ env.WORKING_DIR }}

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: bridgecrewio/checkov-action@v12
        with:
          directory: ${{ env.WORKING_DIR }}
          quiet: true
          soft_fail: false

  plan:
    name: Plan
    needs: [validate, lint, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Init
        run: terraform init
        working-directory: ${{ env.WORKING_DIR }}

      - name: Plan
        id: plan
        run: |
          terraform plan -no-color -out=tfplan 2>&1 | tee plan_output.txt
          echo "exitcode=$?" >> $GITHUB_OUTPUT
        working-directory: ${{ env.WORKING_DIR }}

      - name: Comment Plan on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync(
              '${{ env.WORKING_DIR }}/plan_output.txt', 'utf8'
            );
            const truncated = plan.length > 60000
              ? plan.substring(0, 60000) + '\n... (truncated)'
              : plan;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Terraform Plan\n\`\`\`\n${truncated}\n\`\`\``
            });

  apply:
    name: Apply
    needs: [validate, lint, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Init
        run: terraform init
        working-directory: ${{ env.WORKING_DIR }}

      - name: Apply
        run: terraform apply -auto-approve
        working-directory: ${{ env.WORKING_DIR }}
```

### Environment Protection Rules

Configure in GitHub Settings > Environments > production:
- Required reviewers (1-2 approvers)
- Wait timer (optional delay before deploy)
- Branch restrictions (only `main`)

## GitLab CI

```yaml
# .gitlab-ci.yml
image: hashicorp/terraform:1.9

variables:
  TF_DIR: "terraform/environments/production"

stages:
  - validate
  - plan
  - apply

before_script:
  - cd $TF_DIR
  - terraform init

validate:
  stage: validate
  script:
    - terraform fmt -check -recursive
    - terraform validate
    - tflint --init && tflint

plan:
  stage: plan
  script:
    - terraform plan -out=plan.tfplan
    - terraform show -json plan.tfplan > plan.json
  artifacts:
    paths:
      - $TF_DIR/plan.tfplan
      - $TF_DIR/plan.json
    expire_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_IID

apply:
  stage: apply
  script:
    - terraform apply plan.tfplan
  dependencies:
    - plan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: manual
  environment:
    name: production
```

## Atlantis

Self-hosted Terraform automation triggered by PR comments.

### Setup

```yaml
# atlantis.yaml (repo-level config)
version: 3
projects:
  - name: prod-network
    dir: terraform/environments/production/network
    workspace: default
    autoplan:
      when_modified: ["*.tf", "*.tfvars", "modules/**/*.tf"]
      enabled: true
    apply_requirements: [approved, mergeable]

  - name: prod-compute
    dir: terraform/environments/production/compute
    workspace: default
    autoplan:
      when_modified: ["*.tf", "*.tfvars"]
      enabled: true
    apply_requirements: [approved]
```

### Workflow

1. Open PR -- Atlantis auto-runs `terraform plan` on affected projects
2. Review plan output in PR comment
3. Comment `atlantis apply` after approval
4. Atlantis runs `terraform apply` and posts result

### Atlantis Advantages

| Feature | Benefit |
|---------|---------|
| PR-driven workflow | Plan visible to all reviewers |
| Locking per directory | Prevents concurrent applies |
| Custom workflows | Run tflint, checkov, Infracost |
| Self-hosted | Full control over credentials and network |
| Multi-repo support | Central server, many repos |

## Cost Estimation with Infracost

### Setup

```bash
# Install
brew install infracost

# Authenticate
infracost auth login
```

### CI Integration (GitHub Actions)

```yaml
  cost:
    name: Cost Estimate
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generate Infracost Diff
        run: |
          infracost diff \
            --path=${{ env.WORKING_DIR }} \
            --format=json \
            --out-file=/tmp/infracost.json

      - name: Post Infracost Comment
        run: |
          infracost comment github \
            --path=/tmp/infracost.json \
            --repo=${{ github.repository }} \
            --pull-request=${{ github.event.pull_request.number }} \
            --github-token=${{ github.token }} \
            --behavior=update
```

### Infracost Output

PR comments show:
- Monthly cost estimate for new resources
- Cost difference vs current infrastructure
- Per-resource cost breakdown
- Alerts when cost exceeds configured threshold

### Cost Policies

```yaml
# infracost.yml
version: 0.1
projects:
  - path: terraform/environments/production
    usage_file: infracost-usage.yml

cost_policies:
  - name: max-monthly-cost
    threshold: 5000
    action: warn
```

## Pipeline Security

| Risk | Mitigation |
|------|-----------|
| Secrets in plan output | Mark variables `sensitive = true` |
| Long-lived CI credentials | Use OIDC federation |
| Unauthorized applies | Environment protection rules + required reviewers |
| State file tampering | Encrypt state, restrict backend access |
| Malicious PR modifying pipeline | Branch protection, CODEOWNERS for CI config |
| Concurrent applies | Use state locking or Atlantis project locking |
| Drift between plan and apply | Re-plan on merge, apply saved plan file |

## Provider Plugin Caching

Speed up CI by caching provider downloads:

```yaml
# GitHub Actions
- uses: actions/cache@v4
  with:
    path: ~/.terraform.d/plugin-cache
    key: terraform-plugins-${{ hashFiles('**/.terraform.lock.hcl') }}
    restore-keys: terraform-plugins-

- name: Init with cache
  run: |
    export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
    mkdir -p "$TF_PLUGIN_CACHE_DIR"
    terraform init
```

## Multi-Environment Pipeline Pattern

```
PR to main:
  Plan dev + staging + prod (parallel)
  Post all plans as PR comments

Merge to main:
  Apply dev     -> verify -> Apply staging -> verify -> Apply prod
  (sequential, with gates between environments)
```

Use GitHub environments with required reviewers at each stage. Promote the same plan artifact through environments when possible.

## Pipeline Review Questions

1. Is the same reviewed plan being promoted, or are environments re-planning independently?
2. Are policy checks and security scans placed early enough to stop unsafe plans fast?
3. Is apply protected by human review where the blast radius justifies it?
