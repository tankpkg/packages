---
name: "@tank/terraform-mastery"
description: |
  Production-grade Terraform and OpenTofu for any cloud. Covers HCL syntax
  and language features, provider configuration (AWS, GCP, Azure, Kubernetes),
  module design (composition, versioning, registry publishing), state management
  (remote backends, locking, migration, workspaces), variables/outputs/locals,
  data sources, lifecycle rules, resource import and moved blocks, testing
  (terraform test, Terratest, contract tests), CI/CD pipelines (GitHub Actions,
  GitLab CI, Atlantis), Terragrunt patterns, security (secrets management,
  OIDC authentication, policy as code), drift detection, and cost estimation
  with Infracost.

  Synthesizes HashiCorp Terraform documentation (v1.9+), OpenTofu documentation,
  Brikman (Terraform: Up & Running, 3rd ed.), Winkler (Terraform in Action),
  AWS/GCP/Azure Terraform provider docs, and Terragrunt documentation.

  Trigger phrases: "terraform", "terraform module", "terraform state",
  "terraform plan", "terraform apply", "terraform import", "HCL",
  "terraform workspace", "terraform backend", "remote state", "tfvars",
  "terraform test", "terratest", "terragrunt", "opentofu", "tofu",
  "terraform ci/cd", "terraform pipeline", "infracost", "terraform aws",
  "terraform azure", "terraform gcp", "terraform provider",
  "terraform best practices", "infrastructure as code", "IaC",
  "terraform drift", "terraform moved", "terraform lifecycle",
  "terraform for_each", "terraform variable validation"
---

# Terraform Mastery

## Core Philosophy

1. **State is the source of truth** -- Terraform's state file maps configuration to real infrastructure. Protect it with remote backends, encryption, and locking. Never edit state manually unless using `terraform state` commands.
2. **Modules are the unit of reuse** -- Compose infrastructure from focused, single-responsibility modules. Pin module versions. Publish to a registry for organization-wide sharing.
3. **Plan before apply, always** -- Treat `terraform plan` output as a code review artifact. Automate plan-on-PR, require human approval before apply. Never auto-apply to production.
4. **Blast radius drives structure** -- Split state files by change frequency and risk. Networking changes rarely; application resources change often. Separate them to limit damage from any single apply.
5. **Prefer `for_each` over `count`** -- `for_each` creates stable resource addresses keyed by string. `count` uses numeric indices -- removing an item from the middle forces recreation of all subsequent resources.

## Quick-Start: Common Problems

### "How do I structure a Terraform project?"

| Layer | Contents | Change Frequency |
|-------|----------|-----------------|
| `global/` | IAM, DNS, shared resources | Rarely |
| `network/` | VPC, subnets, peering | Rarely |
| `data/` | RDS, ElastiCache, S3 | Occasionally |
| `compute/` | ECS, Lambda, EC2 | Often |
| `app/` | App-specific resources | Very often |

-> See `references/project-structure.md`

### "How do I manage state safely?"

1. Configure a remote backend with encryption and locking (S3+DynamoDB, GCS, azurerm)
2. Use one state file per environment per layer (e.g., `prod/network`, `prod/compute`)
3. Never store state in version control
4. Use `terraform state mv` for refactoring, `terraform import` for adoption
-> See `references/state-management.md`

### "How do I write reusable modules?"

1. One module = one logical component (VPC module, RDS module, not "infrastructure" module)
2. Expose inputs via `variables.tf`, outputs via `outputs.tf`
3. Add variable validation rules as contract tests
4. Version with Git tags, publish to a registry
-> See `references/module-design.md`

### "How do I test Terraform code?"

1. `terraform validate` + `terraform fmt -check` for syntax
2. `terraform test` with `command = plan` for unit tests (no real resources)
3. `terraform test` with `command = apply` for integration tests
4. Terratest (Go) for complex multi-resource validation
-> See `references/testing-validation.md`

### "How do I set up CI/CD for Terraform?"

1. PR triggers: fmt check, validate, tflint, plan, cost estimate
2. Plan output posted as PR comment for review
3. Merge triggers: apply with approval gate
4. Use OIDC for cloud authentication -- no long-lived credentials
-> See `references/cicd-pipelines.md`

## Decision Trees

### Backend Selection

| Situation | Backend | Locking |
|-----------|---------|---------|
| AWS infrastructure | S3 + DynamoDB | DynamoDB table |
| GCP infrastructure | GCS | Built-in |
| Azure infrastructure | azurerm | Built-in |
| Multi-cloud or team | HCP Terraform / Terraform Cloud | Built-in |
| Local development only | local | None |

### Module Source

| Need | Source |
|------|--------|
| Organization-wide reuse | Private registry (HCP Terraform, Artifactory) |
| Team-level reuse | Git repo with version tags |
| Prototyping | Local path (`./modules/`) |
| Community standard | Terraform Registry (`registry.terraform.io`) |

### Workspace vs Directory

| Signal | Approach |
|--------|----------|
| Same config, different variable values (dev/staging/prod) | Workspaces or Terragrunt |
| Different resources per environment | Separate directories |
| Need independent state per tenant | Workspaces with dynamic backend keys |
| Complex multi-environment with DRY config | Terragrunt with `terragrunt.hcl` hierarchy |

## Reference Index

| File | Contents |
|------|----------|
| `references/hcl-language.md` | HCL syntax, expressions, functions, type system, dynamic blocks, meta-arguments |
| `references/state-management.md` | Remote backends, locking, encryption, migration, workspaces, state surgery, import, moved blocks |
| `references/module-design.md` | Module structure, composition patterns, versioning, registry publishing, variable validation |
| `references/provider-patterns.md` | Provider configuration, multi-region, multi-account, aliases, authentication patterns (OIDC, assume role) |
| `references/testing-validation.md` | terraform test framework, Terratest, tflint, contract tests, policy as code (Sentinel, OPA) |
| `references/cicd-pipelines.md` | GitHub Actions, GitLab CI, Atlantis, plan-on-PR, apply-on-merge, OIDC auth, cost estimation |
| `references/security-secrets.md` | Secrets management, sensitive variables, encryption, least-privilege IAM, drift detection, compliance scanning |
| `references/project-structure.md` | Directory layout, file naming, environment separation, Terragrunt DRY patterns, monorepo vs polyrepo |
