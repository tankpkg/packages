# Convergence and Cutover

Sources: HashiCorp state, import, plan, moved/removed blocks, and backend documentation; Google Cloud Terraform operations, state-storage, and reliability guidance

Covers: backend preflight, import waves, plan triage, writer freeze, verification, rollback, retirement, and post-adoption changes.

## Preflight

Require:

- approved ledger and wave
- final root/module addresses
- remote locked backend
- state/config backups
- locked provider versions
- exact provider aliases and identity
- full import IDs
- previous-writer freeze
- rollback owner
- service/IAM health checks

Import changes state even when the GCP object is unchanged.

## State Bootstrap

Create/protect the state backend separately. For GCS state, enable versioning,
restrict access, and prevent accidental bucket deletion. Avoid storing state in
the same unproven root being migrated.

## Waves

| Wave | Content | Gate |
|---|---|---|
| 0 | Backend, providers, variables, data reads | Correct targets |
| 1 | APIs, network, DNS, KMS | No destructive plan |
| 2 | Identity and IAM foundations | Principal/condition parity |
| 3 | Stateful storage/data | Backup and lifecycle parity |
| 4 | Compute and managed services | Runtime health |
| 5 | Edge, monitoring, fine IAM | End-to-end health |

Keep waves small enough to diagnose and reverse ownership.

## Per-Wave Procedure

1. Freeze old mutation paths.
2. Capture fresh inventory and state backup.
3. Run init/validate and import plan.
4. Apply reviewed import operations.
5. Reconcile configuration without modernization.
6. Run full plan.
7. Stop on unexplained mutation.
8. Verify service, network, data, and IAM health.
9. Record ownership and proceed.

## Plan Triage

| Plan | Response |
|---|---|
| Create | Missing/wrong import, state, address, or collection key; stop |
| Replace | Immutable/type/provider/address mismatch; stop |
| Destroy | Omitted config or wrong ownership; stop |
| Update | Review default/live/desired difference field by field |
| No changes | Candidate adoption baseline; verify health and old writer |

## Dual Control

Disable scripts, console runbooks, Config Connector reconciliation, Deployment
Manager, or alternate IaC for migrated objects. Revoke old mutation credentials
and monitor audit logs.

If another Terraform state currently owns the object, migrate that state or use
reviewed moved/state operations; do not import a duplicate binding.

## Rollback

Rollback restores ownership, not infrastructure:

1. Stop Terraform writers.
2. Preserve current state and evidence.
3. Restore old owner/state mapping from backup.
4. Require its no-change plan before re-enabling.
5. Remove new ownership with a reviewed `removed`/state process that does not
   destroy the GCP object.

Never improvise rollback with `terraform destroy`.

## Acceptance

- Every in-scope object has one owner/address.
- Full plan is no-change or only explicitly approved normalization.
- No replacement/destroy.
- IAM and runtime checks pass.
- CI uses short-lived intended identity.
- Old writer is disabled and monitored.
- State recovery and rollback evidence are retained.

## Modernize Later

After a stable period, use separate changes for module extraction, address moves,
references replacing raw IDs, provider normalization, or infrastructure redesign.
Use `moved` blocks and full plan review.

## Source Links

- https://developer.hashicorp.com/terraform/language/state
- https://developer.hashicorp.com/terraform/language/import
- https://developer.hashicorp.com/terraform/language/block/moved
- https://developer.hashicorp.com/terraform/language/block/removed
- https://docs.cloud.google.com/docs/terraform/resource-management/store-state
