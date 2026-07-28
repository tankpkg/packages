# Google Providers, Import IDs, and IAM

Sources: HashiCorp Google and Google Beta provider Registry documentation, Google Cloud Terraform best practices, IAM documentation, and Google import guidance

Covers: provider choice, aliases, full IDs, immutable/defaulted fields, API enablement, IAM authority, and high-risk resources.

## Provider Choice

Use `hashicorp/google` by default for generally available resources. Use
`hashicorp/google-beta` only for a required beta field/resource and pin/review
its version. They share many resource type prefixes, so aliases and explicit
provider selection must be clear.

Do not import one object through both providers.

## Explicit Targets

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

Use aliases for multiple projects/regions. Authentication should come from
Application Default Credentials or workload identity, not committed keys.

Record provider alias, project, region/zone, credential identity, and resources
for every migration wave.

## Import IDs

The Registry Import section for the exact resource and provider version is
authoritative. Google recommends full identifiers including project ID when
supported.

Typical orientation only:

| Resource | Common full shape, verify |
|---|---|
| Bucket | `project/name` |
| VPC network | `projects/PROJECT/global/networks/NAME` |
| Regional object | `projects/PROJECT/regions/REGION/.../NAME` |
| Zonal object | `projects/PROJECT/zones/ZONE/.../NAME` |
| Service account | `projects/PROJECT/serviceAccounts/EMAIL` |
| API service | `PROJECT/SERVICE` |

Never rely on this summary instead of provider docs.

## Type Mapping

1. Start from CAI asset type/full name.
2. Find the exact Registry resource.
3. Verify it owns the same lifecycle.
4. Record import syntax and full ID.
5. Record immutable/replacement fields.
6. Map live API fields to Terraform arguments.
7. Identify computed/defaulted fields.
8. Select final provider alias and address.

## Defaults and Immutability

Generated/provider-read configuration can differ from historical defaults.
Reconcile one field at a time and reject replacement during adoption. Do not use
broad `ignore_changes` to hide security, retention, IAM, or network differences.

## API Enablement

Determine whether `google_project_service` ownership belongs in this root or a
landing-zone state. Disabling an API can disrupt dependent resources. Import and
protect in-scope service enablement; do not let retirement of the old tool
disable active APIs.

## IAM Forms

| Terraform form | Typical authority |
|---|---|
| `*_iam_policy` | Entire policy authoritative |
| `*_iam_binding` | Members for one role authoritative |
| `*_iam_member` | One additive principal-role relation |

Confirm exact resource documentation. Do not mix authoritative and additive
forms over the same scope/role without understanding provider conflict behavior.
Preserve IAM conditions and inherited policy boundaries.

## High-Risk Review

- organization/folder/project IAM
- KMS keys and key rings
- Cloud SQL and data stores
- bucket retention/locks
- shared VPC relationships
- DNS and certificates
- GKE clusters/node pools
- load balancers
- service account keys and service agents

## Source Links

- https://registry.terraform.io/providers/hashicorp/google/latest/docs
- https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs
- https://docs.cloud.google.com/docs/terraform/best-practices/working-with-resources
- https://docs.cloud.google.com/docs/terraform/resource-management/import
