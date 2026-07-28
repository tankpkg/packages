# Adoption and Cutover

Sources: Pulumi import, preview, refresh, protect, aliases, retainOnDelete, and drift documentation; Google Cloud reliability and asset-management guidance

Covers: import waves, backups, no-change convergence, writer freeze, protection, verification, rollback, handoff, and post-adoption refactoring.

## Preflight Gate

Require these artifacts before any state mutation:

- approved resource ledger
- current-owner evidence
- provider/type/import-ID mapping
- Pulumi project and final stack
- explicit provider targets
- old IaC state and code backup
- Pulumi stack export if the stack already exists
- rollback owner and procedure
- service health checks
- maintenance/change freeze window

Importing is a state mutation even when it does not change the GCP resource.

## Establish the Final Identity

Choose the final project, stack, logical name, parent, provider, and physical
name before import. Correcting these later requires aliases or state migration.

For critical resources, set `protect: true` during adoption. Use
`retainOnDelete` only when the explicit desired behavior is to relinquish state
ownership while leaving the cloud resource unmanaged; it is not a substitute
for protection.

## Import Waves

Keep waves small enough to diagnose and roll back.

| Wave | Typical content | Gate |
|---|---|---|
| 0 | Providers, config, project context, read-only references | Correct targets, no resources created |
| 1 | Shared network, APIs, DNS/KMS foundations | No destructive diff |
| 2 | Identity and IAM foundations | Principal and condition parity |
| 3 | Stateful data and storage | Backup, protection, retention parity |
| 4 | Compute and managed services | Runtime health parity |
| 5 | Edge, load balancing, monitoring, fine IAM | End-to-end health |

Adjust order to the actual graph. Importing does not recreate dependencies, but
provider reads and parent relationships still need a coherent model.

## Per-Wave Procedure

1. Freeze mutations from the current owner for the wave.
2. Capture fresh inventory and health evidence.
3. Run import in preview-only mode where supported.
4. Import canonical IDs into final Pulumi identities.
5. Save generated code without exposing secrets.
6. Reconcile declarations with live immutable/defaulted values.
7. Run `pulumi refresh --preview-only`.
8. Run full `pulumi preview --diff`.
9. Require zero unexplained create, update, replace, or delete.
10. Run service and access health checks.
11. Record ownership transfer and proceed to the next wave.

## Convergence Triage

| Preview operation | Likely cause | Response |
|---|---|---|
| Create | Missing import, wrong stack, wrong logical graph | Stop; do not apply |
| Replace | Immutable mismatch, wrong type/provider, identity change | Stop; align code/import |
| Delete | Code omitted imported child or old ownership cleanup leaked in | Stop; restore model |
| Update | Provider default or desired/live mismatch | Review field and operational impact |
| Same | Candidate steady state | Confirm drift and health checks |

Do not normalize architecture during convergence. Preserve existing names,
regions, network links, IAM, retention, scaling, and service settings first.

## Dual-Control Prevention

At cutover, ensure the previous system cannot continue to mutate migrated rows.

For Terraform:

- stop apply jobs
- preserve state backup
- remove migrated resources from old state only through reviewed ownership
  transfer steps
- do not run `terraform destroy`
- archive code/state with a migration record

For scripts or console runbooks:

- revoke or narrow mutation credentials
- update operational documentation
- point automation to Pulumi workflow
- monitor audit logs for old writers

## Rollback Model

Rollback means restoring management ownership, not deleting and recreating live
resources.

Possible rollback:

1. Stop Pulumi writers.
2. Export Pulumi state and retain migration evidence.
3. Restore old code/state ownership mapping from backup.
4. Re-enable the old pipeline only after a no-change plan.
5. Remove Pulumi ownership without deleting provider resources using the
   documented state/retention procedure.

Rehearse rollback for high-risk waves. Never improvise by deleting Pulumi state
entries or running destroy commands.

## Cutover Acceptance

Require all of:

- every in-scope resource has exactly one owner
- no blocked ledger rows are silently omitted
- full stack refresh preview is understood
- full detailed preview is zero-change or contains only approved non-destructive
  normalization
- no replacement or delete
- IAM principals and conditions match
- service health, data access, DNS, and network paths pass
- CI uses the intended short-lived identity
- old writer is disabled and monitored
- backups and rollback evidence are retained

## Post-Adoption Refactoring

Wait for a stable observation period. Then make one category of change at a
time:

1. Extract components with aliases for reparented children.
2. Rename logical resources with aliases.
3. Replace raw IDs with resource output references.
4. Normalize configuration and provider instances.
5. Remove temporary protection only through explicit review.
6. Redesign or replace infrastructure in separately approved projects.

Keep adoption and modernization in different pull requests and deployment
events. This preserves an auditable baseline and isolates failures.

## Source Links

- https://www.pulumi.com/docs/iac/guides/migration/import/
- https://www.pulumi.com/docs/iac/operations/stack-management/drift/
- https://www.pulumi.com/docs/iac/concepts/resources/options/protect/
- https://www.pulumi.com/docs/iac/concepts/resources/options/retainondelete/
- https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/
