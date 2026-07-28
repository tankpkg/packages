# GCP Providers and Import IDs

Sources: Pulumi GCP and Google Native repositories, Pulumi Terraform Bridge documentation, provider resource pages, Pulumi import documentation, Google Cloud resource-name documentation

Covers: provider-family selection, explicit providers, resource mapping, canonical import IDs, immutable/defaulted properties, API enablement, and IAM ownership forms.

## Provider Families

Use Google Cloud Classic (`gcp`) for new and continuing GCP management. The
`pulumi-google-native` repository explicitly marks Google Native unmaintained,
states that no further releases or fixes are planned, and directs users to GCP
Classic. Do not create new `google-native` ownership.

GCP Classic is generated through Pulumi's Terraform Bridge from the upstream
Terraform Google provider. Its schemas, defaults, CRUD, imports, and many bugs
originate upstream; Pulumi adds bridge mappings and engine semantics.

Choose per resource using evidence:

| Question | Evidence |
|---|---|
| Is the exact resource supported? | Current GCP Classic Registry resource page |
| Is import documented? | Resource page Import section |
| Does it model required fields/lifecycle? | Inputs, outputs, replacement notes |
| Which upstream version is embedded? | Pulumi GCP release metadata and upstream changelog |
| Is the issue engine, bridge, or provider? | Search all three repositories |

If an estate already uses Google Native, freeze new adoption and inventory each
resource for migration to GCP Classic or another maintained owner. Switching
families is not a package rename; it is a resource-type/state migration with
potentially different IDs and schemas. An alias alone does not prove safety.

## Explicit Provider Strategy

Create explicit providers for multi-project or multi-region estates. Record the
target project, region/zone, credentials source, and provider version.

Avoid relying on ambient `gcloud` defaults in CI. A correct import ID against
the wrong configured project can fail confusingly or read a different object.

Provider ledger:

| Logical provider | Project | Region/zone | Credential | Resources |
|---|---|---|---|---|
| `shared` | shared-prod | global | workload identity A | DNS, VPC |
| `app` | app-prod | europe-west1 | workload identity B | Cloud Run, SQL |

## Canonical Import IDs

Import IDs are resource-specific. Never derive them from intuition alone.
Open the exact Registry resource page and copy its documented syntax.

Typical shapes include:

| Resource family | Common shape, verify in Registry |
|---|---|
| Storage bucket | bucket name |
| Service account | `projects/{project}/serviceAccounts/{email}` |
| Compute network | project/name or full resource path |
| Regional resource | project/region/name or full path |
| Zonal resource | project/zone/name or full path |
| Project service | project/service API name |
| IAM member/binding | Composite scope/role/member identifier |

The table is orientation only. The Registry's Import section is authoritative
for the selected package version.

## Type Mapping Procedure

For every Cloud Asset Inventory row:

1. Identify the Google API asset type and full resource name.
2. Search the Pulumi Registry in the chosen provider family.
3. Confirm the resource manages the same lifecycle, not a data source or child.
4. Record the Pulumi type token exactly.
5. Record import syntax and a redacted example.
6. List immutable and replacement-triggering inputs.
7. Map live API fields to Pulumi inputs.
8. Record provider defaults and fields omitted by the inventory export.
9. Test read/import in an isolated migration stack when uncertainty remains.

## Physical Names

Existing GCP resources already have physical names. Set name fields explicitly
where the provider schema expects them so Pulumi does not generate an auto-name
or infer a different name after import.

Keep logical Pulumi names stable and readable; they do not need to equal the
physical name, but the mapping must remain documented.

## Immutable and Defaulted Fields

GCP APIs frequently make location, network attachment, database engine, or
resource name immutable. Provider defaults can also differ from historical API
defaults.

Convergence procedure:

1. Import/read the live object.
2. Inspect generated code and detailed state safely.
3. Add live immutable values explicitly.
4. Add behaviorally important defaults explicitly.
5. Preview.
6. Resolve proposed updates one field at a time.
7. Reject replacement during adoption unless separately approved.

Do not use broad `ignoreChanges` to hide a mismatch. It can conceal security,
IAM, retention, or network drift.

## API Enablement

Many resources require a Google API. Determine whether API enablement itself is
managed by Pulumi, a landing-zone stack, or an external platform.

Changing ownership of project services can be dangerous because disabling an
API may disrupt dependent resources. Import existing service enablement when it
belongs in scope, protect it during migration, and avoid disabling dependent
services during retirement of the old tool.

## IAM Resource Forms

Pulumi GCP providers may expose policy, binding, and member resources with
different authority:

| Form | Typical ownership |
|---|---|
| Policy | Authoritative for the full policy |
| Binding | Authoritative for members of one role |
| Member | Additive for one principal/role pair |

Confirm semantics on the exact Registry page. Importing a full authoritative
binding from an incomplete inventory can remove principals on the next update.
Preserve conditions and inherited policy boundaries.

## High-Risk Resource Checklist

Apply extra review to:

- Cloud SQL and data stores
- KMS keys and key rings
- DNS zones and records
- shared VPC host/service project links
- organization/folder/project IAM
- service account keys
- GKE clusters and node pools
- load balancers and certificates
- buckets with retention or lock policies

## Source Links

- https://www.pulumi.com/registry/packages/gcp/
- https://www.pulumi.com/registry/packages/google-native/
- https://github.com/pulumi/pulumi-google-native
- https://github.com/pulumi/pulumi-terraform-bridge
- https://www.pulumi.com/registry/packages/gcp/api-docs/provider/
- https://www.pulumi.com/tutorials/importing-gcp-infrastructure/
- https://www.pulumi.com/docs/iac/guides/migration/import/
