# Project Structure

Sources: Brikman (Terraform: Up & Running, 3rd ed.), AWS Prescriptive Guidance for Terraform, Terragrunt Documentation, Gruntwork Reference Architecture, Google Cloud Terraform Best Practices

Covers: Directory layout patterns, file naming conventions, environment separation strategies, Terragrunt DRY patterns, monorepo vs polyrepo, tagging standards, and the OpenTofu alternative.

## Directory Layout

### Standard Layout

```
infrastructure/
  modules/                          # Reusable modules
    vpc/
      main.tf
      variables.tf
      outputs.tf
      versions.tf
      README.md
    rds/
    ecs-service/
    lambda/

  environments/                     # Environment-specific configs
    production/
      network/
        main.tf
        variables.tf
        backend.tf
        terraform.tfvars
      data/
        main.tf
        backend.tf
        terraform.tfvars
      compute/
        main.tf
        backend.tf
        terraform.tfvars
    staging/
      network/
      data/
      compute/
    development/
      network/
      data/
      compute/

  global/                           # Shared across all environments
    iam/
    dns/
    state-backend/
```

### Layer-Based Separation

Split by blast radius and change frequency:

| Layer | Contents | Change Frequency | Blast Radius |
|-------|----------|-----------------|--------------|
| `global/` | IAM roles, Route53 zones, state bucket | Rarely | High |
| `network/` | VPC, subnets, NAT, peering, VPN | Rarely | High |
| `data/` | RDS, ElastiCache, S3 data buckets | Occasionally | Medium |
| `compute/` | ECS, EKS, Lambda, ASGs | Often | Medium |
| `app/` | App-specific resources, configs | Very often | Low |

Each layer has its own state file. A bad apply to `compute/` cannot destroy the database in `data/`.

### File Naming Convention

| File | Purpose |
|------|---------|
| `main.tf` | Primary resource definitions and module calls |
| `variables.tf` | All `variable` blocks |
| `outputs.tf` | All `output` blocks |
| `providers.tf` | Provider configuration blocks |
| `versions.tf` | `required_providers` and `required_version` |
| `backend.tf` | Backend configuration |
| `data.tf` | Data source lookups |
| `locals.tf` | Computed local values |
| `terraform.tfvars` | Variable values (gitignored if secrets) |
| `example.tfvars` | Example values for documentation (committed) |

For small modules, consolidate into `main.tf` + `variables.tf` + `outputs.tf`. Split into additional files only when `main.tf` exceeds ~200 lines.

## Environment Separation

### Separate Directories (Recommended)

Each environment is a separate root module with its own backend:

```hcl
# environments/production/network/backend.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "production/network/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

```hcl
# environments/production/network/main.tf
module "vpc" {
  source             = "../../../modules/vpc"
  environment        = "production"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
```

### Workspaces (Simple Cases)

When environments share identical configuration except for variable values:

```bash
terraform workspace new staging
terraform workspace new production
```

```hcl
# main.tf
locals {
  config = {
    staging = {
      instance_type = "t3.small"
      instance_count = 1
    }
    production = {
      instance_type = "m5.large"
      instance_count = 3
    }
  }
  env = local.config[terraform.workspace]
}
```

### When to Use Which

| Signal | Approach |
|--------|----------|
| Same resources, different sizes | Workspaces |
| Different resources per env | Separate directories |
| Need strict access control per env | Separate directories + separate backends |
| Team manages 2-3 environments | Either works |
| Managing 10+ environments/tenants | Terragrunt |

## Terragrunt Patterns

### What Terragrunt Solves

| Problem | Terraform | Terragrunt |
|---------|-----------|-----------|
| DRY backend configuration | Copy-paste backend blocks | Generate from `terragrunt.hcl` |
| DRY provider configuration | Copy-paste providers | Generate from parent config |
| Multi-environment variable management | Separate `.tfvars` per env | Hierarchical `inputs` |
| Dependency ordering across stacks | Manual `terraform_remote_state` | `dependency` blocks |
| Running plan/apply across stacks | Scripting or CI for each dir | `terragrunt run-all plan` |

### Directory Structure

```
infrastructure/
  terragrunt.hcl                    # Root config (backend, provider)
  modules/
    vpc/
    rds/
    ecs/

