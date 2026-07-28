# State and Refactoring

Sources: HashiCorp Terraform state, backends, locking, refactoring, moved blocks, removed blocks, state command, and workspace documentation

Covers: state safety, backend choice, locking, drift, state inspection, supported refactors, ownership removal, and recovery.

## State Invariant

Terraform state stores the one-to-one binding between a resource instance
address and a remote object. It also contains provider metadata, dependencies,
outputs, and potentially secrets.

Protect it with:

- remote durable storage
- locking
- encryption
- least-privilege access
- versioning/backups
- serialized writers
- auditable runs

Never commit state or edit its JSON directly.

## Backend Boundary

State boundaries should follow owner, lifecycle, privilege, and blast radius.
Too-large state makes every plan risky; too-small state creates remote-state
coupling and orchestration overhead.

Backend configuration is bootstrap-sensitive. Migrate with `terraform init
-migrate-state`, a backup, exclusive access, and post-migration verification.

## Locking and Concurrency

Only one mutation may operate on a state at a time. Investigate lock ownership
before force-unlock; a still-running apply can corrupt coordination.

Saved plans embed prior state and input decisions. Regenerate a plan after state,
configuration, variables, credentials, or provider versions change.

## Drift

Normal plan refreshes remote objects before diffing unless configured otherwise.
Use refresh-only planning to review externally made changes without immediately
accepting or reverting them.

| Drift intent | Action |
|---|---|
| External change should be reverted | Normal reviewed plan/apply |
| External change should become desired | Update config, then plan |
| State must accept observed change first | Refresh-only plan/apply with explicit review |
| Object deleted externally | Decide recreate vs remove ownership before apply |

## Refactoring

Use declarative `moved` blocks for address changes:

```hcl
moved {
  from = google_storage_bucket.assets
  to   = module.storage.google_storage_bucket.assets
}
```

This documents the migration and lets every state pass through it. Prefer it to
ad hoc `terraform state mv` for versioned configuration refactors.

## Removing Ownership

Use a `removed` block with destroy disabled when Terraform should forget an
object while leaving it live. Review current version syntax and plan output.
This intentionally creates unmanaged infrastructure, so record the new owner.

`terraform state rm` is an imperative last resort. If configuration still
declares the resource, the next plan proposes a create.

## State Command Safety

Before `state mv`, `state rm`, `state replace-provider`, or state push:

1. Stop all writers.
2. Pull a state backup.
3. Record lineage/serial and exact addresses.
4. Define the expected post-command plan.
5. Rehearse on a copy when production risk is high.
6. Run a complete plan afterward.

## Recovery Ladder

1. Fix configuration or variables.
2. Reinitialize providers/backend.
3. Review refresh-only plan.
4. Import an unmanaged live object.
5. Use moved/removed blocks.
6. Use precise state commands with backup.
7. Restore a versioned state snapshot only through documented backend process.

Do not remove state bindings merely to silence an error.

## Workspaces

CLI workspaces provide multiple state instances for one configuration but do not
create strong permission or code boundaries. Use separate roots/backends when
environments have different owners, credentials, or infrastructure shapes.

## Review Checklist

- Backend is remote, locked, encrypted, and recoverable.
- State boundary matches blast radius.
- Writers are serialized.
- Refactors use moved blocks.
- Ownership removal names the next owner.
- State commands have backup and expected-plan evidence.
- Full plan follows every state operation.
- State artifacts and outputs do not leak secrets.

## Source Links

- https://developer.hashicorp.com/terraform/language/state
- https://developer.hashicorp.com/terraform/language/state/locking
- https://developer.hashicorp.com/terraform/language/state/refactor
- https://developer.hashicorp.com/terraform/language/state/remove
- https://developer.hashicorp.com/terraform/language/block/moved
- https://developer.hashicorp.com/terraform/language/block/removed
