# Secrets and Infrastructure-as-Code Scanning

Sources: Gitleaks documentation, TruffleHog documentation, Checkov documentation (Bridgecrew), tfsec documentation (Aqua Security), OWASP Secrets Management Cheat Sheet

Covers: Secret detection tooling (Gitleaks, TruffleHog, detect-secrets), incident response for leaked credentials, common secret patterns, IaC scanning (Checkov, tfsec, KICS, Trivy), top cloud misconfigurations by provider, and CI pipeline integration.

---

## Secret Detection

Secrets committed to source control are one of the highest-severity, lowest-effort attack vectors. A single leaked AWS key can result in full account compromise within minutes of a public push.

### Tool Selection

| Tool | Strength | Best For |
|------|----------|----------|
| Gitleaks | Git history scanning, pre-commit hooks | General secret detection, CI gates |
| TruffleHog | Credential verification (tests if live) | Incident response, confirmed leaks |
| detect-secrets | Baseline approach, low false positives | Enterprise environments, gradual adoption |
| GitHub Secret Scanning | GitHub-native, partner notifications | GitHub-hosted repos with push protection |

Use Gitleaks as the default CI gate. Add TruffleHog during incident response to confirm whether a leaked credential is still active.

### Gitleaks

**Installation:**

```bash
brew install gitleaks          # macOS
# Linux / CI: download from GitHub releases
```

**Usage:**

```bash
# Scan full history
gitleaks detect --source . --verbose

# Scan only staged changes (pre-commit)
gitleaks protect --staged

# JSON output for downstream processing
gitleaks detect --source . --report-format json --report-path gitleaks-report.json
```

**Configuration — `.gitleaks.toml`:**

```toml
[extend]
useDefault = true

[[rules]]
id = "custom-internal-api-key"
description = "Internal API key pattern"
regex = '''MYAPP_[A-Z0-9]{32}'''
tags = ["api-key", "internal"]

[allowlist]
description = "Global allowlist"
regexes = [
  '''AKIAIOSFODNN7EXAMPLE''',  # Rotated key — safe to ignore in history
]
paths = [
  '''tests/fixtures/''',
]
```

**Pre-commit hook:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

Install with `pre-commit install`. This blocks commits containing detected secrets before they reach the remote.

**Inline suppression:**

```python
EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"  # gitleaks:allow
```

### TruffleHog

TruffleHog actively tests detected credentials against their respective APIs to confirm whether they are valid. This eliminates false positives and prioritizes response effort.

**Usage:**

```bash
# Scan filesystem
trufflehog filesystem . --only-verified

# Scan full git history
trufflehog git file://. --only-verified

# Include unverified results (higher noise, useful for audits)
trufflehog git file://. --include-detectors=all
```

The `--only-verified` flag sends test requests to AWS, GitHub, Slack, Stripe, and 700+ services to confirm the credential is live. A verified result means the secret is active and must be rotated immediately.

Use TruffleHog in incident response mode — not as a primary CI gate — because verification requests may appear in the service's audit logs.

**Supported detector categories (partial):**

| Category | Examples |
|----------|---------|
| Cloud providers | AWS, GCP, Azure |
| Source control | GitHub, GitLab, Bitbucket |
| Communication | Slack, Twilio, SendGrid |
| Payments | Stripe, Square, PayPal |
| CI/CD | CircleCI, Travis CI, Jenkins |

### Incident Response for Leaked Secrets

Execute this procedure in order when a secret is found in git history or a public location. Speed matters: automated scanners harvest newly pushed secrets within seconds.

1. **Rotate the credential immediately.** Revoke the old key and issue a new one before doing anything else.
2. **Audit access logs.** Check the service's audit trail for unauthorized use. For AWS, query CloudTrail; for GitHub tokens, check recent API activity.
3. **Assess blast radius.** Determine what the credential could access and escalate accordingly.
4. **Remove from git history** using BFG Repo-Cleaner (faster) or `git filter-branch`:

```bash
# BFG Repo-Cleaner
java -jar bfg.jar --replace-text secrets.txt repo.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force

# git filter-branch — remove a specific file
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secrets.env' \
  --prune-empty --tag-name-filter cat -- --all
```

Removing from history does not remove the secret from GitHub's cache or any forks. Treat the credential as permanently compromised regardless.

5. **Add the rotated value to the Gitleaks allowlist** to prevent future alerts on the now-harmless historical value.
6. **Install pre-commit hooks** to prevent recurrence.
7. **Notify affected parties** if audit logs show unauthorized access.

### Common Secret Patterns

| Pattern | Format | Risk |
|---------|--------|------|
| AWS access key | `AKIA[A-Z0-9]{16}` | Critical |
| GitHub personal access token | `ghp_[a-zA-Z0-9]{36}` | High |
| GitHub OAuth / Actions token | `gho_` / `ghs_` prefix | High |
| Slack bot token | `xoxb-[0-9]+-[a-zA-Z0-9]+` | High |
| Slack user token | `xoxp-[0-9]+-[a-zA-Z0-9]+` | High |
| Database URL | `postgres://user:pass@host/db` | Critical |
| Private key block | `-----BEGIN RSA PRIVATE KEY-----` | Critical |
| JWT secret (raw) | Long random string assigned to `JWT_SECRET` | High |
| API key in URL | `https://api.example.com?key=abc123` | Medium–High |
| `.env` file committed | Any `.env` in git history | Variable |

Flag any of these patterns during code review regardless of whether automated tools catch them.

---

## Infrastructure-as-Code Scanning

IaC misconfigurations are a leading cause of cloud data breaches. Scanning Terraform, CloudFormation, and Kubernetes manifests before deployment catches issues that are expensive to fix post-deployment.

### Tool Selection

| Tool | IaC Types Supported | Strength |
|------|---------------------|----------|
| Checkov | Terraform, CloudFormation, K8s, Helm, Dockerfile, ARM | Broadest coverage, 1000+ checks |
| tfsec | Terraform | Deep Terraform analysis, fast, low false positives |
| KICS | Terraform, Docker, K8s, Ansible, CloudFormation | Multi-IaC, good for mixed stacks |
| Trivy | Terraform, CloudFormation, Dockerfile, K8s | Single tool if already used for SCA |

Use Checkov as the default for mixed IaC stacks. Use tfsec alongside Checkov for Terraform-heavy projects — it catches issues Checkov misses.

### Checkov

**Installation:**

```bash
pip install checkov
```

**Usage:**

```bash
checkov -d .                                          # Scan directory
checkov -f main.tf                                    # Scan single file
checkov -d . -o json > checkov-results.json           # JSON output
checkov -d . --check CKV_AWS_18,CKV_AWS_20            # Run specific checks
checkov -d . --skip-check CKV_AWS_18                  # Skip specific checks
```

**Key check categories:**

| Category | Example Checks |
|----------|---------------|
| Encryption at rest | S3 SSE, EBS encryption, RDS storage encryption |
| Encryption in transit | ALB HTTPS listeners, RDS SSL enforcement |
| Public access | S3 public access block, RDS `publicly_accessible` |
| Logging | S3 access logging, CloudTrail enabled, VPC flow logs |
| IAM | Wildcard actions, wildcard resources, admin policies |
| Network | Security group ingress `0.0.0.0/0`, default VPC SG |

**Inline suppression:**

```hcl
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  #checkov:skip=CKV_AWS_18:Access logging not required for this internal bucket
}
```

### tfsec

**Installation:**

```bash
brew install tfsec
```

**Usage:**

```bash
tfsec .                                    # Scan current directory
tfsec . --minimum-severity HIGH            # Filter by severity
tfsec . --format json > tfsec-results.json
```

**Key checks by resource:**

