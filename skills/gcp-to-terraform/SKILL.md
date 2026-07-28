---
name: @tank/gcp-to-terraform
description: |
  Adopt existing Google Cloud infrastructure into Terraform management without
  recreating live resources. Covers Cloud Asset Inventory and ownership
  discovery, Google provider types and full import IDs, declarative imports and
  generated configuration, Google's pre-GA bulk export, IAM authority, remote
  state, no-change convergence, writer cutover, rollback, and later refactoring.
  Depends on @tank/terraform and synthesizes current HashiCorp and Google docs.

  Trigger phrases: "migrate GCP to Terraform", "convert GCP to Terraform",
  "import Google Cloud resources", "existing GCP Terraform", "Terraform import GCP",
  "GCP to HCL", "adopt Google Cloud infrastructure", "brownfield GCP Terraform",
  "Cloud Asset Inventory Terraform", "bulk export GCP Terraform",
  "generate-config-out GCP", "Google provider import ID", "GCP IAM Terraform import",
  "move Google Cloud to Terraform", "no downtime GCP Terraform migration"
---

# GCP to Terraform

Load `@tank/terraform` for HCL, providers, modules, state, import, testing, and
delivery fundamentals. This skill adds the brownfield Google Cloud workflow.

## Core Philosophy

1. **Transfer ownership before redesign** -- first represent live behavior and
   obtain a no-change plan; modernize only in later reviewed changes.
2. **One object has one state address and writer** -- freeze scripts, consoles,
   Config Connector, Deployment Manager, or other IaC before Terraform cutover.
3. **Inventory is multi-source** -- combine Cloud Asset Inventory, IAM search,
   service APIs, audit logs, CI definitions, and existing state.
4. **Provider documentation defines identity** -- use the exact Google provider
   resource and full import ID format; do not infer IDs from names.
5. **No destructive plan is the adoption gate** -- stop on unexplained create,
   update, replacement, or destroy for an ownership-only migration.

## Migration Workflow

1. Define scope, owners, target root/state, freeze, rollback, and success checks.
2. Inventory resources, IAM, APIs, dependencies, locations, and current writers.
3. Classify each object as import, data-source read, controller-owned, excluded,
   unsupported, or later replacement.
4. Select `hashicorp/google` or `hashicorp/google-beta`, resource type, provider
   alias, final address, and Registry-documented import ID.
5. Write reviewed resource and declarative import blocks; use generated config
   only as a draft.
6. Initialize a protected remote backend and lock reviewed provider versions.
7. Freeze the previous writer, back up state/configuration, and import in waves.
8. Reconcile generated/defaulted fields without changing live behavior.
9. Require a full no-change plan plus IAM and service health parity.
10. Transfer CI ownership and retire the prior writer without destroy.
11. Refactor later with `moved` blocks and ordinary production gates.

## Quick-Start: Common Problems

### "What should be migrated?"

Build an organization/folder/project asset and IAM ledger, then enrich it with
service-specific details, state, pipelines, and audit-log writer evidence.

-> See `references/discovery-and-classification.md`.

### "Which import workflow should I use?"

Prefer reviewed declarative import blocks. Use generated resource configuration
when code is missing, CLI import for small legacy cases, and bulk export only
after accepting its pre-GA and coverage limitations.

-> See `references/import-workflows.md`.

### "What type and ID does this GCP resource use?"

Use the exact Google provider Registry page, prefer a full project-qualified ID
when supported, and model IAM policy/binding/member authority deliberately.

-> See `references/google-provider-and-iam.md`.

### "How do I prevent downtime or replacement?"

Import into final addresses, preserve immutable/defaulted values, protect
stateful resources, and stop until the full plan is non-destructive.

-> See `references/convergence-and-cutover.md`.

### "Can Google generate all the Terraform?"

Google's Config Connector-based bulk export is useful discovery/code-generation
but is pre-GA, platform-limited, and does not support every provider resource.
Review generated modules/import scripts instead of running them blindly.

-> See `references/bulk-export-and-modernization.md`.

## Decision Trees

### Classify the Resource

| Current condition | Target |
|---|---|
| Manually/script-created and supported | Declarative import |
| Existing Terraform state | Keep or deliberately migrate that state; do not re-import elsewhere |
| Shared resource owned by platform root | Data source or remote-state contract |
| Service/controller-generated child | Observe; keep controller ownership |
| Unsupported provider resource | Exclude or use reviewed alternative; do not fake CRUD |

### Choose Scale

| Scope | Default |
|---|---|
| One resource | One import and resource block |
| Small graph | Multiple reviewed import blocks |
| Unknown configuration | Import blocks plus `-generate-config-out` |
| Large supported estate | Inventory-driven waves; optionally compare Google bulk export |

## Stop Conditions

Stop if the current writer is unknown, backend/state ownership is undecided, an
ID is guessed, provider alias targets are implicit, IAM authority is unclear,
backup/rollback is missing, or plan proposes unexplained mutation. Never validate
the migration by applying a destructive production plan.

## Reference Index

| File | Contents |
|---|---|
| `references/discovery-and-classification.md` | Asset/IAM inventory, dependencies, controllers, ownership, and migration ledger |
| `references/import-workflows.md` | Declarative, generated-config, CLI, bulk-query, and module imports |
| `references/google-provider-and-iam.md` | Google/google-beta choice, aliases, import IDs, API enablement, defaults, and IAM authority |
| `references/convergence-and-cutover.md` | Remote state, import waves, no-change plan, freeze, rollback, and handoff |
| `references/bulk-export-and-modernization.md` | Google pre-GA bulk export, generated artifacts, limitations, review, and post-adoption refactoring |
