# GCP to Terraform Field Guide 2026

Sources: Terraform v1.10-v1.15 releases, Terraform Google provider v7.33-v7.41 releases/issues, Magic Modules internals, Google Cloud Asset Inventory, IAM propagation, GCS backend, Bucket Lock, Cloud KMS, Cloud SQL, Shared VPC, and 2025 brownfield operations reporting

Covers: version/provider capability, bulk query coverage, generated HCL, provider generation, inventory gaps, IAM/service agents, deletion semantics, irreversible resources, backend recovery, and adoption evidence.

## Pin the 2026 Baseline

As of July 2026, Terraform 1.15.8 and Google provider 7.41.0 are current stable
releases. Pin exact migration tool/provider versions and commit the lockfile.

Do not mix these changes:

- Terraform minor upgrade
- Google provider major/minor upgrade
- import wave
- module refactor
- live resource configuration change

Each can independently alter plans and state. Keep ownership transfer boring.

## Know How the Google Provider Is Built

Magic Modules generates much of both `hashicorp/google` and
`hashicorp/google-beta` from one source model; handwritten/custom code handles
exceptions. This explains recurring patterns:

- GA and beta often share implementation but release on different surfaces.
- A generator change can affect many resources at once.
- Defaults, force-new flags, import formats, flattening, retries, and deletion
  policy can change without a Google API change.
- Provider issue fixes may originate in Magic Modules and arrive downstream in
  a later provider release.

Magic Modules explicitly classifies ID/import format changes, default changes,
force-new defaults, deletion behavior, and state representation as breaking.
Before upgrading, inspect both provider and Magic Modules release/PR context.

## Bulk Query Is Real but Partial

Terraform 1.14 introduced provider-backed list resources and `terraform query`.
The Google provider began adding list-resource coverage incrementally; releases
7.38-7.40 added specific types such as Compute addresses, DNS records/zones,
Pub/Sub topics, Secret Manager secrets, IAM members, and project services.

Therefore:

- There is no single "list every GCP resource" query.
- Support is exact-resource-type and provider-version dependent.
- A missing list resource is a coverage gap, not proof that no object exists.
- Default query limit is 100 unless raised.
- `include_resource = true` can increase read time and API cost.
- Query results still require ownership filtering against other states/tools.

Build a capability table before promising bulk adoption:

| GCP asset type | Terraform resource | List resource in pinned provider | Identity schema | Import tested |
|---|---|---|---|---|
| `compute.googleapis.com/Network` | `google_compute_network` | yes/no | fields | evidence |

## Generated HCL Is Not Apply-Ready

Both single-import `plan -generate-config-out` and bulk-query generation are
provider-assisted and experimental. Current/open issue history shows:

- sensitive fields generated as `null`
- computed-only fields emitted as configurable
- mutually exclusive arguments emitted together
- provider-normalized empty values failing validation
- missing/invalid nested configuration
- inability to generate directly into registry/remote modules

Generation can still write a file when plan reports conflicts. Do not interpret
file existence as success.

Reduction procedure:

1. Preserve raw generated HCL as evidence outside maintained code.
2. Run `terraform fmt` and `terraform validate`.
3. Remove computed-only fields and meaningless null/empty defaults.
4. Resolve conflicts using the exact provider schema.
5. Restore sensitive values through secret references, not copied state.
6. Make immutable/security/retention/topology settings explicit.
7. Replace literal dependency IDs with resource/data references where correct.
8. Run a fresh full plan and review all non-import operations.

## Module Imports Have Important Boundaries

In stable v1.15:

- A root import block can target a concrete resource already declared inside a
  module.
- CLI import can target a concrete module address.
- Generated config cannot generally be written into a registry/remote module.
- Generate at root, clean it, then move it into a local module when appropriate.
- Import blocks declared inside reusable modules are v1.16 alpha behavior, not a
  stable migration dependency.

Read and pin third-party module source before importing. Internal resource
addresses are part of the adoption contract even if the module did not promise
them as a public API.

