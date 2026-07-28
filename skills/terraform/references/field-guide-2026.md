# Terraform Field Guide 2026

Sources: Terraform v1.10-v1.15 changelogs and documentation, Terraform core and Google provider maintainer issues, provider protocol behavior, GCS backend guidance, and a 2025 regulated-brownfield field report

Covers: version capabilities, provider schemas, plan/state semantics, query and import limitations, generated configuration, sensitive data, lifecycle controls, backend recovery, and operational drills.

## Maintain a Capability Ledger

Terraform core features and provider features ship independently. Record:

| Layer | Evidence to retain |
|---|---|
| Terraform CLI | Exact version and release line |
| Provider | Source address, selected version, lockfile checksums |
| Backend | Type, state key/workspace, lock mechanism, encryption method |
| Module | Source and immutable version/ref |
| Cloud API | Region/project/account and relevant API release behavior |

Do not infer a provider capability from the Terraform version. Resource
identity, list resources, generated configuration, ephemeral resources, and
write-only arguments all require provider implementation.

### Stable Feature Timeline

| Terraform | Capability | Hidden constraint |
|---:|---|---|
| 1.10 | Ephemeral resources/values | Only valid in ephemeral contexts; provider must expose resources |
| 1.11 | Write-only managed-resource attributes | Provider schema must implement them; usually paired with version field |
| 1.12 | Import by structured resource identity | Provider must publish identity schema |
| 1.14 | `list` resources and `terraform query` | Each resource type needs provider list support |
| 1.14 | Provider-defined actions | Imperative side effects expand review surface |
| 1.15 | Query/validation and typed-output refinements | Generated import configuration remains experimental |

As of July 2026, v1.15.8 is the current stable patch line. Import blocks inside
modules appear in v1.16 alpha release notes and must not be treated as stable
v1.15 behavior. A root import block can target an existing module address, but
that is different from declaring reusable imports inside the module.

## The Provider Owns Most Surprises

Terraform core evaluates configuration and graph/state transitions. Providers
own schemas and remote behavior, including:

- required, optional, computed, sensitive, and write-only attributes
- force-new/replacement decisions
- default values and API-default preservation
- import ID parsing and structured identities
- flatten/expand normalization
- retries, polling, and timeouts
- read-after-create consistency behavior
- generated configuration and list-resource support

When a plan changes after a provider upgrade with no HCL edit, inspect the
provider changelog and schema before changing lifecycle settings.

Provider authors classify changing ID formats, import formats, defaults,
deletion behavior, force-new fields, diff suppression, and state representation
as breaking changes. Stable-major policies reduce but do not eliminate risk:
bug fixes can intentionally correct an unsafe in-place update to replacement.

## Plan Has Three Inputs, Not One

A normal plan combines configuration, prior state, and provider reads of remote
objects. Therefore a plan can change because:

1. Configuration changed.
2. State changed or was migrated.
3. The provider read a different live value.
4. Provider schema/default/normalization changed.
5. Credentials now see a different object or permission surface.

Save the plan for production apply, but remember that a saved plan contains
provider decisions and can contain sensitive values. It is not a harmless log
artifact. Protect it like state and reject it when environment, credentials,
provider binaries, or approval context no longer match.

`-detailed-exitcode` is useful automation evidence, not a semantic guarantee.
Terraform issue #38097 documents a case where output type changes returned 2
while human output said "No changes." Inspect machine-readable plan details for
policy decisions rather than parsing prose.

## Generated Configuration Is Experimental

Terraform v1.15 documentation still labels `plan -generate-config-out` as
experimental. It asks the provider to turn read state into candidate HCL, which
is not the inverse of provider apply logic.

Known failure classes include:

- mutually conflicting arguments emitted together
- computed-only fields emitted as configuration
- nested schema fields incorrectly treated as required
- sensitive fields emitted as `null`
- values that pass generation but fail normal validation/apply
- inability to generate directly into local, registry, or remote modules
- formatting or representation changes between Terraform minor versions

Terraform core issue #37361 remains open for sensitive generated attributes
becoming `null`. Issue #35596 explains that generation into registry/remote
modules cannot generally work; the practical workaround is root generation,
manual cleanup, then moving reviewed code into a local module. Issue #37712
demonstrates bulk query output that could not be applied until many computed and
conflicting fields were removed.

Treat generated HCL as a provider-state dump requiring reduction:

1. Run `terraform fmt` and `terraform validate`.
2. Remove computed-only and empty/default artifacts.
3. Resolve mutually exclusive arguments.
4. Reconstruct sensitive values from an authoritative secret source.
5. Replace copied IDs with references where ownership is known.
6. Make immutable, security, retention, and topology fields explicit.
7. Run a new full plan; never apply the generation plan blindly.

## Query and List Are Provider-Limited Discovery

`terraform query` runs provider-defined list resources from `.tfquery.hcl`.
The default list limit is 100; `include_resource = true` retrieves attributes
and may materially increase latency. The generated file includes resource and
import blocks with structured identities where supported.

This is not a universal cloud inventory:

- Only provider/resource combinations with list support are discoverable.
- Filters and result completeness are provider-specific.
- Discovery can include resources owned by other states or tools.
- HCP can identify cross-workspace ownership only where identities are known.
- Generated configuration inherits all limitations above.

Maintain an external ownership ledger and diff query results against state,
cloud inventory, and current writers. Never equate "query found none" with
"none exist."

