# Planning and Imports

Sources: HashiCorp Terraform plan/apply, import overview, import block, single and bulk import, configuration generation, and CLI import documentation

Covers: plan review, saved plans, declarative imports, CLI import, generated configuration, bulk workflows, identity, and no-change convergence.

## Plan Semantics

Plan compares configuration, prior state, and refreshed remote objects using the
selected providers and variables. Review the exact root, workspace/backend,
credentials, lockfile, and variable inputs.

| Operation | Question |
|---|---|
| Create | Is this intentionally new rather than missing import? |
| Update | Is provider-side impact acceptable? |
| Replace | Which immutable/address/lifecycle change caused it? |
| Destroy | Is deletion intended, backed up, and approved? |
| Import | Does this ID map to exactly this address? |
| Move | Does old identity map to new identity? |

For production, save the reviewed plan and apply that file. Do not regenerate an
unreviewed plan inside the apply step.

## Declarative Import

Use import blocks so adoption participates in normal plan/apply review:

```hcl
import {
  to = google_storage_bucket.assets
  id = "project-id/assets-bucket"
}
```

Also declare the destination resource. The provider documentation defines the
accepted ID/identity format.

Each remote object must bind to one resource address. Never import the same
object into two addresses or states.

## Generated Configuration

When the destination block is unknown, declare import and run:

```bash
terraform plan -generate-config-out=generated_resources.tf
```

Generated configuration is a draft based on provider-read data. Review computed
fields, defaults, sensitive values, immutable properties, naming, dependencies,
and module boundaries before treating it as maintained code.

## CLI Import

`terraform import ADDRESS ID` writes the state binding but does not generate
configuration. Use it for a small legacy case when the resource block already
exists and declarative import is impractical.

CLI import can require local equivalents of remote workspace variables because
the command runs locally in some HCP Terraform workflows.

## Bulk Import

Modern Terraform supports provider-backed search/query and bulk import where
the provider implements it. Verify current Terraform/provider support and review
all discovered identities; broad discovery can include objects owned elsewhere.

For providers without suitable bulk query support, generate a reviewed import
manifest from inventory and create import blocks in small waves.

## Convergence

Import is complete only when:

1. State shows the intended provider ID at the intended address.
2. Configuration represents live immutable and behaviorally important values.
3. A full plan proposes no unexplained create/update/replace/destroy.
4. The prior writer is disabled.
5. Runtime health and access checks pass.

Do not hide mismatches with broad `ignore_changes` or apply replacement during
an ownership-only migration.

## Import Troubleshooting

| Symptom | Likely cause |
|---|---|
| ID not found | Wrong ID format, project, provider alias, or permissions |
| Address missing | Destination resource/module instance not declared |
| Create still planned | Import targeted wrong state/address or did not execute |
| Replacement planned | Immutable field/default/type mismatch |
| Duplicate-object error | Same object already bound or import omitted |
| IAM change after import | Authoritative resource form does not match ownership |

## Import Block Lifecycle

Import blocks are idempotent after the object is bound and can remain as history.
Follow repository policy consistently; never remove them before the successful
import is committed and the stable plan is recorded.

## Review Checklist

- Plan target, inputs, providers, and state are explicit.
- Production applies the reviewed saved plan.
- Import ID comes from provider docs.
- Destination address is final and unique.
- Generated config is reviewed, not blindly committed.
- Imports run in bounded waves.
- Steady-state plan is non-destructive.
- Previous writers are retired without destroy.

## Source Links

- https://developer.hashicorp.com/terraform/cli/commands/plan
- https://developer.hashicorp.com/terraform/language/import
- https://developer.hashicorp.com/terraform/language/import/single-resource
- https://developer.hashicorp.com/terraform/language/import/generating-configuration
- https://developer.hashicorp.com/terraform/cli/import
