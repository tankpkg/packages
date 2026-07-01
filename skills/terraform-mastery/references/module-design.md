# Module Design

Sources: HashiCorp Module Documentation (v1.9+), Terraform Registry Publishing Guide, Brikman (Terraform: Up & Running, 3rd ed.), AWS Prescriptive Guidance for Terraform Modules

Covers: Module anatomy, composition patterns, variable design with validation, output conventions, versioning strategies, registry publishing, and anti-patterns.

## Module Anatomy

A well-structured module has a predictable file layout:

```
modules/vpc/
  main.tf           # Primary resources
  variables.tf      # Input variable declarations
  outputs.tf        # Output declarations
  versions.tf       # Required providers and Terraform version
  data.tf           # Data sources (optional)
  locals.tf         # Computed locals (optional)
  README.md         # Auto-generated with terraform-docs
```

### File Responsibilities

| File | Contains | Rules |
|------|----------|-------|
| `main.tf` | Resource definitions | Core logic only |
| `variables.tf` | All `variable` blocks | Types, descriptions, validations |
| `outputs.tf` | All `output` blocks | Descriptions required |
| `versions.tf` | `required_providers` and `required_version` | Pin ranges, not exact |
| `data.tf` | Data source lookups | Separate from resources for clarity |
| `locals.tf` | Computed values, name prefixes, tags | Avoid complex chains |

## Module Design Principles

### Single Responsibility

One module manages one logical component:

| Good | Bad |
|------|-----|
| `modules/vpc` -- only VPC resources | `modules/infrastructure` -- everything |
| `modules/rds` -- one database | `modules/app` -- compute + DB + DNS |
| `modules/ecs-service` -- one service | `modules/platform` -- all services |

### Minimal Interface

Expose only what consumers need. Too many variables create a brittle interface.

```hcl
# Good: focused interface
variable "name" { type = string }
variable "vpc_cidr" { type = string }
variable "availability_zones" { type = list(string) }

# Bad: leaking implementation details
variable "nat_gateway_elastic_ip_allocation_id" { type = string }
variable "route_table_propagation_enabled" { type = bool }
```

### Sensible Defaults

Provide defaults for optional configuration:

```hcl
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type for the application server"
}

variable "volume_config" {
  type = object({
    size      = number
    type      = optional(string, "gp3")
    iops      = optional(number, 3000)
    encrypted = optional(bool, true)
  })
  description = "EBS volume configuration"
}
```

### Explicit Over Implicit

Do not read `terraform.workspace` or environment variables inside modules. Pass values explicitly:

```hcl
# Module call -- values passed explicitly
module "vpc" {
  source      = "./modules/vpc"
  environment = var.environment    # Passed from root
  vpc_cidr    = "10.0.0.0/16"
}
```

## Variable Validation

Add validation rules as contract tests:

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cidr_block" {
  type        = string
  description = "VPC CIDR block"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block (e.g., 10.0.0.0/16)."
  }
}

variable "port" {
  type        = number
  description = "Application port"

  validation {
    condition     = var.port > 0 && var.port <= 65535
    error_message = "Port must be between 1 and 65535."
  }
}

