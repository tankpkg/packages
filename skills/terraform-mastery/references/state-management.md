# State Management

Sources: HashiCorp Terraform State Documentation (v1.9+), Brikman (Terraform: Up & Running, 3rd ed.), Winkler (Terraform in Action), AWS Prescriptive Guidance for Terraform

Covers: State purpose, remote backends with locking, state encryption, migration between backends, workspaces, state surgery commands, resource import, moved blocks, and drift detection.

## State Purpose

Terraform state is the mapping between configuration and real-world infrastructure. Without state, Terraform cannot:

- Track which real resources correspond to which config blocks
- Detect drift between desired and actual state
- Determine resource dependencies for correct ordering
- Store computed attributes (IDs, ARNs, IPs) needed by other resources

State is stored as JSON. The file contains resource IDs, attribute values (including secrets if not marked sensitive), and dependency metadata.

## Remote Backends

### Why Remote

| Concern | Local State | Remote State |
|---------|-------------|-------------|
| Collaboration | One person at a time | Team access with locking |
| Security | Plaintext on disk | Encrypted at rest |
| Durability | Lost if disk fails | Redundant storage |
| Locking | None | Prevents concurrent applies |
| CI/CD | Must copy state around | Pipeline reads directly |

### S3 Backend (AWS)

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "terraform-locks"
  }
}
```

**Bootstrap the backend** before first use:

```hcl
resource "aws_s3_bucket" "state" {
  bucket = "mycompany-terraform-state"
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### GCS Backend (GCP)

```hcl
terraform {
  backend "gcs" {
    bucket = "mycompany-terraform-state"
    prefix = "prod/networking"
  }
}
```

GCS provides built-in locking and encryption. Enable Object Versioning on the bucket.

### Azure Backend

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "mycompanytfstate"
    container_name       = "tfstate"
    key                  = "prod/networking/terraform.tfstate"
    use_oidc             = true
  }
}
```

### HCP Terraform / Terraform Cloud

```hcl
terraform {
  cloud {
    organization = "mycompany"
    workspaces {
      name = "prod-networking"
    }
  }
}
```

Built-in locking, encryption, run history, and policy enforcement.

## State Key Design

Use a consistent key hierarchy:

```
{environment}/{layer}/terraform.tfstate
```

| Key | Contents |
|-----|----------|
| `prod/network/terraform.tfstate` | VPC, subnets, NAT gateways |
| `prod/data/terraform.tfstate` | RDS, ElastiCache |
| `prod/compute/terraform.tfstate` | ECS, Lambda |
| `staging/network/terraform.tfstate` | Staging VPC |

This maps directly to directory structure and limits blast radius per apply.

## Workspaces

Workspaces create isolated state files within the same backend configuration.

```bash
terraform workspace new staging
terraform workspace new production
terraform workspace select staging
terraform workspace list
```

Access workspace name in configuration:

```hcl
locals {
  environment = terraform.workspace
}

resource "aws_instance" "app" {
  instance_type = terraform.workspace == "production" ? "m5.xlarge" : "t3.micro"
}
```

### When to Use Workspaces

| Use Case | Workspaces? |
|----------|-------------|
| Same config, different environments | Yes |
| Per-customer/tenant isolation | Yes, with dynamic backend keys |
| Fundamentally different infra per env | No -- use separate directories |
| Complex multi-env with shared modules | Terragrunt often better |

### Workspace Pitfalls

- All workspaces share the same backend configuration block
- `terraform.workspace` defaults to `"default"` -- guard against accidental use
- State files share the same access controls -- cannot scope IAM per workspace in S3

## Backend Migration

Move state between backends:

```bash
# 1. Update backend configuration in code
# 2. Run init with migration flag
terraform init -migrate-state

