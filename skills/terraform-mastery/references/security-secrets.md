# Security and Secrets

Sources: HashiCorp Terraform Security Documentation, OWASP Infrastructure as Code Security Cheat Sheet, Checkov Documentation, tfsec Documentation, HashiCorp Vault Integration Guide, AWS Well-Architected Framework (Security Pillar)

Covers: Secrets management in Terraform, sensitive variable handling, encryption patterns, least-privilege IAM for Terraform, drift detection, compliance scanning, .gitignore configuration, and state file security.

## Secrets Management

### The Problem

Terraform manages infrastructure that often requires secrets: database passwords, API keys, TLS certificates. These secrets must flow through Terraform without being exposed in:

- Version control (`.tf` files, `.tfvars`)
- State files (stored as plaintext JSON by default)
- Plan output (logged in CI)
- Terminal output

### Secret Injection Methods

| Method | Security | Use Case |
|--------|----------|----------|
| Environment variables | Medium | CI/CD pipelines |
| `-var` CLI flag | Medium | One-off operations |
| `.tfvars` (gitignored) | Medium | Local development |
| Secrets manager data source | High | Production |
| Provider-managed secrets | Highest | AWS RDS, GCP SQL |
| Vault integration | Highest | Enterprise secrets |

### Environment Variables

```bash
export TF_VAR_database_password="secret123"
export TF_VAR_api_key="sk-abc..."
```

Terraform auto-reads `TF_VAR_<name>` for variable `<name>`. Never echo or log these values.

### Secrets Manager Integration

```hcl
# AWS Secrets Manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/database/master-password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

```hcl
# GCP Secret Manager
data "google_secret_manager_secret_version" "db_password" {
  secret = "database-master-password"
}

resource "google_sql_user" "main" {
  password = data.google_secret_manager_secret_version.db_password.secret_data
}
```

```hcl
# Azure Key Vault
data "azurerm_key_vault_secret" "db_password" {
  name         = "database-master-password"
  key_vault_id = data.azurerm_key_vault.main.id
}
```

### Provider-Managed Secrets (Best Option)

Let the cloud provider generate and manage the secret:

```hcl
# AWS RDS managed master password (no secret in Terraform at all)
resource "aws_db_instance" "main" {
  engine                          = "postgres"
  instance_class                  = "db.t3.medium"
  manage_master_user_password     = true
  master_user_secret_kms_key_id   = aws_kms_key.rds.arn
}
```

The password is created by AWS, stored in Secrets Manager, and never appears in Terraform state.

### HashiCorp Vault

```hcl
provider "vault" {
  address = "https://vault.company.com"
}

data "vault_generic_secret" "db" {
  path = "secret/data/production/database"
}

resource "aws_db_instance" "main" {
  password = data.vault_generic_secret.db.data["password"]
}
```

## Sensitive Variable Handling

### Mark Variables Sensitive

```hcl
variable "database_password" {
  type        = string
  sensitive   = true
  description = "Master database password"
}

output "connection_string" {
  value     = "postgres://admin:${var.database_password}@${aws_db_instance.main.endpoint}/app"
  sensitive = true
}
```

`sensitive = true` prevents the value from appearing in `terraform plan` and `terraform apply` output. It does NOT encrypt the value in state.

### Sensitive Expressions

Terraform propagates sensitivity. If a variable is sensitive, any expression using it is also sensitive:

```hcl
locals {
  # This local is automatically sensitive because it references a sensitive variable
  db_url = "postgres://admin:${var.database_password}@${aws_db_instance.main.endpoint}/app"
}
```

### nonsensitive() Function

Override sensitivity when the derived value is no longer secret:

```hcl
output "password_length" {
  value = nonsensitive(length(var.database_password))
}
```

Use sparingly -- ensure the output genuinely does not leak the secret.

## Encryption

### State Encryption

| Backend | Encryption Method |
|---------|------------------|
| S3 | `encrypt = true` + KMS key |
| GCS | Default encryption (Google-managed or CMEK) |
| Azure | Storage service encryption (Microsoft-managed or customer key) |
| HCP Terraform | Encrypted at rest by default |

### KMS Key for State

```hcl
resource "aws_kms_key" "terraform" {
  description             = "Terraform state encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::123456789012:role/terraform"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### Resource Encryption

Enforce encryption on all storage resources:

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_ebs_default_encryption" "main" {
  enabled    = true
  kms_key_id = aws_kms_key.ebs.arn
}