variable "name" {
  type        = string
  description = "Resource name prefix"

  validation {
    condition     = length(var.name) >= 3 && length(var.name) <= 24
    error_message = "Name must be 3-24 characters."
  }

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with a letter and contain only lowercase alphanumerics and hyphens."
  }
}
```

Multiple `validation` blocks on one variable enforce all rules independently.

## Output Conventions

```hcl
output "vpc_id" {
  description = "The ID of the created VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = [for s in aws_subnet.private : s.id]
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

| Convention | Reason |
|-----------|--------|
| Always add `description` | Consumers discover outputs via docs |
| Mark sensitive outputs | Prevents accidental exposure in logs |
| Output IDs, ARNs, endpoints | These are what downstream modules need |
| Use consistent naming | `*_id`, `*_arn`, `*_endpoint`, `*_name` |

## Composition Patterns

### Flat Composition

Root module calls multiple child modules:

```hcl
module "vpc" {
  source = "./modules/vpc"
  # ...
}

module "rds" {
  source     = "./modules/rds"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

module "ecs" {
  source       = "./modules/ecs"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
  database_url = module.rds.endpoint
}
```

Prefer flat composition. The root module is the orchestrator -- child modules are independent components wired together.

### Nested Composition

A parent module wraps child modules for a higher-level abstraction:

```hcl
# modules/application-stack/main.tf
module "network" {
  source   = "../network"
  vpc_cidr = var.vpc_cidr
}

module "database" {
  source     = "../database"
  vpc_id     = module.network.vpc_id
  subnet_ids = module.network.private_subnet_ids
}
```

Use nested composition sparingly. It hides complexity but creates deep dependency chains that are harder to debug.

### Cross-State Data Sharing

When modules live in separate state files, use `terraform_remote_state` or data sources:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "mycompany-terraform-state"
    key    = "prod/network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.private_subnet_ids[0]
}
```

Alternative: use SSM Parameter Store, Consul, or cloud-native service discovery to decouple state files.

## Versioning

### Git Tags

```bash
git tag -a "vpc-v1.2.0" -m "Add IPv6 support"
git push origin "vpc-v1.2.0"
```

Reference in consumers:

```hcl
module "vpc" {
  source  = "git::https://github.com/myorg/terraform-modules.git//modules/vpc?ref=vpc-v1.2.0"
}
```

### Semver Conventions

| Change | Bump | Example |
|--------|------|---------|
| New optional variable with default | Minor | 1.1.0 -> 1.2.0 |
| Bug fix, no interface change | Patch | 1.2.0 -> 1.2.1 |
| Remove variable, rename output | Major | 1.2.1 -> 2.0.0 |
| Change required variable type | Major | Breaking change |
| Add new output | Minor | Non-breaking addition |

### Version Constraints

```hcl
module "vpc" {
  source  = "app.terraform.io/myorg/vpc/aws"
  version = "~> 1.2"   # Allows 1.2.x but not 1.3.0
}
```

| Constraint | Meaning |
|-----------|---------|
| `= 1.2.0` | Exact version |
| `~> 1.2` | >= 1.2.0, < 2.0.0 |
| `~> 1.2.0` | >= 1.2.0, < 1.3.0 |
| `>= 1.0, < 2.0` | Explicit range |

## Registry Publishing

### Terraform Registry (Public)

Repository naming convention: `terraform-<PROVIDER>-<NAME>`

```
terraform-aws-vpc
terraform-google-network
terraform-azurerm-vnet
```

Required files: `main.tf`, `variables.tf`, `outputs.tf`, `README.md`

Tag releases with semver: `v1.0.0`

### Private Registry (HCP Terraform)

Publish via API or VCS connection. Supports automatic testing before release. Pin in consumers with `version` constraint.

## Module Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| God module | One module manages everything | Split by responsibility |
| Provider in module | Module declares provider | Consumer declares provider, module inherits |
| Hardcoded regions/accounts | Module only works in one context | Pass as variables |
| Reading `terraform.workspace` | Module coupled to workspace name | Accept `environment` as variable |
| No variable descriptions | Consumers cannot discover usage | Add description to every variable |
| No outputs | Downstream modules cannot reference | Output all IDs, ARNs, endpoints |
| Deeply nested modules (3+ levels) | Hard to debug, slow plans | Flatten to 1-2 levels max |
| Unpinned module versions | Breaking changes propagate silently | Always pin with `version` or `ref` |
| Monorepo without tags | All modules version together | Use per-module tags or separate repos |
| Copy-paste instead of modules | Drift between copies | Extract shared logic into a module |

## terraform-docs

Auto-generate module documentation:

```bash
# Install
brew install terraform-docs

# Generate markdown table format
terraform-docs markdown table ./modules/vpc > ./modules/vpc/README.md

# Use .terraform-docs.yml for consistent formatting
```

Configuration file:

```yaml
formatter: markdown table
output:
  file: README.md
  mode: inject
sort:
  enabled: true
  by: required
```

Run terraform-docs in CI to keep docs synchronized with code.
