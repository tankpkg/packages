# Google Bulk Export and Modernization

Sources: Google Cloud export/import Terraform documentation, Config Connector CLI references, Cloud Asset Inventory, HashiCorp generated configuration and module guidance

Covers: Google bulk export prerequisites, artifacts, limitations, safe review, comparison with native imports, and post-adoption modernization.

## Status and Purpose

Google's `gcloud beta resource-config bulk-export` path generates Terraform HCL
from project, folder, or organization resources. Google marks it pre-GA and not
supported on Windows. Coverage is narrower than the full Google provider.

Use it as discovery and draft generation, not unquestioned source of truth.

## Capability Check

```bash
gcloud beta resource-config list-resource-types
```

Compare supported export types with the migration ledger. Unsupported rows still
need declarative imports or explicit exclusion.

## Export Shape

```bash
gcloud beta resource-config bulk-export \
  --path=OUTPUT_DIRECTORY \
  --project=PROJECT_ID \
  --resource-format=terraform
```

The workflow uses Config Connector and Cloud Asset API prerequisites. Review the
current Google documentation for service-agent permissions before running at
folder/organization scope; avoid granting broad roles permanently.

## Generated Imports

Google documents:

```bash
gcloud beta resource-config terraform generate-import OUTPUT_DIRECTORY
```

This generates module files and an executable import script. Do not execute the
script before reviewing every address, provider ID, target backend/workspace,
module source, and ownership classification.

## Review Matrix

| Artifact | Review |
|---|---|
| Generated `.tf` | Defaults, computed fields, secrets, names, references |
| Module tree | Address stability and maintainability |
| Provider block | Correct project/region and credential source |
| Import script | Full IDs, shell quoting, exact target state |
| Coverage list | Missing/unsupported resources |
| IAM output | Authority and inherited bindings |

Generated modules are often organized by API resource type, not team ownership
or lifecycle. Preserve addresses through adoption, then redesign with moved
blocks after a stable baseline.

## Compare Paths

| Need | Better default |
|---|---|
| One/small batch | Terraform import blocks |
| Unknown resource arguments | `-generate-config-out` |
| Large GCP discovery draft | Google bulk export |
| Stable maintained architecture | Hand-reviewed modules after adoption |

## Safe Execution

1. Run export with read-oriented, time-bounded permissions.
2. Store output as sensitive migration material.
3. Diff against CAI ledger and service inventories.
4. Review generated HCL and scripts.
5. Replace broad generated provider configuration with explicit aliases.
6. Import bounded waves into a locked remote state.
7. Require no-change plan and health checks.
8. Remove temporary export privileges.

## Modernization Backlog

Defer these until ownership is stable:

- module boundaries by team/lifecycle
- root/state decomposition
- `for_each` stable-key conversion
- raw-ID replacement with references
- policy and labels normalization
- provider version/alias cleanup
- resource replacement or architecture redesign

Every address change needs a `moved` block or reviewed state migration.

## Source Links

- https://docs.cloud.google.com/docs/terraform/resource-management/export
- https://docs.cloud.google.com/docs/terraform/resource-management/import
- https://docs.cloud.google.com/sdk/gcloud/reference/beta/resource-config/bulk-export
- https://docs.cloud.google.com/sdk/gcloud/reference/beta/resource-config/terraform/generate-import
- https://developer.hashicorp.com/terraform/language/import/generating-configuration