## Cloud Asset Inventory Is Eventually Consistent

CAI current data is eventually consistent and historical data is best-effort;
Google states rare updates can be missed. Most updates appear within minutes,
but different content types have different ingestion schedules and ancestor
data can disagree. History retention is 35 days.

Safe discovery requires:

- at least two CAI snapshots with `update_time`
- supported asset-type coverage check
- separate `RESOURCE`, `IAM_POLICY`, and org-policy retrieval
- service API listings for unsupported/incomplete types
- Cloud Audit Logs to identify current writers/controllers
- billing, DNS, CI, existing state, and Config Connector cross-checks

CAI relationship data can require Security Command Center Premium/Enterprise.
Do not make migration completeness depend on a relationship feed the customer
does not have.

## IAM Adoption Is Both Authoritative and Eventual

Choose the narrowest Terraform IAM resource matching intended authority:

| Resource form | Ownership |
|---|---|
| `*_iam_policy` | Entire policy |
| `*_iam_binding` | All members for one role |
| `*_iam_member` | One additive member/role |

Policy, binding, and member resources at the same scope can fight. Do not split
one role across multiple authoritative bindings. Preserve conditions and verify
whether inherited policy is being confused with attached policy.

Google documents IAM policy changes as typically propagating in two minutes and
potentially seven minutes or longer. Group changes can take hours; nested group
changes longer. Terraform dependency edges order API calls but do not wait for
authorization to become effective everywhere.

Use a readiness probe for the exact permission the consumer needs. Restrict
retries to documented propagation failures and retain a timeout with evidence.

## API Enablement and Service Identity Races

`google_project_service` returning success does not guarantee every dependent
service agent or permission is immediately usable. Enabling APIs can create
Google-managed service identities and IAM grants asynchronously.

For an adoption wave:

1. Import/record existing service enablement before dependent resources.
2. Set disable/deletion behavior explicitly after reading the pinned provider.
3. Wait for required service identities via service-specific data/read calls.
4. Re-snapshot IAM before importing authoritative bindings.
5. Never retire old state by destroying project-service resources.

Provider 7.33 introduced a broad generated `deletion_policy` rollout. Open issue
#27469 documents a spurious `deletion_policy = "DELETE"` state diff on
`google_project_service` conflicting conceptually with
`disable_on_destroy = false`. Review this interaction on the exact provider
version rather than accepting the default field mechanically.

## Deletion Protection Can Fail Late

Open provider issue #22997 documents resources where Terraform plans deletion
despite `deletion_protection = true`; the provider prevents it only during
apply. A green plan review is therefore not proof that a protected deletion
will fail early or clearly.

Use layered controls:

| Layer | Example |
|---|---|
| Terraform | `prevent_destroy` while resource remains configured |
| Provider field | `deletion_protection`, `deletion_policy`, `disable_on_destroy` |
| GCP API | Cloud SQL deletion protection, retention lock |
| Organization | constraints, liens, deny policies |
| Data recovery | backups, PITR, object versioning, replicas |

Remember: removing a resource block also removes its `prevent_destroy` lifecycle
block. Remote GCP protection remains necessary for out-of-band deletion.

## Irreversible and Non-Deletable Resources

| Resource/control | Migration consequence |
|---|---|
| Bucket retention lock | Cannot unlock or reduce retention; may block project deletion via lien |
| KMS key ring | Cannot be deleted; name/location are permanent inventory |
| KMS key version | Destruction becomes permanent after schedule; encrypted data can be lost |
| Project lien | Separate permissions and origin; may be service-created |
| Shared VPC attachment | One host per service project; cross-project privileges |
| Cloud SQL | Project deletion bypasses instance deletion protection |

Import these using live immutable values. Never test destroy in production to
discover provider behavior. Rehearse state removal/abandonment against replicas
or representative test resources.

## GCS Backend Has Its Own Migration Hazards

The Terraform GCS backend supports locking and recommends object versioning.
For production migration state:

- Create the bucket before configuring the backend.
- Separate state-admin identity from infrastructure provider identity.
- Expect temporary 403s after bucket IAM changes.
- Do not pass credentials through `-backend-config`; they can enter
  `.terraform` and plan files.
- Retain old CMEK versions until every state object has been rewritten after a
  key migration.
- Changing customer-supplied encryption keys requires manual object rewrite;
  Terraform cannot migrate them automatically.
- Test version restore and force-unlock procedures with exact object paths.

Never let the state root manage and destroy its own only backend bucket/key
without an independently controlled bootstrap layer.

## Shared VPC Crosses State and Permission Boundaries

The host project owns shared networks/subnets and network policy. Service
projects own workloads and many address objects. Service project administrators
consume host subnets through `compute.networkUser` grants.

Model separate states when ownership/privilege differs. A service project can
attach to one host only. Existing workloads do not automatically adopt Shared
VPC after attachment; many must be recreated to use shared subnets.

Before importing:

- identify attachment owner
- distinguish project-level from subnet-level network-user grants
- capture org constraints restricting host/subnets
- map service agents that need host-project roles
- verify DNS and load-balancer resources that span projects

## Permadiffs Can Be Provider Bugs

A console-created object can have an API shape that valid HCL cannot express.
Google provider issue #28070 documented a PAM entitlement whose empty API block
flattened into state, forced replacement, but could not be represented in HCL.
The fix shipped in provider 7.40.0.

When no HCL value converges:

1. Do not apply replacement during ownership transfer.
2. Capture API JSON, state, schema, and detailed plan.
3. Search provider and Magic Modules issues/releases.
4. Upgrade to a confirmed fixed version in isolation.
5. Use temporary `ignore_changes` only with named risk, owner, and removal issue.

Permanent ignore rules can hide future security or approval-workflow drift.

## Brownfield Ordering by Learning and Blast Radius

A regulated brownfield report recommends first building operator knowledge with
refactor, migration, disaster, and unsupported-service exercises. Apply that to
GCP adoption:

1. Begin with replaceable, low-coupling resources.
2. Exercise state loss and import reconstruction in a non-production project.
3. Adopt service-level resources before shared global foundations.
4. Move IAM, DNS, Shared VPC, KMS, and organization resources last.
5. Maintain explicit layer order and reverse-order retirement.

The goal is not merely valid HCL. It is a repeatable operating procedure another
engineer can execute under incident pressure.

## Acceptance Gate

Require all of the following:

- CAI and service inventories reconcile, including timestamps and gaps.
- Every object has one current writer and one final Terraform address.
- Terraform/provider/backend versions and lockfile are recorded.
- Generated HCL has passed reduction and validation.
- Import plus subsequent full plan has no unexplained mutation.
- IAM/service-agent readiness checks pass after propagation.
- GCP and Terraform protection layers are documented separately.
- Stateful service restore/backup evidence is current.
- Old state is preserved read-only and its apply path disabled.
- A later ordinary change succeeds before final retirement.

## Source Links

- https://github.com/hashicorp/terraform/releases/tag/v1.15.8
- https://github.com/hashicorp/terraform-provider-google/releases/tag/v7.41.0
- https://github.com/hashicorp/terraform-provider-google/issues/22997
- https://github.com/hashicorp/terraform-provider-google/issues/27469
- https://github.com/hashicorp/terraform-provider-google/issues/28070
- https://googlecloudplatform.github.io/magic-modules/breaking-changes/breaking-changes/
- https://developer.hashicorp.com/terraform/language/import/bulk
- https://developer.hashicorp.com/terraform/language/backend/gcs
- https://cloud.google.com/asset-inventory/docs/overview
- https://cloud.google.com/iam/docs/access-change-propagation
- https://cloud.google.com/storage/docs/bucket-lock
- https://cloud.google.com/kms/docs/destroy-restore
- https://cloud.google.com/sql/docs/mysql/deletion-protection
- https://cloud.google.com/vpc/docs/shared-vpc
- https://www.evalapply.org/posts/systems-approach-to-infrastructure-as-code/index.html