  environments/
    production/
      terragrunt.hcl                # Environment-level inputs
      network/
        terragrunt.hcl              # Stack-level config
      data/
        terragrunt.hcl
      compute/
        terragrunt.hcl
    staging/
      terragrunt.hcl
      network/
        terragrunt.hcl
```

### Root Configuration

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "mycompany-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Environment = "${basename(get_terragrunt_dir())}"
    }
  }
}
EOF
}
```

### Stack Configuration with Dependencies

```hcl
# environments/production/compute/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules/ecs"
}

dependency "network" {
  config_path = "../network"
}

dependency "data" {
  config_path = "../data"
}

inputs = {
  environment        = "production"
  vpc_id             = dependency.network.outputs.vpc_id
  private_subnet_ids = dependency.network.outputs.private_subnet_ids
  database_endpoint  = dependency.data.outputs.endpoint
  instance_type      = "m5.large"
  desired_count      = 3
}
```

### Terragrunt Commands

```bash
# Plan a single stack
terragrunt plan

# Plan all stacks in an environment
terragrunt run-all plan

# Apply all stacks in dependency order
terragrunt run-all apply

# Destroy in reverse dependency order
terragrunt run-all destroy
```

## Monorepo vs Polyrepo

| Factor | Monorepo | Polyrepo |
|--------|----------|----------|
| Module discoverability | All modules in one place | Spread across repos |
| Versioning | Must use per-module tags | Natural repo-level semver |
| CI/CD complexity | Path-based triggers needed | Simple per-repo triggers |
| Code review | Single PR can span modules | Cross-repo changes need multiple PRs |
| Access control | Fine-grained with CODEOWNERS | Repo-level permissions |
| Dependency management | Local paths during dev, tags for release | Always remote references |

### Monorepo with Per-Module Tags

```bash
# Tag specific modules
git tag "modules/vpc/v1.2.0"
git tag "modules/rds/v2.0.0"
```

### Polyrepo with Separate Module Repos

```
github.com/myorg/terraform-aws-vpc       (one module per repo)
github.com/myorg/terraform-aws-rds
github.com/myorg/infra-production         (environment repo)
```

## Tagging Standards

### Mandatory Tags

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
    Team        = var.team
    CostCenter  = var.cost_center
  }
}
```

### Provider Default Tags

```hcl
provider "aws" {
  default_tags {
    tags = local.common_tags
  }
}
```

All resources inherit these tags. Override per-resource only when needed.

### Tag Enforcement

Use Sentinel, OPA, or Checkov to block untagged resources:

```rego
# policy/require_tags.rego
package main

required_tags := {"Environment", "Project", "ManagedBy", "Team"}

deny[msg] {
  resource := input.resource_changes[_]
  tags := object.get(resource.change.after, "tags", {})
  missing := required_tags - {key | tags[key]}
  count(missing) > 0
  msg := sprintf("Resource '%s' missing tags: %v", [resource.address, missing])
}
```

## OpenTofu

OpenTofu is the open-source fork of Terraform (post-BSL license change). It maintains CLI and HCL compatibility.

### Key Differences

| Feature | Terraform | OpenTofu |
|---------|-----------|----------|
| License | BSL 1.1 (source-available) | MPL 2.0 (open-source) |
| Registry | registry.terraform.io | registry.opentofu.org (mirrors Terraform) |
| CLI command | `terraform` | `tofu` |
| State encryption | Via backend only | Native client-side encryption (v1.7+) |
| Provider lock file | `.terraform.lock.hcl` | Same format |
| Early variable evaluation | No | Yes (v1.8+) |

### Migration

```bash
# Install OpenTofu
brew install opentofu

# Replace terraform with tofu (same commands)
tofu init
tofu plan
tofu apply
```

Existing state files, modules, and provider configurations work without changes. The `.terraform.lock.hcl` file is compatible.

### OpenTofu State Encryption

```hcl
terraform {
  encryption {
    key_provider "pbkdf2" "main" {
      passphrase = var.state_encryption_passphrase
    }
    method "aes_gcm" "main" {
      keys = key_provider.pbkdf2.main
    }
    state {
      method   = method.aes_gcm.main
      enforced = true
    }
  }
}
```

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| One giant state file | Slow plans, huge blast radius | Split by layer and environment |
| Copy-paste across environments | Drift between copies | Use modules + Terragrunt |
| No backend configuration | State lost, no collaboration | Configure remote backend first |
| Missing `.terraform.lock.hcl` in Git | Version inconsistency | Always commit the lock file |
| No tagging standard | Cannot track costs or ownership | Enforce tags via default_tags + policy |
| Environment config in module | Module not reusable | Pass environment as variable |
| No example.tfvars | New team members cannot start | Commit example.tfvars with dummy values |

## Structure Review Questions

1. Is this project split by environment, by layer, or by product boundary intentionally?
2. Does the state layout match team ownership and blast-radius expectations?
3. Would a new engineer know where to add one resource without copying a bad pattern?