## Import Addressing and Modules

An import binds one remote identity to one concrete address. The module source
must already define the resource when importing into a module address.

Important distinctions:

| Need | Supported stable approach |
|---|---|
| Import an existing child in a module | Root import block or CLI targeting concrete module address |
| Generate missing resource into root | `plan -generate-config-out` |
| Generate directly inside registry module | Not generally possible |
| Put import block inside reusable module | v1.16 alpha feature, not stable v1.15 |
| Import `for_each` instances | Exact stable key per object |

Do not import into a third-party module without reading its source and upgrade
history. A module can rename or restructure internal addresses in a later
release; pin it and record the address contract used for adoption.

## Sensitive Is Redaction, Not Omission

`sensitive = true` hides values in normal CLI/UI rendering but stores them in
state and plan. `terraform output -raw` and `-json` can reveal sensitive output.

Use modern primitives deliberately:

| Primitive | Persistence |
|---|---|
| Sensitive variable/output | Stored, normally redacted |
| Ephemeral variable/child output/resource | Omitted from plan and state |
| Provider write-only argument | Sent during operation, omitted afterward |

Ephemeral values can flow only through allowed ephemeral contexts. Root outputs
cannot be ephemeral. Write-only arguments normally have a separate version
argument because Terraform cannot compare a value it does not retain.

Provider support is uneven. Before claiming a secret no longer enters state,
inspect the exact provider resource schema and a redacted test state. Migrating
to write-only fields may also require explicit rotation/version semantics.

## State Safety Requires Practiced Recovery

State has lineage and serial metadata to prevent accidental replacement with an
unrelated or older state. Do not bypass those checks until proving the source,
target, and expected next plan.

The GCS backend provides state locking and recommends object versioning. It has
additional sharp edges:

- IAM changes on the bucket are eventually consistent and can return temporary
  403 errors.
- Backend credentials supplied through configuration can be copied into
  `.terraform` and plan files; prefer environment-based short-lived auth.
- Changing a customer-supplied encryption key requires manual object rewrite.
- Changing a KMS key takes full effect on the next state write; retain the old
  key until every state object has been rewritten.
- Losing or destroying the encryption key makes state unrecoverable.

Practice two distinct exercises in an isolated environment:

1. Lose state while infrastructure remains; rebuild ownership and prove a
   no-change plan.
2. Lose infrastructure while state remains; determine what state can and cannot
   restore, including data and external side effects.

A 2025 regulated-brownfield report recommends these drills because operator
knowledge is tacit and disaster recovery cannot be learned safely during an
incident. Capture the exact commands, permissions, and manual workarounds.

## Lifecycle Protection Is Layered

`prevent_destroy` rejects a plan only while the lifecycle block remains in
configuration. Removing the whole resource block removes the protection along
with it. It also does not protect console/API deletion.

Cloud/provider deletion protection may behave differently. Some providers show
a destructive plan and fail only during apply because the provider cannot
consistently raise the protection conflict during planning. Reviewers must check
both Terraform lifecycle and remote protection state.

`create_before_destroy` propagates through dependencies and can be impossible
for globally unique physical names. `ignore_changes` suppresses desired-vs-live
management for selected attributes and can hide security drift. `replace_triggered_by`
requires managed-resource references, not arbitrary values; use `terraform_data`
when a plain value intentionally controls replacement.

## Provider Upgrade Discipline

Upgrade providers separately from infrastructure changes:

1. Read every intervening major upgrade guide and relevant minor notes.
2. Run `terraform init -upgrade` only in the upgrade change.
3. Review `.terraform.lock.hcl` source, version, and platform hashes.
4. Produce refreshed plans for representative states.
5. Search the provider issue tracker for used high-risk resources.
6. Canary low-blast-radius states before shared IAM/network/data states.
7. Keep a tested rollback to the prior provider lockfile and state version.

Provider rollback is not always safe after state upgraders write a newer schema.
Test downgrade against a copied state before promising it as rollback.

## Test Semantics Can Create Real Infrastructure

`terraform test` run blocks use apply behavior unless configured otherwise.
Mocks and overrides are useful for module logic, but they do not prove provider
CRUD, cloud policy, eventual consistency, quotas, or import behavior.

Use three layers:

1. `validate` and plan-mode tests for contracts and invariants.
2. Provider-backed tests in isolated disposable projects/accounts.
3. Migration rehearsals against representative resources with real state and
   recovery drills.

Never run apply-mode tests against a user's live authenticated production
workspace. Isolate backend, credentials, quotas, and cleanup ownership.

## Source Links

- https://github.com/hashicorp/terraform/releases/tag/v1.15.8
- https://github.com/hashicorp/terraform/blob/v1.10/CHANGELOG.md
- https://github.com/hashicorp/terraform/blob/v1.11/CHANGELOG.md
- https://github.com/hashicorp/terraform/blob/v1.14/CHANGELOG.md
- https://github.com/hashicorp/terraform/issues/37361
- https://github.com/hashicorp/terraform/issues/35596
- https://github.com/hashicorp/terraform/issues/37712
- https://developer.hashicorp.com/terraform/language/import/bulk
- https://developer.hashicorp.com/terraform/language/import/generating-configuration
- https://developer.hashicorp.com/terraform/language/manage-sensitive-data
- https://developer.hashicorp.com/terraform/language/backend/gcs
- https://www.evalapply.org/posts/systems-approach-to-infrastructure-as-code/index.html