| Resource | Check | Risk |
|----------|-------|------|
| `aws_s3_bucket` | Public access block missing | Data exposure |
| `aws_security_group` | Ingress `0.0.0.0/0` on port 22/3389 | Unauthorized access |
| `aws_db_instance` | `publicly_accessible = true` | Database exposure |
| `aws_iam_policy` | Wildcard `*` in actions or resources | Privilege escalation |
| `aws_kms_key` | Key rotation disabled | Compliance failure |
| `azurerm_storage_account` | `allow_blob_public_access = true` | Data exposure |

**Inline suppression:**

```hcl
#tfsec:ignore:aws-s3-enable-versioning:Versioning managed by lifecycle policy
resource "aws_s3_bucket" "example" { ... }
```

### Common IaC Misconfigurations

**AWS:**

| Misconfiguration | Terraform Attribute | Risk |
|-----------------|---------------------|------|
| Public S3 bucket | `block_public_acls = false` | Data exposure |
| Overly permissive IAM | `actions = ["*"]` | Privilege escalation |
| Unencrypted EBS volume | `encrypted = false` | Data at rest exposure |
| Open security group | `cidr_blocks = ["0.0.0.0/0"]` on sensitive ports | Unauthorized access |
| RDS publicly accessible | `publicly_accessible = true` | Database exposure |
| CloudTrail disabled | Missing `aws_cloudtrail` resource | No audit trail |

**GCP:**

| Misconfiguration | Risk |
|-----------------|------|
| Public Cloud Storage bucket | Data exposure |
| Default service account on compute | Overly broad permissions |
| Missing audit logging for admin activity | No audit trail |
| Firewall rule allowing `0.0.0.0/0` on SSH | Unauthorized access |

**Azure:**

| Misconfiguration | Risk |
|-----------------|------|
| Public blob storage container | Data exposure |
| Microsoft Defender for Cloud disabled | Reduced threat detection |
| Missing NSG rules on subnets | Unrestricted lateral movement |
| Storage account allowing HTTP | Data in transit exposure |

**Kubernetes:**

| Misconfiguration | Risk |
|-----------------|------|
| `privileged: true` in security context | Container escape |
| `hostPath` volume mounts | Host filesystem access |
| Missing `NetworkPolicy` resources | Unrestricted pod-to-pod traffic |
| No resource limits (`cpu`, `memory`) | Denial of service via resource exhaustion |
| `automountServiceAccountToken: true` (default) | Token theft from compromised pod |
| Running as root (`runAsNonRoot: false`) | Privilege escalation on container escape |

---

## CI Pipeline Integration

Run secret scanning and IaC scanning as blocking gates on every pull request.

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  pull_request:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history required for secret scanning

      - name: Secret scan (Gitleaks)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: IaC scan (Checkov)
        uses: bridgecrewio/checkov-action@master
        with:
          directory: .
          soft_fail: false
          output_format: sarif
          output_file_path: checkov.sarif

      - name: Upload Checkov SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: checkov.sarif

      - name: IaC scan (tfsec)
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          soft_fail: false
```

**Key pipeline decisions:**

| Decision | Recommendation |
|----------|---------------|
| `fetch-depth` | Always `0` for secret scanning — shallow clones miss history |
| `soft_fail` | `false` for blocking gates; `true` only during initial rollout |
| SARIF upload | Upload to GitHub Security tab for centralized triage |
| Scan scope | Scan the full repository, not just changed files |

**Rollout strategy for existing repositories:**

1. Run in `soft_fail: true` mode for one sprint to baseline findings.
2. Triage results: fix critical findings, add allowlist entries for confirmed false positives.
3. Switch to `soft_fail: false` to enforce the gate.
4. Add pre-commit hooks to catch issues before they reach CI.

Do not skip the baseline phase on large repositories. Blocking CI on day one with hundreds of pre-existing findings creates friction that causes teams to disable scanning entirely.
