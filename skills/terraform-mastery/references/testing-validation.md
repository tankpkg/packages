# Testing and Validation

Sources: HashiCorp Terraform Testing Documentation (v1.9+), HashiCorp Blog (Testing HashiCorp Terraform, Wang 2024), Gruntwork Terratest Documentation, tflint Documentation, Checkov Documentation, Sentinel Documentation

Covers: Terraform native testing framework (terraform test), test file syntax, unit and integration testing, mocking, Terratest patterns, linting with tflint, policy as code (Sentinel, OPA/Conftest), pre-commit hooks, and testing pyramid strategy.

## Testing Pyramid for Infrastructure

| Level | Tool | Creates Resources? | Speed | Cost |
|-------|------|-------------------|-------|------|
| Formatting | `terraform fmt -check` | No | Instant | Free |
| Validation | `terraform validate` | No | Instant | Free |
| Linting | tflint | No | Seconds | Free |
| Policy | Sentinel, OPA/Conftest | No | Seconds | Free |
| Unit tests | `terraform test` (plan) | No | Seconds | Free |
| Contract tests | Variable validation, preconditions | No | Seconds | Free |
| Integration tests | `terraform test` (apply) | Yes | Minutes | Cloud costs |
| E2E tests | Terratest, check blocks | Yes | Minutes-Hours | Cloud costs |

Run lower-level tests first to fail fast and cheap. Reserve integration and E2E tests for module releases and critical paths.

## terraform test (Native Framework)

### File Structure

Test files live in a `tests/` directory or alongside the module:

```
modules/vpc/
  main.tf
  variables.tf
  outputs.tf
  tests/
    unit.tftest.hcl
    integration.tftest.hcl
```

Test files must have the `.tftest.hcl` extension.

### Unit Test (Plan Only)

```hcl
# tests/unit.tftest.hcl

variables {
  vpc_cidr           = "10.0.0.0/16"
  environment        = "test"
  availability_zones = ["us-east-1a", "us-east-1b"]
}

run "verify_vpc_cidr" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block should be 10.0.0.0/16"
  }
}

run "verify_subnet_count" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 2
    error_message = "Should create 2 private subnets"
  }
}

run "verify_tags" {
  command = plan

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "test"
    error_message = "VPC should be tagged with Environment = test"
  }
}
```

Unit tests with `command = plan` do not create real resources. They validate configuration logic, variable transformations, and resource attribute values in the plan.

### Integration Test (Apply)

```hcl
# tests/integration.tftest.hcl

variables {
  vpc_cidr    = "10.99.0.0/16"
  environment = "test"
}

run "create_vpc" {
  command = apply

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC ID should not be empty after apply"
  }

  assert {
    condition     = length(output.private_subnet_ids) > 0
    error_message = "Should have at least one private subnet"
  }
}
```

Integration tests create real resources. Terraform automatically destroys them after the test run.

### Negative Testing

Test that invalid inputs produce expected errors:

```hcl
run "reject_invalid_environment" {
  command = plan

  variables {
    environment = "invalid"
  }

  expect_failures = [
    var.environment
  ]
}

run "reject_tiny_cidr" {
  command = plan

  variables {
    vpc_cidr = "10.0.0.0/30"
  }

  expect_failures = [
    var.vpc_cidr
  ]
}
```

### Test Mocking (v1.7+)

Mock providers and resources to test modules without cloud API calls:

```hcl
# tests/mocked.tftest.hcl

mock_provider "aws" {}

run "test_with_mocked_aws" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == var.vpc_cidr
    error_message = "VPC CIDR should match input variable"
  }
}
```

Override specific resource attributes in mocks:

```hcl
mock_provider "aws" {
  mock_resource "aws_vpc" {
    defaults = {
      id       = "vpc-mock123"
      arn      = "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-mock123"
    }
  }
}
```

Mocks enable fast unit testing without network calls. Be cautious -- mocks may not reflect actual API behavior.

### Running Tests

```bash
# Run all tests
terraform test

# Run specific test file
terraform test -filter=tests/unit.tftest.hcl

# Verbose output
terraform test -verbose

# JSON output for CI parsing
terraform test -json
```

## Terratest (Go)

For complex integration tests that need programmatic assertions:

```go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "vpc_cidr":    "10.99.0.0/16",
            "environment": "test",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    assert.Regexp(t, `^vpc-`, vpcId)

    subnetIds := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
    assert.Equal(t, 2, len(subnetIds))
}
```

### When to Use Terratest vs terraform test

| Scenario | Tool |
|----------|------|
| Simple attribute checks | `terraform test` |
| Plan-only unit tests | `terraform test` |
| HTTP endpoint health check | `terraform test` (check block) or Terratest |
| Complex multi-step validation | Terratest |
| Custom API calls after deploy | Terratest |
| Go-based infrastructure codebase | Terratest |
| Team does not know Go | `terraform test` |

## tflint

Static analysis for Terraform configuration:

```bash
# Install
brew install tflint

# Initialize plugins
tflint --init

# Run
tflint
tflint --recursive   # Scan all subdirectories
```

### Configuration

```hcl
# .tflint.hcl

plugin "aws" {
  enabled = true
  version = "0.31.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}
```

### What tflint Catches

| Category | Examples |
|----------|---------|
| Invalid instance types | `t2.superxlarge` does not exist |
| Deprecated resources | Using removed provider features |
| Naming violations | Resources not following convention |
| Missing descriptions | Variables/outputs without docs |
| Unused declarations | Variables declared but never used |

## Contract Tests (Variable Validation)

Build contract tests directly into module variables:

```hcl
variable "listener_rule_priority" {
  type        = number
  default     = 1
  description = "Priority of listener rule (1-50000)"

  validation {
    condition     = var.listener_rule_priority > 0 && var.listener_rule_priority < 50000
    error_message = "Priority must be between 1 and 50000."
  }
}
```

### Preconditions and Postconditions

```hcl
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = data.aws_ami.selected.architecture == "x86_64"
      error_message = "AMI must be x86_64 architecture."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP assigned."
    }
  }
}
```

## Policy as Code

### Sentinel (HCP Terraform)

```python
# prevent-public-s3.sentinel
import "tfplan/v2" as tfplan

main = rule {
  all tfplan.resource_changes as _, rc {
    rc.type is not "aws_s3_bucket_public_access_block" or
    rc.change.after.block_public_acls is true
  }
}
```

### OPA / Conftest

```rego
# policy/deny_public_s3.rego
package main

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  not resource.change.after.tags["Environment"]
  msg := sprintf("S3 bucket '%s' missing Environment tag", [resource.address])
}
```

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
conftest test plan.json
```

## Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.92.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_docs
        args: ["--args=--config=.terraform-docs.yml"]
      - id: terraform_checkov
        args: ["--args=--quiet --compact"]
```

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Checkov (Security Scanning)

```bash
checkov -d .
checkov --framework terraform --directory ./modules/
checkov --skip-check CKV_AWS_18,CKV_AWS_19   # Skip specific checks
```

Checkov catches security misconfigurations: unencrypted resources, public access, missing logging, overly permissive IAM.

## Test Organization Strategy

| Module Tests | Environment Tests |
|-------------|-------------------|
| Unit + Contract + Integration | Unit + Integration + E2E |
| Run on module PR | Run on infra PR |
| Create/destroy ephemeral resources | Test against long-lived dev env |
| Gate module version release | Gate production apply |
| Fast feedback loop (< 15 min) | Slower (may take 30+ min) |
