---
name: @tank/terraform
description: |
  Build, review, operate, import, and refactor production Terraform. Covers HCL
  data flow and stable addresses, providers and reusable modules, remote state
  and locking, declarative import and generated configuration, moved and removed
  blocks, testing, sensitive data, policy, and reviewed CI/CD. Synthesizes the
   current HashiCorp documentation, Terraform core and provider release notes,
   maintainer issue investigations, provider internals, and brownfield reports.

  Trigger phrases: "terraform", "terraform plan", "terraform apply",
  "terraform import", "Terraform import block", "generate-config-out", "HCL",
  "Terraform state", "tfstate", "Terraform module", "Terraform provider",
  "moved block", "removed block", "terraform test", "Terraform CI/CD",
  "Terraform drift", "infrastructure as code", "Terraform refactor"
---

# Terraform

## Core Philosophy

1. **Plan is the review contract** -- inspect the complete saved plan before
   apply; formatting and validation cannot reveal cloud lifecycle changes.
2. **Addresses are durable identities** -- stable `for_each` keys and explicit
   `moved` blocks preserve state bindings through refactors.
3. **State is sensitive coordination data** -- store it remotely with locking,
   encryption, access control, and recovery; never edit JSON directly.
4. **Modules expose capabilities, not resource dumps** -- compose small modules
   through typed variables and minimal outputs while callers own provider setup.
5. **One remote object has one address** -- import or move ownership explicitly;
   duplicate bindings and competing states cause destructive plans.

## Default Workflow

1. Inspect the root module, selected workspace/state, backend, provider lockfile,
   variable sources, and cloud identity.
2. Run `terraform fmt -check`, `terraform init`, and `terraform validate`.
3. Run targeted tests, then create a full saved plan for the intended state.
4. Review creates, updates, replacements, destroys, provider changes, and
   sensitive/stateful resources.
5. Apply the reviewed saved plan through a serialized, trusted pipeline.
6. Verify outputs and service health; retain plan/run evidence without secrets.

## Quick-Start: Common Problems

### "How should I write this configuration?"

Use typed variables with validation, locals for readable derivation, explicit
resource references for dependencies, stable map keys, and minimal outputs.

-> See `references/configuration-and-addresses.md`.

### "How do I choose providers and modules?"

Declare provider sources and constraints in every module, commit the root lock
file, configure providers in roots, and pass aliases into child modules.

-> See `references/providers-and-modules.md`.

### "How do I manage or repair state?"

Use a locking remote backend and supported state, `moved`, and `removed` flows.
Pull a backup before state mutation and define the expected next plan.

-> See `references/state-and-refactoring.md`.

### "How do I adopt existing infrastructure?"

Prefer declarative `import` blocks so adoption appears in plan. Generate draft
configuration when useful, reconcile it, and require a no-change steady state.

-> See `references/planning-and-imports.md`.

### "How do I ship this safely?"

Layer formatting, validation, tests, policy, a reviewed saved plan, short-lived
credentials, serialized apply, and post-deployment verification.

-> See `references/testing-security-delivery.md`.

### "What changed in modern Terraform, and where are the traps?"

Use a capability ledger rather than assuming every provider supports resource
identity, list/query, generated configuration, ephemeral resources, or
write-only arguments. Check open core/provider limitations before adopting new
bulk import, lifecycle, state, and secret-handling workflows.

-> See `references/field-guide-2026.md`.

## Decision Trees

### Choose State Boundaries

| Signal | Direction |
|---|---|
| Same owner, lifecycle, privilege, and failure domain | One root/state |
| Different owners or deployment cadence | Separate roots/states |
| Same configuration, environment-specific values | Separate state/workspace only with explicit targeting |
| Circular remote-state dependency | Redesign boundaries |

### Choose an Import Workflow

| Scope | Default |
|---|---|
| One legacy resource | Declarative `import` block; CLI import only if required |
| Small reviewed batch | Multiple import blocks |
| Configuration unknown | Import blocks plus `plan -generate-config-out=...` |
| Large provider-supported estate | Query/bulk import where stable, otherwise generated manifest reviewed in waves |

### Choose a Collection Meta-Argument

| Identity | Choice |
|---|---|
| Durable business keys | `for_each` |
| Fixed homogeneous count where index identity is acceptable | `count` |
| Independent named resources | Separate resource blocks |

## Safety Gates

Stop before apply when state identity is uncertain, the workspace/backend is
wrong, a provider upgrade is mixed into unrelated work, a replacement or destroy
is unexplained, a saved plan is stale, or credentials target the wrong account.
Do not use `-target`, `state rm`, refresh-only acceptance, or `-auto-approve` to
bypass uncertainty.

## Reference Index

| File | Contents |
|---|---|
| `references/configuration-and-addresses.md` | HCL values, dependencies, variables, locals, outputs, collections, and stable addresses |
| `references/providers-and-modules.md` | Provider requirements, lockfiles, aliases, module contracts, and composition |
| `references/state-and-refactoring.md` | Backends, locking, drift, state commands, moved/removed blocks, and recovery |
| `references/planning-and-imports.md` | Plan/apply semantics, declarative and CLI import, generated configuration, and convergence |
| `references/testing-security-delivery.md` | Validation, tests, policies, secrets, CI authentication, saved plans, and production gates |
| `references/field-guide-2026.md` | Terraform 1.10-1.15 capabilities, provider internals, import/query failures, state and lifecycle traps |