# Interactive prompt: "Do you want to copy existing state?"
# Type "yes" to migrate
```

### Migration from Local to S3

1. Add the `backend "s3"` block to configuration
2. Run `terraform init -migrate-state`
3. Confirm the copy
4. Verify: `terraform state list` returns all resources
5. Delete local `terraform.tfstate` and `.terraform.tfstate.backup`

### Force Unlock

If a apply crashes and leaves a stale lock:

```bash
terraform force-unlock LOCK_ID
```

Use with extreme caution -- only after confirming no other process is running.

## State Surgery

### terraform state list

```bash
terraform state list
terraform state list module.vpc
```

### terraform state show

```bash
terraform state show aws_instance.web
```

### terraform state mv

Rename or move resources without destroy/recreate:

```bash
# Rename a resource
terraform state mv aws_instance.web aws_instance.application

# Move into a module
terraform state mv aws_instance.app module.compute.aws_instance.app

# Move between state files
terraform state mv -state-out=other.tfstate aws_s3_bucket.old aws_s3_bucket.migrated
```

### terraform state rm

Remove a resource from state without destroying it:

```bash
terraform state rm aws_instance.legacy
```

Use when a resource is being managed by another tool or state file.

## Resource Import

### terraform import (CLI)

```bash
terraform import aws_instance.web i-1234567890abcdef0
terraform import 'aws_subnet.private["us-east-1a"]' subnet-abc123
terraform import module.vpc.aws_vpc.main vpc-xyz789
```

Write the matching resource block first, then import. After import, run `terraform plan` to verify no changes.

### import Block (Declarative, v1.5+)

```hcl
import {
  to = aws_instance.web
  id = "i-1234567890abcdef0"
}
```

Run `terraform plan -generate-config-out=generated.tf` to auto-generate the resource configuration from the imported resource.

### Import Workflow

1. Identify the real resource ID (AWS console, CLI, or API)
2. Write the `resource` block or use `import` block with config generation
3. Run `terraform import` or `terraform plan` (for import blocks)
4. Run `terraform plan` -- target zero diff
5. Iterate on the resource block until plan shows no changes
6. Remove the `import` block after successful import

## Moved Blocks

Refactor resource addresses in configuration without destroying infrastructure:

```hcl
moved {
  from = aws_security_group.web
  to   = aws_security_group.application
}

moved {
  from = module.old_name
  to   = module.new_name
}
```

Run `terraform plan` to verify the move is recognized as an in-place rename, not a destroy+create. Remove `moved` blocks after applying to all environments.

## Drift Detection

Drift occurs when real infrastructure diverges from Terraform state.

### Detect Drift

```bash
terraform plan -refresh-only
```

Review the output. Resources showing changes were modified outside Terraform.

### Resolve Drift

| Situation | Action |
|-----------|--------|
| External change is correct | `terraform apply -refresh-only` to update state |
| External change is wrong | `terraform apply` to revert to desired config |
| Resource deleted outside TF | `terraform state rm` then re-import or let TF recreate |

### Continuous Drift Detection

Schedule `terraform plan -refresh-only -detailed-exitcode` in CI. Exit code 2 means drift detected. Alert the team and investigate.

## State Security

| Threat | Mitigation |
|--------|-----------|
| Secrets in state | Mark variables `sensitive = true`; encrypt state at rest |
| Unauthorized access | Restrict backend bucket/blob IAM to Terraform role only |
| State corruption | Enable versioning on the backend bucket |
| Concurrent modification | Always use state locking (DynamoDB, built-in GCS/Azure) |
| State enumeration | Use separate state files per team/project with scoped access |

Never commit `terraform.tfstate` or `.terraform/` to version control. Add both to `.gitignore`.

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| No state locking | Concurrent applies corrupt state | Configure DynamoDB table or use built-in locking |
| Giant monolithic state | Slow plans, large blast radius | Split by layer and environment |
| Backend variables | Backend blocks do not support variables | Use `-backend-config` flags or Terragrunt |
| Manual state edits | Corrupted state, orphaned resources | Always use `terraform state` commands |
| Forgetting `-migrate-state` | Init fails on backend change | Run `terraform init -migrate-state` |
| Lost state file | All resources become unmanaged | Restore from versioned backend or re-import |
