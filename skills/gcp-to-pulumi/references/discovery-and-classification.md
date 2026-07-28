# GCP Discovery and Classification

Sources: Google Cloud Asset Inventory documentation, Google Cloud IAM documentation, Pulumi migration and import documentation, Google Cloud service inventory guidance

Covers: scope, asset and IAM discovery, service-specific enrichment, ownership evidence, dependency mapping, and migration classification.

## Define the Boundary

Record the organization, folders, projects, regions, zones, billing boundary,
environments, and excluded systems. Inventory at the highest authorized scope;
project-only discovery misses shared DNS, IAM, networking, organization policy,
and cross-project service dependencies.

Migration brief:

| Field | Required answer |
|---|---|
| Business owner | Who accepts operational risk? |
| Current writer | Console, script, Terraform, another Pulumi stack, service controller |
| Target owner | Pulumi organization/project/stack |
| Change freeze | When does the old writer stop? |
| Outage tolerance | None, degraded, scheduled window |
| Rollback | How is state ownership restored without deleting resources? |
| Success | No-change preview plus service health and ownership transfer |

## Build a Multi-Source Inventory

Cloud Asset Inventory is the broad baseline, not the complete answer.

```bash
gcloud asset search-all-resources \
  --scope="organizations/ORG_ID" \
  --format=json

gcloud asset search-all-iam-policies \
  --scope="organizations/ORG_ID" \
  --format=json
```

Use least-privilege read access and store exports as sensitive operational data.
IAM bindings, labels, network paths, service account identities, and resource
names can reveal security architecture.

Supplement with:

| Source | Finds |
|---|---|
| Asset Inventory resource search | Broad metadata and ancestry |
| Asset Inventory IAM search | Policy references and principals |
| Existing Terraform/Pulumi state | Current IaC ownership and provider IDs |
| Service-specific APIs | Fields or child resources omitted from broad inventory |
| Cloud Logging audit logs | Recent writers and mutation paths |
| CI/CD definitions | Automated owners and credentials |
| Billing/export data | Active resources missed by initial filters |
| DNS, certificates, secrets | External dependencies and hidden coupling |

## Resource Ledger

Create one row per independently managed Pulumi resource, not one row per
application. Include child IAM resources and API enablement where they have a
separate lifecycle.

| Column | Purpose |
|---|---|
| Asset full name | Stable GCP identity |
| Asset type | Google API type |
| Project/location | Provider target |
| Current owner | Tool/state/pipeline |
| Pulumi package/type | Intended resource mapping |
| Import ID | Registry-documented canonical form |
| Dependencies | Parent, API, network, service account, KMS |
| Immutable fields | Replacement risk |
| Sensitive/stateful | Protection and backup requirements |
| Migration path | Import, Terraform adoption, read, exclude, replace later |
| Wave | Ordered adoption batch |
| Evidence | Source and timestamp |

An unknown value is a discovery task, not permission to guess.

## Map Dependencies

Build edges from both configuration and runtime behavior.

Common GCP ordering:

1. Project/folder context and required APIs.
2. Shared VPC, networks, subnetworks, routes, NAT, DNS.
3. KMS keys, service accounts, workload identity, base IAM.
4. Data services, buckets, databases, artifact registries.
5. Compute, GKE, Cloud Run, functions, schedulers.
6. Load balancing, certificates, DNS records, monitoring.
7. Fine-grained IAM bindings and policy attachments.

This is a planning order, not a universal create order. Existing resources
already run; import waves should minimize provider-read and ownership ambiguity.

## Identify Controllers

Some GCP objects are generated or reconciled by another service. Do not import
controller-owned children independently unless Pulumi is intended to become
their controller.

Examples:

- GKE-created forwarding rules and service accounts
- Serverless-managed revisions
- Google-managed service agents
- Certificate-manager generated records
- Organization policy inherited from ancestors

Classify these as observed/read-only, controller-owned, or explicitly migrated.

## Classify Ownership

| Evidence | Classification |
|---|---|
| Present in active Terraform state | Terraform-owned |
| Present in another Pulumi stack | Pulumi-owned elsewhere |
| Audit logs show deployment service account | Pipeline-owned; locate source |
| Console-created with no automation | Manual brownfield import |
| Google-managed service agent/resource | Provider/controller-owned |
| No evidence | Unknown; investigate before import |

One cloud object must not be managed by two IaC states. Multiple systems may
read it, but only one may declare mutation ownership.

## IAM Inventory

IAM is often represented at project, folder, organization, and resource levels.
Determine whether desired Pulumi resources are authoritative policies, bindings,
or individual members. Mixing authoritative and additive IAM resource forms can
remove unrelated principals.

Record:

- policy scope
- role
- member/principal
- condition and expression
- inherited vs direct binding
- Google-managed principals
- current authoritative owner

Treat service account keys as secrets and rotate long-lived keys during or
after migration rather than importing plaintext key material.

## Classification Gate

Every ledger row must end in exactly one class:

| Class | Meaning |
|---|---|
| Import | Pulumi assumes lifecycle ownership now |
| Terraform adoption | Transfer from trusted tfstate and converted program |
| Read | Pulumi consumes but does not own |
| Exclude | Out of migration scope with named owner |
| Controller-owned | Managed by a platform service |
| Replace later | Imported first, redesigned in a separate approved phase |
| Blocked | Missing coverage, ID, permissions, or ownership evidence |

## Source Links

- https://docs.cloud.google.com/asset-inventory/docs
- https://docs.cloud.google.com/asset-inventory/docs/search-resources
- https://docs.cloud.google.com/sdk/gcloud/reference/asset/search-all-resources
- https://docs.cloud.google.com/sdk/gcloud/reference/asset/search-all-iam-policies
- https://www.pulumi.com/docs/iac/guides/migration/import/