resource "aws_rds_cluster" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}
```

## Least-Privilege IAM for Terraform

### Principle

Grant Terraform only the permissions it needs. Avoid `*` actions and `*` resources.

### AWS IAM Policy for Terraform Role

```hcl
resource "aws_iam_policy" "terraform" {
  name = "terraform-deployer"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EC2Management"
        Effect   = "Allow"
        Action   = [
          "ec2:Describe*",
          "ec2:CreateVpc",
          "ec2:DeleteVpc",
          "ec2:CreateSubnet",
          "ec2:DeleteSubnet",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = ["us-east-1", "eu-west-1"]
          }
        }
      },
      {
        Sid      = "StateAccess"
        Effect   = "Allow"
        Action   = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::mycompany-terraform-state",
          "arn:aws:s3:::mycompany-terraform-state/*"
        ]
      },
      {
        Sid      = "StateLocking"
        Effect   = "Allow"
        Action   = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:us-east-1:123456789012:table/terraform-locks"
      }
    ]
  })
}
```

### Scope by Environment

Use separate IAM roles per environment. Production role has tighter constraints and requires MFA or OIDC.

## Compliance Scanning

### Checkov

```bash
checkov -d . --framework terraform
checkov -d . --check CKV_AWS_145    # Run specific check
checkov -d . --skip-check CKV_AWS_18  # Skip specific check
```

| Check Category | Examples |
|---------------|---------|
| Encryption | S3, EBS, RDS encryption enabled |
| Public access | S3 public access blocked, SG not open to 0.0.0.0/0 |
| Logging | CloudTrail, VPC flow logs, access logging |
| Network | Private subnets, no public IPs on sensitive resources |
| IAM | No wildcard actions, MFA enforcement |

### tfsec

```bash
tfsec .
tfsec . --minimum-severity HIGH
tfsec . --format json > results.json
```

### Trivy (IaC Scanning)

```bash
trivy config .
trivy config --severity HIGH,CRITICAL ./terraform/
```

## .gitignore Configuration

```gitignore
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
!example.tfvars
.terraform/
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Keep the lock file
!.terraform.lock.hcl

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
```

Never commit state files, `.terraform/` directory, or `.tfvars` files containing secrets. Always commit `.terraform.lock.hcl`.

## Drift Detection

### Scheduled Detection

```yaml
# GitHub Actions - daily drift check
name: Drift Detection

on:
  schedule:
    - cron: "0 8 * * 1-5"  # Weekdays at 8 AM

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3

      - run: terraform init
        working-directory: terraform/environments/production

      - name: Check Drift
        id: drift
        run: |
          terraform plan -refresh-only -detailed-exitcode -no-color 2>&1 | tee drift.txt
          echo "exitcode=${PIPESTATUS[0]}" >> $GITHUB_OUTPUT
        working-directory: terraform/environments/production
        continue-on-error: true

      - name: Alert on Drift
        if: steps.drift.outputs.exitcode == '2'
        run: |
          echo "::warning::Drift detected in production!"
          # Send Slack notification or create GitHub issue
```

### Exit Code Meaning

| Exit Code | Meaning |
|-----------|---------|
| 0 | No changes (no drift) |
| 1 | Error |
| 2 | Changes detected (drift found) |

## Common Security Pitfalls

| Pitfall | Risk | Fix |
|---------|------|-----|
| Secrets in `.tf` files | Exposed in version control | Use secrets manager or env vars |
| Secrets in state | State readable by anyone with backend access | Encrypt state, restrict access |
| `sensitive = true` missing | Secrets appear in plan output | Mark all secret variables sensitive |
| Over-permissive IAM for TF | Blast radius of compromised credentials | Least-privilege, scoped to environment |
| No state encryption | Data at rest exposure | Enable encryption on backend |
| `.tfvars` committed | Secrets in Git history | Add to `.gitignore`, use `git-secrets` |
| Public state bucket | Anyone can read state | Block public access, restrict IAM |
