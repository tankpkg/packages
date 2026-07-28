---
name: @tank/gcp-to-pulumi
description: |
  Convert or adopt existing Google Cloud infrastructure into Pulumi management
  without recreating live resources. Inventories GCP assets and IAM, chooses
  Pulumi GCP resource types and canonical import IDs, distinguishes direct
  import from Terraform code/state conversion, stages dependency-aware imports,
  and proves a zero-replacement steady state. Depends on @tank/pulumi and
  synthesizes current Pulumi and Google Cloud documentation.

  Trigger phrases: "migrate GCP to Pulumi", "convert GCP to Pulumi",
  "import Google Cloud resources", "adopt GCP infrastructure", "Pulumi import GCP",
  "existing GCP Pulumi", "GCP infrastructure as code migration",
  "convert Terraform GCP to Pulumi", "import tfstate to Pulumi",
  "Cloud Asset Inventory Pulumi", "bulk import GCP", "GCP import IDs",
  "move Google Cloud to Pulumi", "brownfield GCP Pulumi", "no downtime Pulumi migration"
---

# GCP to Pulumi

Load `@tank/pulumi` for Pulumi programming, stack, state, provider, testing,
and delivery fundamentals. This skill adds the brownfield GCP adoption workflow.

## Core Philosophy

1. **Migration changes ownership before architecture** -- first represent the
   live estate exactly; refactor only after a no-change baseline exists.
2. **One resource has one writer** -- identify the current owner and freeze its
   mutations before Pulumi assumes management.
3. **Inventory beats inference** -- combine Cloud Asset Inventory, service APIs,
   existing IaC state, IAM policy, and runtime dependencies; no single source is
   complete enough for a safe migration.
4. **Provider identity is a migration decision** -- choose `gcp` or
   `google-native` per supported resource and keep one provider family as the
   long-term owner of each object.
5. **Zero destructive operations is the adoption gate** -- imported resources
   are not complete until refresh and full preview show no unexplained create,
   replacement, update, or delete.

## Migration Workflow

1. Define scope, owner, outage tolerance, rollback, and the Pulumi project/stack.
2. Inventory resources, IAM, APIs, dependencies, locations, and current IaC.
3. Classify each object as import, Terraform state adoption, code conversion,
   data-source read, intentional exclusion, or later replacement.
4. Select the Pulumi provider resource type and Registry-documented import ID.
5. Generate code and an import manifest in dependency-aware waves.
6. Freeze the prior writer, back up its state, and import into the final Pulumi
   identity with deletion protection.
7. Reconcile code with provider-read state without changing live behavior.
8. Run drift detection and a full detailed preview; accept only the reviewed
   zero-change baseline.
9. Transfer CI/CD ownership, monitor, then retire the old writer without running
   its destroy path.
10. Refactor in later changes using aliases and ordinary Pulumi review gates.

## Quick-Start: Common Problems

### "What exists in this GCP estate?"

Search Cloud Asset Inventory at the organization, folder, or project scope;
supplement it with IAM search, service-specific listings, billing/export data,
and current IaC state. Build a resource ledger before writing Pulumi code.

-> See `references/discovery-and-classification.md`.

### "Should I use import or convert?"

Import manually or externally created resources. For Terraform-owned resources,
prefer Terraform-aware state adoption and convert HCL separately when it helps;
conversion alone does not transfer ownership of live resources.

-> See `references/migration-paths.md`.

### "How do I find the right GCP type and import ID?"

Start from the Pulumi Registry page for the exact resource. Confirm package,
type token, immutable fields, and documented import syntax against the live API.

-> See `references/gcp-provider-and-import-ids.md`.

### "How do I avoid replacement or downtime?"

Import into final names and parents, preserve explicit physical names, protect
critical resources, align provider defaults, and stop when preview proposes any
unexplained operation.

-> See `references/adoption-and-cutover.md`.

### "The current estate is Terraform-managed"

Back up code and state, classify provider/resource coverage, use Pulumi's
Terraform converter and state import intentionally, then remove old ownership
without `terraform destroy`.

-> See `references/terraform-to-pulumi.md`.

## Decision Trees

### Choose the Migration Path

| Current owner | Path |
|---|---|
| Console, `gcloud`, scripts, Deployment Manager, unknown | Direct or program-first Pulumi import |
| Terraform with reliable state | Terraform state adoption plus code conversion |
| Terraform code but missing/unreliable state | Inventory live GCP and import directly; use conversion only as a draft |
| Shared platform object not owned by this stack | Read with a provider function or stack contract |
| Unsupported resource | Keep current owner or use a reviewed bridge; do not fake ownership |

### Choose Import Scale

| Scope | Default |
|---|---|
| One or two independent resources | `pulumi import` with generated code review |
| Existing target program | Resource `import` option for controlled adoption |
| Complex graph or component | Program-first `preview --import-file` workflow |
| Existing Terraform state | `pulumi import --from terraform` where supported |

## Stop Conditions

Stop before mutation if the current writer is unknown, the import ID is guessed,
the provider package is undecided, state backups are missing, critical IAM is
not inventoried, or preview shows an unexplained create/replacement/delete.
Never test a migration by applying a destructive preview to production.

## Reference Index

| File | Contents |
|---|---|
| `references/discovery-and-classification.md` | Cloud Asset Inventory, IAM, dependency mapping, ownership ledger, and scope |
| `references/migration-paths.md` | Direct import, program-first bulk import, Terraform adoption, reads, and exclusions |
| `references/gcp-provider-and-import-ids.md` | Provider-family choice, type mapping, canonical IDs, defaults, and IAM resources |
| `references/adoption-and-cutover.md` | Import waves, no-change convergence, protection, cutover, rollback, and handoff |
| `references/terraform-to-pulumi.md` | Terraform code conversion, tfstate adoption, dual-control prevention, and retirement |
