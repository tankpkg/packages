# Terraform GCP to Pulumi

Sources: Pulumi migration from Terraform documentation, Pulumi convert and import CLI documentation, Terraform state and provider documentation, Pulumi Google Cloud Classic Registry

Covers: source/state assessment, HCL conversion, tfstate adoption, provider mapping, unsupported constructs, dual-control prevention, validation, and Terraform retirement.

## Two Inputs, Two Jobs

Terraform migrations have two independent sources:

| Source | Tells you | Pulumi operation |
|---|---|---|
| `.tf` HCL and modules | Intended configuration and abstractions | `pulumi convert --from terraform` or manual rewrite |
| `.tfstate` | Real provider IDs and current ownership | `pulumi import --from terraform` where supported |

Neither is sufficient alone. Code can be stale; state can omit intent and
module design. Compare both to live GCP inventory.

## Readiness Assessment

Capture:

- Terraform and provider versions
- backend and workspace
- latest state serial and backup
- selected workspace/environment
- module sources and versions
- provider aliases/projects/regions
- resources excluded by targets or workspaces
- import blocks, moved blocks, and state moves
- pending plan and known drift
- CI apply identity and schedule

Run a read-only Terraform plan before freeze. Resolve unknown drift or document
why live infrastructure is authoritative.

## Convert the Program

Use Pulumi's Terraform converter as a translation accelerator:

```bash
pulumi convert --from terraform --language typescript --out pulumi-infra
```

Check current CLI help and migration docs for supported flags and languages.
Conversion may emit diagnostics or placeholders for unsupported expressions,
providers, modules, provisioners, or lifecycle behavior.

Review output for:

- provider aliases and target projects
- data sources vs managed resources
- `for_each` keys and resource identity
- dynamic blocks and conditional resources
- lifecycle ignore/prevent/replace behavior
- explicit dependencies
- secrets and sensitive variables
- remote-state references
- module boundaries
- local-exec/remote-exec provisioners

Rewrite unsupported behavior explicitly; do not retain shell mutation as an
opaque compatibility layer.

## Adopt Terraform State

Pulumi documents Terraform-aware state adoption with:

```bash
pulumi import --from terraform /path/to/terraform.tfstate
```

Use the current official syntax and preview options. Adopt into the final Pulumi
stack after the converted/maintained program has been reviewed.

State adoption checklist:

1. Freeze Terraform applies.
2. Pull and back up the exact current state.
3. Verify state lineage/workspace and GCP identity.
4. Map every Terraform address to a Pulumi declaration.
5. Identify provider aliases and module nesting.
6. Run import preview.
7. Import in small waves if the estate is large.
8. Reconcile generated/provider-read inputs.
9. Run full Pulumi refresh preview and detailed preview.
10. Require no replacement or delete.

## Address Mapping

Maintain a ledger:

| Terraform address | Provider ID | Pulumi type | Logical name/parent | Status |
|---|---|---|---|---|
| `module.net.google_compute_network.main` | project/network | `gcp:compute/network:Network` | network/main | imported |

Account for:

- `count` indexes
- `for_each` string keys
- module addresses
- provider aliases
- resources moved in state
- tainted or deposed instances
- resources present in GCP but absent from state

If state is unreliable, use live GCP direct import for affected resources
instead of trusting a stale provider ID mapping.

## Terraform/Pulumi Semantic Differences

| Terraform concept | Pulumi direction |
|---|---|
| Variables/locals | Stack config and ordinary language values |
| Resource references | Inputs/Outputs dataflow |
| Modules | Components or language packages |
| Data sources | Provider invoke/get functions |
| `depends_on` | Output edge or `dependsOn` |
| `prevent_destroy` | `protect` |
| `ignore_changes` | `ignoreChanges`, only with named external owner |
| Moved block | Resource aliases/state migration |
| Workspaces | Pulumi stacks, with boundary review |
| Remote state output | Stack reference or external contract |

Translate intent, not syntax. Preserve behavior through adoption; improve the
abstraction after steady state.

## Retire Terraform Safely

Do not prove migration by running `terraform destroy` or removing resources
from configuration and applying a delete plan.

Retirement sequence:

1. Disable scheduled and merge-triggered Terraform applies.
2. Preserve code, lockfile, state, plan, and provider versions.
3. Transfer each resource to Pulumi and verify no-change state.
4. Remove old mutation credentials or scopes.
5. Mark the Terraform workspace archived/read-only.
6. Monitor GCP audit logs for unexpected old writers.
7. Retain rollback artifacts for the agreed window.

If Terraform must continue managing out-of-scope resources, surgically separate
ownership and verify its next plan does not change Pulumi-owned objects.

## Acceptance Gate

- Converted code compiles and passes language checks.
- Every tfstate resource is mapped, excluded with owner, or blocked.
- Every Pulumi resource has the expected GCP provider ID.
- Pulumi preview has no unexplained operation.
- Terraform's next read-only plan cannot mutate migrated resources.
- CI ownership is singular.
- Runtime health and IAM parity are verified.

## Source Links

- https://www.pulumi.com/docs/iac/guides/migration/migrating-to-pulumi/from-terraform/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_convert/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_import/
- https://www.pulumi.com/registry/packages/gcp/
