# GCP Discovery and Classification

Sources: Google Cloud Asset Inventory, IAM, audit logging, Terraform on Google Cloud import/export, and HashiCorp import/state documentation

Covers: scope, resource and IAM discovery, ownership evidence, dependency mapping, controller-owned resources, and migration classification.

## Scope Brief

Record organization, folders, projects, regions/zones, environments, billing,
owners, current writers, target Terraform root/state, outage tolerance, freeze,
rollback, exclusions, and acceptance tests.

Inventory at the highest authorized scope. Project-only discovery misses shared
VPC, organization/folder IAM, DNS, policy, and cross-project dependencies.

## Discovery Sources

```bash
gcloud asset search-all-resources \
  --scope="organizations/ORG_ID" \
  --format=json

gcloud asset search-all-iam-policies \
  --scope="organizations/ORG_ID" \
  --format=json
```

Supplement broad inventory:

| Source | Evidence |
|---|---|
| Asset resource search | Names, types, ancestry, location |
| IAM search | Principals, roles, conditions, scopes |
| Service-specific APIs | Child fields and resources absent from CAI |
| Audit logs | Recent mutation identities and tools |
| Existing Terraform/other state | Current lifecycle owner and provider IDs |
| CI/CD and scripts | Scheduled/merge-triggered writers |
| Billing/export data | Active costly assets missed by filters |

Treat exports as sensitive architecture data.

## Resource Ledger

| Field | Meaning |
|---|---|
| Asset full name/type | GCP identity |
| Project/location | Provider alias target |
| Current owner | State/tool/pipeline/person |
| Terraform type/address | Final binding |
| Import ID | Registry-documented full form |
| Dependencies | APIs, network, service account, KMS, parent |
| Immutable/defaulted fields | Replacement/update risk |
| IAM semantics | Policy, binding, member, inherited |
| Classification | Import, read, controller, exclude, blocked |
| Wave/evidence | Execution order and source timestamp |

Unknown fields remain blocked; do not guess.

## Controllers

Do not independently import children reconciled by GKE, serverless revisions,
managed load balancing, service agents, or another platform controller unless
Terraform will become that controller.

## Current Ownership

| Evidence | Classification |
|---|---|
| Object in active Terraform state | Already Terraform-owned |
| Audit log deployment service account | Locate pipeline/source before transfer |
| Config Connector owner references | Controller-owned |
| Console creation and no automation | Manual brownfield candidate |
| Google-managed service agent | Service-owned |
| No reliable evidence | Blocked |

The same object must not be imported into multiple Terraform states.

## Dependencies and Waves

Typical planning order:

1. Project/provider context and APIs.
2. Shared VPC, subnetworks, routes, NAT, DNS.
3. Service accounts, KMS, workload identity, base IAM.
4. Buckets, databases, artifact repositories, data services.
5. GKE, compute, Cloud Run, functions, schedulers.
6. Load balancing, certificates, monitoring, fine IAM.

Existing objects already run, so order imports for ownership clarity and provider
reads rather than pretending to recreate them.

## IAM Inventory

Record scope, role, principal, condition, inherited/direct status, Google-managed
principals, and current authority. Incomplete IAM discovery can make an
authoritative binding remove unrelated members after import.

Do not import service account private key material into source or state. Rotate
long-lived keys toward workload identity.

## Classification Gate

Every row ends in exactly one state:

- import into this root
- read through data source
- already managed in named state
- controller-owned
- excluded with named owner
- unsupported/blocker
- import now, replace later in separate project

## Source Links

- https://docs.cloud.google.com/asset-inventory/docs
- https://docs.cloud.google.com/asset-inventory/docs/search-resources
- https://docs.cloud.google.com/sdk/gcloud/reference/asset/search-all-resources
- https://docs.cloud.google.com/sdk/gcloud/reference/asset/search-all-iam-policies
- https://docs.cloud.google.com/docs/terraform/resource-management/import
