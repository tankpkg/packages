# Reader Outcomes and Validation Plan

This design brief shows the reasoning behind the example documentation set and
defines how to gather evidence. It is a validation plan, not a claim that
representative-reader testing has already occurred.

## Diagnosed Need

Observed failures:

- Integrators expose download actions immediately after `202 Accepted`.
- Operators rerun generation when only webhook delivery failed.
- New engineers search conceptual pages for exact retry limits.
- Experienced operators cannot find recovery gates during incidents.

Documentation is appropriate for the mental-model, retrieval, and point-of-work
gaps. Product controls are still required for worker fencing, conditional state
transitions, and webhook deduplication.

## Reader Model

| Audience | Existing knowledge | Likely misconception | Immediate need |
| --- | --- | --- | --- |
| API integrator | HTTP request-response and webhooks | A success response means work finished | Complete a correct integration |
| New engineer | Basic queues and workers | One retry mechanism owns all failures | Build a causal model |
| Experienced engineer | Distributed job systems | Product-specific state names are predictable | Retrieve exact guarantees quickly |
| On-call operator | Monitoring and incident response | Missing webhook means generation failed | Diagnose and recover safely |

## Observable Outcomes

After using the relevant file, a representative reader can:

1. Predict whether a file exists from state rather than HTTP status.
2. Distinguish processing retry from notification-delivery retry.
3. Implement idempotent request and webhook handling.
4. Find exact state transitions without reading the conceptual explanation.
5. Diagnose delayed notification without rerunning generation.
6. Recover paused processing without activating two worker fleets.
7. Apply the boundary model when webhooks are replaced by polling.

## File-to-Outcome Alignment

| File | Primary evidence |
| --- | --- |
| Concept | Correct prediction under a changed scenario |
| How-to | Working integration across normal, duplicate, delayed, and failed paths |
| Reference | Accurate retrieval of a state, transition, or guarantee |
| Troubleshooting | Diagnosis from export state and delivery evidence |
| Runbook | Safe recovery with hazards, gates, and invariants preserved |

## Reader Tests

### Prediction Test

Present: `202 Accepted`, state `queued`, no webhook.

Pass when the reader says the request is accepted, the file is not ready, and
missing webhook is expected before terminal state.

### Contrast Test

Present two failures:

- A worker times out during storage.
- A completion webhook receives `503`.

Pass when the reader says the first may repeat generation or upload, while the
second repeats notification only.

### Integration Test

Ask the reader to handle a request timeout, a duplicate completion event, and
an expired download URL.

Pass when one export is created for the idempotency key, one local completion
effect occurs for the event ID, and the client refreshes status for a new URL.

### Retrieval Test

Ask for the allowed transition out of `retrying` and its owner.

Pass when the reader finds the answer in the reference without reading the
concept or runbook.

### Incident Test

Simulate growing queue age while the original fleet's telemetry is missing.

Pass when the operator refuses to start a replacement fleet until independent
evidence proves fencing.

### Transfer Test

Replace webhooks with polling.

Pass when the reader preserves acceptance, processing, and completion
boundaries and changes only the delivery mechanism.

## Evidence to Record

- Wrong predictions
- Time to find exact state behavior
- Skipped prerequisites or safety gates
- Duplicate client effects
- Unnecessary generation retries
- External searches and dead-end navigation
- Confident but incorrect explanations

Revise the responsible layer. Change prose when the relationship is
misunderstood, navigation when the answer is known but not found, and the
product when documentation accurately exposes unsafe or unnecessary work.
