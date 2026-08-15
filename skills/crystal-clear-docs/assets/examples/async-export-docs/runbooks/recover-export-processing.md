# Recover Export Processing

Use this fictional runbook when exports accumulate because queue consumption is
paused or worker leases no longer progress.

> **Safety invariant:** Never start a second worker fleet until the original
> fleet is fenced from claiming jobs. Concurrent recovery fleets can duplicate
> non-idempotent side effects and invalidate lease assumptions.

## Authority and Roles

| Role | Responsibility |
| --- | --- |
| Incident commander | Authorizes recovery phases and accepts degraded operation |
| Export operator | Fences workers, restores processing, and verifies invariants |
| Application observer | Confirms client-visible status and download behavior |

Require two-person confirmation before fencing or activating a replacement
fleet.

Escalation contacts:

- Export service owner: `<on-call contact>`
- Platform incident commander: `<incident escalation contact>`

## Trigger

Use this runbook when all are true:

- Nonterminal export age exceeds the service objective.
- Queue depth grows or remains flat while intake continues.
- Normal autoscaling or worker restart procedures did not recover progress.

## Stop and Escalate

Stop if:

- You cannot identify the active worker fleet.
- More than one fleet can claim jobs.
- Export-store writes are unavailable or inconsistent.
- Terminal exports are moving back to nonterminal states.
- The observed topology differs from this runbook.

When a stop condition occurs:

1. Do not start, stop, fence, or reconfigure another worker fleet.
2. Keep intake paused if it is already paused. Do not change a confirmed fence.
3. Contact both escalation roles above.
4. Provide the incident ID, observed topology, queue age, active lease evidence,
   last successful completion, and every action already taken.
5. Resume only from a documented decision by the incident commander and export
   service owner.

## Phase 1: Stabilize Intake

1. Declare the incident and assign roles.
2. Pause new export submissions using the approved feature control.
3. Verify the API returns the documented maintenance response.
4. Record queue depth, oldest message age, nonterminal counts, and active
   worker leases.

**Gate:** Continue only when intake is paused and baseline evidence is recorded.

## Phase 2: Fence the Original Fleet

1. Disable job claims for the original fleet.
2. Wait for active leases to expire or revoke them with the approved control.
3. Verify from the queue, export store, and worker telemetry that no original
   worker can claim or renew a job.
4. Record the fencing evidence and both approvers.

Do not treat missing telemetry as proof that the fleet is fenced.

## Phase 3: Start Controlled Processing

1. Start one replacement worker with concurrency `1`.
2. Confirm it claims only `queued`, `retrying`, or `processing` with an expired
   lease and receives a new fencing token.
3. Verify one export reaches `completed`.
4. If the attempt returns to `retrying`, keep concurrency at `1`, diagnose the
   dependency failure, and stop if the cause remains unresolved.
5. Confirm no terminal state regressed and no stale worker committed results.
6. Confirm the completed export references the immutable object written under
   the current lease token.
7. Increase concurrency in controlled steps while monitoring lease conflicts,
   error rate, queue age, and storage writes.

**Gate:** Restore normal capacity only after progress is stable and invariants
hold across a representative sample.

## Phase 4: Restore Intake

1. Re-enable export submission for a small traffic cohort.
2. Verify new requests receive `202` and enter `queued` once.
3. Confirm queue age continues to fall.
4. Restore full intake.

## Completion Criteria

- One worker fleet can claim jobs.
- Only current lease tokens can commit attempt results.
- Completed exports reference immutable objects from the current lease token.
- Queue age and depth return within objectives.
- No terminal export regressed.
- Completed files match one terminal export ID each.
- Webhook delivery proceeds independently of generation recovery.
- Monitoring and normal autoscaling are restored.

## Rollback and Recovery

Before replacement workers process jobs, stop them and restore the original
fleet only after proving it is healthy and authoritative.

After replacement workers process jobs, do not reactivate the original fleet.
Keep it fenced, reconcile leases and attempts, and use the approved failback
procedure.

## Follow-Up

Capture the oldest affected export, duplicate-work count, customer-visible
delay, and any manual state changes. Add a regression test for the failure that
prevented automatic recovery.
