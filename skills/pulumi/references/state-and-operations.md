# State and Operations

Sources: Pulumi documentation on state and backends, stack management, preview, update, refresh, drift, state export/import, cancellation, and deployment safety

Covers: backend choice, operation lifecycle, drift detection, concurrency, recovery, and last-resort state repair.

## State Contract

State maps Pulumi resource identities to provider IDs and stores inputs,
outputs, dependencies, provider references, pending operations, and secret
ciphertext. Losing or corrupting state can turn known resources into apparent
creates or orphan management relationships.

Protect state as production data:

- durable storage
- encryption at rest and in transit
- access control
- update locking
- version history or backups
- auditability
- tested recovery

Do not commit exported state. Treat exports as sensitive even if secrets remain
encrypted because metadata, endpoints, IDs, and topology are exposed.

## Backend Decision

| Context | Direction |
|---|---|
| Team or production estate | Managed Pulumi Cloud unless policy requires DIY |
| Regulated self-managed storage | Supported DIY object backend with versioning |
| Offline local experiment | Local backend only temporarily |

DIY storage moves responsibility for locking behavior, backup, recovery,
access, secrets-provider compatibility, and operational observability to the
team. Choose it for a concrete control requirement, not to avoid setup.

## Operation Sequence

Use this sequence for routine changes:

1. Select and display the fully qualified target stack.
2. Verify cloud identity and provider target.
3. Run language-level checks.
4. Run `pulumi preview --diff`.
5. Review operation counts and detailed property changes.
6. Obtain approval appropriate to the environment.
7. Run `pulumi up` through the serialized deployment path.
8. Verify outputs and service health.

Preview is a prediction. Cloud-side validation, races, quota, policy, or an
unknown output can still fail during update. Plan rollback and recovery for
high-risk changes.

## Drift Decision

Start read-only:

```bash
pulumi refresh --preview-only --stack production
```

| Finding | Response |
|---|---|
| No drift | Continue with code preview |
| Authorized manual change should remain | Update code, then reconcile state |
| Unauthorized manual change | Decide whether to revert with `up` or accept via refresh |
| Resource deleted outside Pulumi | Determine restore vs state acceptance before action |
| Provider returns normalized defaults | Align code/state only after understanding provider behavior |

`pulumi refresh` writes observed provider values into state. It does not update
the program. After refresh, run preview to see what the program will attempt to
change back.

## Concurrency

Only one mutation should run against a stack at a time. Do not run local and CI
updates concurrently. Managed backends help coordinate locks, but operational
ownership still matters when canceling or recovering failed deployments.

Use target flags sparingly. A targeted update can violate assumptions in the
full dependency graph and leave the stack in a state never reviewed as a whole.
Follow with a complete preview.

## Failed Updates

Classify before acting:

| Failure | First action |
|---|---|
| Language/program crash | Fix program; preview again |
| Authentication/permission | Restore correct short-lived identity |
| Provider API partial failure | Inspect cloud object and stack pending operation |
| Interrupted update | Inspect stack history and pending operations |
| Concurrent update | Identify owner; do not blindly cancel |
| State mismatch | Export state and investigate before repair |

Canceling the CLI process does not guarantee the provider operation stopped.
Cloud APIs may complete asynchronously. Observe the provider and stack before
retrying to avoid duplicate operations.

## Recovery Ladder

Use the least invasive layer that solves the problem:

1. Fix code or configuration and rerun preview.
2. Refresh read-only to diagnose drift.
3. Refresh state when live infrastructure is intentionally authoritative.
4. Import a real but unmanaged resource.
5. Use supported `pulumi state` commands for a precise identity operation.
6. Export, review, and re-import state only as a documented last resort.

Before steps 5-6:

- stop writers
- export the stack
- record current stack history
- inspect the exact URN and provider ID
- rehearse on a non-production copy when feasible
- define the expected post-repair preview

Never remove a state entry merely to make an error disappear. The cloud object
will remain and the next program evaluation may try to create a duplicate.

## Resource Protection During Operations

Apply `protect` to resources where accidental deletion is categorically worse
than a blocked deployment: production databases, root DNS zones, shared KMS
keys, organization IAM foundations, and state storage.

Protection is not backup. Maintain provider-native recovery controls such as
database backups, bucket versioning, and retention policies.

## Provider Upgrades

Provider upgrades can change defaults, schemas, diff behavior, import ID
parsing, and replacement decisions. Upgrade in isolation:

1. Read release notes.
2. Update lockfiles.
3. Preview representative non-production stacks.
4. Inspect normalized/defaulted properties.
5. Roll through stacks gradually.

## Operational Evidence

Capture without leaking secrets:

- fully qualified stack
- commit SHA and dependency lockfile
- CLI and provider versions
- preview operation counts
- approval identity
- update URL/history identifier
- post-update outputs and health checks

## Review Checklist

- Backend is durable and access-controlled.
- Production changes have a reviewed detailed preview.
- Stack mutation is serialized.
- Drift is observed before it is accepted.
- Failed operations are classified before retry.
- State export exists before state surgery.
- Protection complements provider-native backup.
- Provider upgrades are isolated from feature changes.

## Source Links

- https://www.pulumi.com/docs/iac/concepts/state-and-backends/
- https://www.pulumi.com/docs/iac/operations/stack-management/
- https://www.pulumi.com/docs/iac/operations/stack-management/drift/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_preview/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_refresh/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_stack_export/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_stack_import/
