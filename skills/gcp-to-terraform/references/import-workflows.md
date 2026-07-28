# GCP Import Workflows

Sources: HashiCorp declarative and CLI import documentation, generated configuration and bulk import documentation, Google Cloud Terraform import guidance

Covers: import blocks, generated configuration, CLI import, modules, collection instances, bulk discovery, review, and convergence.

## Preferred Declarative Flow

Declare the final resource address and provider-defined ID:

```hcl
import {
  to = google_compute_network.main
  id = "projects/my-project/global/networks/main"
}

resource "google_compute_network" "main" {
  project                 = "my-project"
  name                    = "main"
  auto_create_subnetworks = false
}
```

Run plan, review the import and all subsequent diffs, then apply the reviewed
plan. Import blocks allow normal code review and can handle batches.

## Generate Missing Configuration

If resource arguments are unknown, write the import block and run:

```bash
terraform plan -generate-config-out=generated_resources.tf
```

Generated code is experimental even in Terraform 1.15 and is a draft. It can
emit conflicting arguments, computed-only fields, invalid nested schemas, and
`null` for sensitive values. Run normal validation, remove non-configurable
fields, reconstruct secrets from their authority, preserve immutable and
behaviorally important defaults, and fit the resource into the final module
structure before acceptance.

## CLI Import

Google documents one-at-a-time import as:

```bash
terraform import google_storage_bucket.assets my-project/assets-bucket
```

Prefer the provider's full project-qualified ID when supported. CLI import only
writes state; the destination resource configuration must already exist.

## Module Addresses

Import every concrete child address, for example:

```bash
terraform import \
  module.storage.google_storage_bucket.assets \
  my-project/assets-bucket
```

Inspect the pinned module source to determine its internal address. Avoid
importing into a module version whose future upgrade immediately moves/replaces
the resource.

Stable Terraform can target a module child from a root import block. It cannot
generally generate missing configuration directly into registry or remote
modules. Declaring import blocks inside reusable modules is a Terraform 1.16
alpha feature as of July 2026, not stable 1.15 behavior.

## Collections

For `for_each` and `count`, target the exact instance address. Use durable keys
and quote shell addresses correctly. Declarative imports are easier to review
and less error-prone for collection instances.

## Bulk Options

| Option | Use | Caveat |
|---|---|---|
| Multiple import blocks | Reviewed bounded batches | Manual ledger work |
| Terraform query/bulk import | Provider-supported large discovery | Google list support is resource-by-resource and still expanding |
| Google bulk export/generate-import | Draft code and script | Pre-GA and incomplete coverage |
| Generated internal manifest | Deterministic estate-specific waves | Must verify every ID/type |

Do not execute generated import scripts before reviewing addresses, IDs,
provider aliases, ownership, and state target.

## Steady-State Gate

After import:

1. `terraform state show` confirms ID/address.
2. Configuration matches immutable/live behavior.
3. Full plan uses the intended backend and provider aliases.
4. No unexplained create/update/replace/destroy remains.
5. Service and IAM health checks pass.
6. The prior writer is disabled.

## Troubleshooting

| Symptom | Investigate |
|---|---|
| Not found | Full ID format, project, alias, permissions |
| Create remains | Wrong state/address or import not applied |
| Replacement | Immutable/default/type mismatch |
| IAM update | Wrong policy/binding/member authority |
| Module address error | Pinned module's actual child path |
| Duplicate binding | Existing state ownership |

## Source Links

- https://developer.hashicorp.com/terraform/language/import
- https://developer.hashicorp.com/terraform/language/import/generating-configuration
- https://developer.hashicorp.com/terraform/cli/import
- https://developer.hashicorp.com/terraform/language/import/bulk
- https://github.com/hashicorp/terraform/issues/37361
- https://github.com/hashicorp/terraform/issues/35596
- https://docs.cloud.google.com/docs/terraform/resource-management/import
