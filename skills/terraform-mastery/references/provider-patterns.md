# Provider Patterns

Sources: HashiCorp Provider Documentation (v1.9+), AWS Provider Documentation (v5.x), Google Provider Documentation (v5.x), AzureRM Provider Documentation (v3.x), Brikman (Terraform: Up & Running, 3rd ed.)

Covers: Provider configuration, version pinning, multi-region and multi-account patterns, provider aliases, authentication methods (static credentials, environment variables, OIDC, assume role), and data source patterns.

## Provider Configuration

### Basic Setup

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.5.0"
}
```

### Version Pinning Strategy

| Constraint | Meaning | When to Use |
|-----------|---------|-------------|
| `~> 5.0` | >= 5.0.0, < 6.0.0 | Production -- allows patches, blocks breaking |
| `~> 5.40.0` | >= 5.40.0, < 5.41.0 | Strict -- patch updates only |
| `>= 5.0, < 6.0` | Explicit range | Same as `~> 5.0` but more readable |
| `= 5.40.0` | Exact version | Maximum reproducibility, manual updates |

Always commit `.terraform.lock.hcl` -- it pins the exact provider version and checksums. Run `terraform init -upgrade` to update within constraints.

## Authentication Patterns

### AWS Authentication Hierarchy

Terraform AWS provider resolves credentials in this order:

1. Provider block `access_key` / `secret_key` (avoid -- secrets in code)
2. Environment variables `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
3. Shared credentials file (`~/.aws/credentials`)
4. ECS task role / EC2 instance profile
5. SSO / OIDC token

### Static Credentials (Development Only)

```hcl
provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key    # From tfvars, never hardcoded
  secret_key = var.aws_secret_key
}
```

Never commit static credentials. Use for local development with short-lived keys only.

### Environment Variables

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI..."
export AWS_REGION="us-east-1"
```

Provider inherits automatically -- no credentials in HCL:

```hcl
provider "aws" {
  region = "us-east-1"
}
```

### OIDC Authentication (CI/CD)

Preferred for GitHub Actions, GitLab CI, and other CI systems. No long-lived secrets.

```hcl
# AWS OIDC setup
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}

resource "aws_iam_role" "terraform" {
  name = "terraform-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:myorg/infra:*"
        }
      }
    }]
  })
}
```

GitHub Actions workflow:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/terraform-github-actions
      aws-region: us-east-1
```

### Assume Role (Cross-Account)

```hcl
provider "aws" {
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::987654321098:role/terraform-deployer"
    session_name = "terraform-prod"
    external_id  = "unique-external-id"
  }
}
```

### GCP Authentication

```bash
# Local development
gcloud auth application-default login

# CI/CD: use workload identity federation or service account key (less preferred)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

### Azure Authentication

```hcl
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  use_oidc        = true    # For CI/CD with OIDC
}
```

## Multi-Region Patterns

### Provider Aliases

```hcl
provider "aws" {
  region = "us-east-1"
  alias  = "us_east"
}

provider "aws" {
  region = "eu-west-1"
  alias  = "eu_west"
}

resource "aws_s3_bucket" "us_data" {
  provider = aws.us_east
  bucket   = "myapp-data-us"
}

resource "aws_s3_bucket" "eu_data" {
  provider = aws.eu_west
  bucket   = "myapp-data-eu"
}
```

### Passing Providers to Modules

```hcl
module "us_east_vpc" {
  source = "./modules/vpc"
  providers = {
    aws = aws.us_east
  }
  vpc_cidr = "10.0.0.0/16"
}

module "eu_west_vpc" {
  source = "./modules/vpc"
  providers = {
    aws = aws.eu_west
  }
  vpc_cidr = "10.1.0.0/16"
}
```

Module declares provider requirement without configuring it:

```hcl
# modules/vpc/versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

Modules inherit the provider from the caller. Never configure providers inside reusable modules.

## Multi-Account Patterns

### Hub-Spoke with Assume Role

```hcl
# Management account provider (default)
provider "aws" {
  region = "us-east-1"
}

# Production account
provider "aws" {
  alias  = "production"
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/terraform"
  }
}

# Staging account
provider "aws" {
  alias  = "staging"
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/terraform"
  }
}
```

### Per-Account State Files

Prefer separate root modules and state files per account rather than managing all accounts from one state:

```
accounts/
  production/
    backend.tf    # S3 key: prod/terraform.tfstate
    main.tf
  staging/
    backend.tf    # S3 key: staging/terraform.tfstate
    main.tf
```

## Data Sources

### Common Data Source Patterns

```hcl
# Look up the latest AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Look up existing VPC
data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["production-vpc"]
  }
}

# Look up current account/caller identity
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Look up availability zones
data "aws_availability_zones" "available" {
  state = "available"
}
```

### Remote State Data Source

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "mycompany-terraform-state"
    key    = "prod/network/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from the remote state
resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.private_subnet_ids[0]
}
```

### External Data Source

Call external programs for dynamic data:

```hcl
data "external" "git_sha" {
  program = ["bash", "-c", "echo '{\"sha\": \"'$(git rev-parse --short HEAD)'\"}'"]
}

locals {
  git_sha = data.external.git_sha.result.sha
}
```

Use sparingly -- external data sources break reproducibility.

## Provider-Specific Patterns

### AWS Default Tags

```hcl
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "terraform"
      Team        = var.team
    }
  }
}
```

All AWS resources inherit these tags automatically. Override per-resource when needed.

### Google Labels

```hcl
provider "google" {
  project               = var.project_id
  region                = var.region
  default_labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
```

### Azure Features Block

```hcl
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}
```

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Provider configured inside module | Module cannot be reused across accounts/regions | Declare provider requirement, let caller configure |
| Unpinned provider version | Upgrades break configuration silently | Pin with `~> X.0` at minimum |
| Static credentials in code | Secrets leak to version control | Use env vars, OIDC, or assume role |
| Missing `.terraform.lock.hcl` | Different team members get different provider versions | Commit the lock file |
| No default tags | Inconsistent tagging across resources | Use provider `default_tags` |
| Hardcoded account IDs | Config only works in one account | Use `data.aws_caller_identity.current.account_id` |
