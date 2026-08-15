# Integrate Async Exports

This guide adds async exports to a client application. It assumes you can send
authenticated HTTP requests and expose an HTTPS webhook endpoint.

For the underlying model, read [How Async Exports Work](../concepts/how-async-exports-work.md).

## Before You Begin

You need:

- An API token with `exports:create` and `exports:read`
- A durable place to store the export ID
- An HTTPS webhook endpoint
- Idempotent handling keyed by `event_id`

## 1. Submit the Export

```http
POST /v1/exports HTTP/1.1
Host: api.example.test
Authorization: Bearer EXAMPLE_TOKEN
Idempotency-Key: order-export-2026-08-15
Content-Type: application/json

{
  "type": "orders",
  "format": "csv",
  "webhook_url": "https://client.example.test/export-events"
}
```

Expected response:

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "id": "exp_01JABC123",
  "status": "queued",
  "status_url": "/v1/exports/exp_01JABC123"
}
```

Store `id` before updating the interface. Do not show a download action yet.
The response confirms acceptance, not completion.

If the request times out, retry with the same `Idempotency-Key`. Do not create a
new key until you have reconciled the first request.

## 2. Represent Pending State

Show the export as queued or processing. Preserve the export ID so the client
can recover after a page reload or webhook delay.

Use the status endpoint when the user needs current state:

```http
GET /v1/exports/exp_01JABC123 HTTP/1.1
Host: api.example.test
Authorization: Bearer EXAMPLE_TOKEN
```

Do not poll more frequently than the `Retry-After` response header.

## 3. Handle Completion Events

Example event:

```json
{
  "event_id": "evt_01JDEF456",
  "type": "export.completed",
  "export_id": "exp_01JABC123",
  "occurred_at": "2026-08-15T19:33:58Z"
}
```

Process the event in this order:

1. Verify the signature against the raw request body.
2. Reject timestamps outside the accepted replay window.
3. Retrieve the authoritative export status using `export_id`.
4. If status is not `completed`, return a retryable error and do not record
   `event_id`.
5. Begin a local database transaction.
6. Insert `event_id` under a unique constraint.
7. If the insert conflicts, roll back and return `204 No Content`.
8. Update the local export to `completed`.
9. Commit the event ID and local state update atomically.
10. Return a successful response after the transaction commits.

Webhook delivery is at least once. Duplicate events are expected behavior.

## 4. Retrieve the File

A completed status includes a short-lived download URL:

```json
{
  "id": "exp_01JABC123",
  "status": "completed",
  "download_url": "https://downloads.example.test/example-signed-url",
  "download_expires_at": "2026-08-15T20:33:58Z"
}
```

Fetch a new status response when the URL expires. Do not persist the signed URL
as the durable identity of the export.

## 5. Verify the Integration

Run these checks in a non-production environment:

| Scenario | Expected result |
| --- | --- |
| Normal export | UI observes a valid monotonic path and reaches `completed`; it may not observe every intermediate state |
| Duplicate webhook | One local completion update occurs |
| Delayed webhook | Polling still discovers `completed` |
| Request timeout and retry | One export exists for the idempotency key |
| Worker retry | The client sees one export and one terminal result |
| Terminal failure | UI shows a recoverable error without a download action |

## If Verification Fails

- If status is `completed` but no event arrived, follow
  [Webhook Missing](../troubleshooting/troubleshoot-exports.md#webhook-missing).
- If an export remains nonterminal, follow
  [Export Stuck](../troubleshooting/troubleshoot-exports.md#export-stuck).
- For exact state semantics, use
  [Export Lifecycle Reference](../reference/export-lifecycle.md).
