# Events, Workflows, and Automation

Sources: Intercom Developer Documentation, Intercom Workflows documentation

Covers: trackEvent API, event metadata, workflow triggers from frontend, webhooks, segmentation, A/B testing patterns.

For the trackEvent method signature, see `references/js-api-reference.md`. For phone callback patterns using trackEvent, see `references/calling-and-performance.md`.

---

## trackEvent API

Fire custom events to record user actions in Intercom. Events power workflow triggers, segmentation, and behavioral analytics.

```js
// Basic event — no metadata
Intercom('trackEvent', 'completed-onboarding');

// Event with metadata
Intercom('trackEvent', 'upgraded-plan', {
  from_plan: 'starter',
  to_plan: 'pro',
  revenue: { amount: 4900, currency: 'usd' }
});
```

### Naming Conventions

Use past-tense verb-noun format. This signals that the action already occurred and reads naturally in Intercom's event log.

Good names:
- `created-project`
- `upgraded-plan`
- `completed-onboarding`
- `viewed-pricing`
- `requested-phone-callback`
- `feature-activated`

Avoid:
- Present tense: `create-project`, `upgrade-plan`
- Vague names: `button-click`, `page-view`
- PII in event names: `user-john@example.com-signed-up`
- Spaces or special characters — use hyphens

Event names are case-sensitive. Standardize on lowercase-hyphenated across your codebase.

### Advanced Example

```js
// Track a feature activation with rich context
Intercom('trackEvent', 'feature-activated', {
  feature: 'analytics-dashboard',
  plan: 'enterprise',
  days_since_signup: 7,
  is_trial: true,
  trial_end_date: 1735689600,  // Unix timestamp — key must end in _date
  docs_url: 'https://docs.example.com/analytics'
});
```

---

## Event Metadata Types

Intercom supports seven metadata value types. Keep all metadata flat — nested JSON objects are not supported (except for Rich Link and Monetary, which have defined schemas).

| Type | Example | Notes |
|------|---------|-------|
| String | `{ plan: 'enterprise' }` | Most common type; use for labels, names, identifiers |
| Number | `{ items: 5 }` | Integer or float; use for counts, scores, quantities |
| Boolean | `{ is_trial: true }` | Use for flags and binary states |
| Date | `{ trial_end_date: 1735689600 }` | Unix timestamp (seconds); key must end in `_date` |
| Link | `{ docs_url: 'https://docs.example.com' }` | Plain URL string; renders as clickable link |
| Rich Link | `{ article: { url: 'https://...', value: 'Getting Started' } }` | Clickable link with display label |
| Monetary | `{ revenue: { amount: 9900, currency: 'usd' } }` | Amount in cents; currency as ISO 4217 lowercase |

### Metadata Rules

- Flat structure only. Do not nest arbitrary objects.
- Rich Link and Monetary are the only exceptions — they use a defined two-key schema.
- Monetary amounts are in the smallest currency unit (cents for USD, pence for GBP).
- Date keys must end in `_date` for Intercom to render them as dates in the UI.
- String values over 255 characters are truncated.
- Maximum 5 metadata keys per event is a practical guideline; Intercom does not enforce a hard limit but excessive keys reduce readability.

```js
// Correct monetary metadata
Intercom('trackEvent', 'completed-purchase', {
  revenue: { amount: 9900, currency: 'usd' },  // $99.00
  items: 3,
  invoice_url: { url: 'https://billing.example.com/inv/123', value: 'Invoice #123' }
});

// Incorrect — nested object not supported
Intercom('trackEvent', 'completed-purchase', {
  product: { name: 'Pro Plan', sku: 'PRO-001' }  // Will not work as expected
});
```

---

## Workflow Trigger Pattern

Intercom provides no JavaScript method to trigger a Workflow by ID directly. The correct pattern is event-driven: fire a custom event from the frontend, then configure a Workflow in the Intercom dashboard to listen for that event.

### End-to-End Pattern

**Step 1 — Fire the event from your frontend:**

```js
Intercom('trackEvent', 'requested-phone-callback', {
  phone: user.phone,
  preferred_time: 'morning',
  timezone: 'America/New_York'
});
```

**Step 2 — Configure the Workflow in Intercom dashboard:**

1. Navigate to Workflows in the Intercom dashboard.
2. Create a new Workflow.
3. Set the trigger to "A user performs an event."
4. Enter the exact event name: `requested-phone-callback`.
5. Optionally add conditions on metadata attributes (e.g., `preferred_time is morning`).
6. Add actions: assign to inbox, send a message, create a ticket, notify a teammate.

**Step 3 — Verify the connection:**

Fire the event in your staging environment. Check the Intercom event log for the contact to confirm the event was received. Confirm the Workflow ran by checking the Workflow activity log.

### Why This Pattern Works

Workflows in Intercom are rule-based automations that respond to triggers. Event-based triggers are the most reliable way to connect frontend user actions to backend automation. The event acts as a signal; the Workflow acts as the responder. This decouples your frontend code from Intercom's automation logic — you can change Workflow behavior without deploying frontend code.

---

## Common Event Patterns

Fire these events at the moments described. Include the suggested metadata to enable segmentation and workflow targeting.

| Event Name | When to Fire | Suggested Metadata |
|------------|-------------|-------------------|
| `viewed-pricing` | User visits or scrolls to pricing page | `{ plan_viewed: 'enterprise', source: 'navbar' }` |
| `started-trial` | Trial period begins | `{ plan: 'pro', trial_days: 14, trial_end_date: unixTimestamp }` |
| `completed-onboarding` | User finishes onboarding flow | `{ steps_completed: 5, skipped_steps: 1 }` |
| `requested-phone-callback` | User submits callback request | `{ phone: '...', preferred_time: 'afternoon' }` |
| `upgraded-plan` | User upgrades subscription | `{ from_plan: 'starter', to_plan: 'pro', revenue: { amount: 4900, currency: 'usd' } }` |
| `feature-activated` | User uses a feature for the first time | `{ feature: 'analytics', plan: 'pro' }` |
| `invited-teammate` | User sends a team invitation | `{ invitee_role: 'admin', team_size: 4 }` |
| `exported-data` | User exports a report or dataset | `{ format: 'csv', rows: 1200 }` |
| `connected-integration` | User connects a third-party tool | `{ integration: 'salesforce' }` |
| `cancelled-subscription` | User initiates cancellation | `{ plan: 'pro', reason: 'too-expensive' }` |

---

## Webhooks (Server-Side)

Webhooks deliver real-time HTTP POST notifications from Intercom to your server when specific events occur. They are server-side only — the browser does not receive webhooks directly.

### Supported Webhook Topics

| Topic | Fires When |
|-------|-----------|
| `conversation.created` | A new conversation starts |
| `conversation.closed` | A conversation is closed |
| `conversation.assigned` | A conversation is assigned to a teammate |
| `contact.created` | A new contact is created |
| `contact.signed_up` | A contact converts from visitor to user |
| `ticket.created` | A new ticket is created |
| `ticket.state_updated` | A ticket changes state |
| `call.completed` | A phone call ends |

### Architecture: Webhook to Frontend Update

Webhooks cannot push directly to the browser. Use this pattern to surface real-time updates in your UI:

```
Intercom Event
     |
     v
Intercom Webhook (HTTP POST)
     |
     v
Your Server (webhook endpoint)
     |
     +---> Validate signature
     |
     +---> Process payload
     |
     v
WebSocket or SSE connection
     |
     v
Frontend UI update
```

Text diagram:

```
[Intercom] --webhook POST--> [Your API Server]
                                    |
                              validate + process
                                    |
                         [WebSocket / SSE server]
                                    |
                         [Browser: update UI state]
```

### Webhook Signature Validation

Intercom signs webhook payloads with HMAC-SHA1. Validate every incoming webhook before processing.

```js
// Node.js example
const crypto = require('crypto');

function validateWebhook(rawBody, signature, secret) {
  const expected = crypto
    .createHmac('sha1', secret)
    .update(rawBody)
    .digest('hex');
  return `sha1=${expected}` === signature;
}
```

Check the `X-Hub-Signature` header against your webhook secret from the Intercom developer settings.

---

## Segmentation via Custom Attributes

Segments in Intercom are saved filters on contact or company attributes. Set attributes via `Intercom('boot', {...})` or `Intercom('update', {...})`, then build Segments in the dashboard.

### Attribute-to-Segment Flow

1. Set a custom attribute on the user:

```js
Intercom('update', {
  plan_tier: 'enterprise',
  account_age_days: 45,
  has_completed_onboarding: true
});
```

2. In the Intercom dashboard, navigate to Contacts > Segments.
3. Create a new Segment with filter: `plan_tier is enterprise`.
4. Use this Segment as an audience for outbound messages or Workflow conditions.

### Segmentation Use Cases

- Target onboarding messages to users where `has_completed_onboarding is false`
- Trigger upgrade prompts for users where `plan_tier is starter` and `account_age_days > 30`
- Route conversations to specialized teams based on `plan_tier`
- Exclude churned users from campaigns using `subscription_status is cancelled`

Segments update in real time as attribute values change. When you call `Intercom('update', { plan_tier: 'pro' })`, the contact moves into or out of Segments immediately.

---

## A/B Testing Pattern

Intercom's A/B testing tools live entirely in the dashboard. The frontend's role is to fire goal events and set audience attributes.

### Frontend Responsibilities

1. Fire conversion goal events when the target action occurs:

```js
// Goal: user upgrades after seeing a message
Intercom('trackEvent', 'upgraded-plan', {
  from_plan: 'starter',
  to_plan: 'pro',
  revenue: { amount: 4900, currency: 'usd' }
});
```

2. Set attributes that define the test audience:

```js
Intercom('update', {
  plan_tier: 'starter',
  account_age_days: 14,
  has_seen_upgrade_prompt: false
});
```

### Dashboard Responsibilities

- Define the A/B test variants (message copy, timing, channel)
- Set the audience using Segments built from custom attributes
- Configure the goal event that measures conversion
- Monitor results in the A/B test report

### What Not to Do

Do not implement A/B test logic in your frontend code (e.g., randomly assigning users to variants and conditionally calling Intercom). Let Intercom handle variant assignment. Your frontend only needs to fire accurate goal events and maintain up-to-date user attributes.

---

## Outbound Messaging Types

All outbound message creation happens in the Intercom dashboard. The frontend enables targeting by keeping user attributes current and firing events that trigger message rules.

| Message Type | Channel | Best For |
|-------------|---------|---------|
| Chat | Messenger | In-app announcements, onboarding nudges |
| Post | Messenger | Long-form announcements, release notes |
| Banner | Top/bottom of page | Urgent notices, trial expiry warnings |
| Tooltip | Specific UI element | Feature discovery, contextual help |
| Email | Email | Re-engagement, drip sequences |
| Push | Mobile push | Mobile app re-engagement |

### Event-Triggered Outbound Pattern

```js
// User activates a feature for the first time
// This event triggers a Workflow that sends a contextual tip
Intercom('trackEvent', 'feature-activated', {
  feature: 'analytics-dashboard'
});
```

In the dashboard, configure a Workflow:
- Trigger: user performs event `feature-activated`
- Condition: `feature is analytics-dashboard`
- Action: send a Chat message with analytics tips

This pattern delivers contextual messages at the exact moment of relevance without hardcoding message logic in your frontend.

---

## Best Practices

### When to Fire Events

Fire events at meaningful, discrete user actions — not on every page load or scroll. Each event should represent a decision or achievement that has business significance.

Good moments to fire events:
- Completing a multi-step flow
- Activating a feature for the first time
- Reaching a usage milestone
- Initiating a high-intent action (requesting a demo, starting a trial)

Avoid:
- Firing events on every page view (use Intercom's built-in page tracking instead)
- Firing the same event multiple times for the same action
- Firing events before the action completes (e.g., before a form submits successfully)

### Event Volume

Keep unique event names under 50. A large number of distinct events makes Workflows harder to manage and event logs harder to read. Consolidate similar actions using metadata:

```js
// Instead of: 'activated-analytics', 'activated-reporting', 'activated-exports'
// Use one event with a feature attribute:
Intercom('trackEvent', 'feature-activated', { feature: 'analytics' });
Intercom('trackEvent', 'feature-activated', { feature: 'reporting' });
Intercom('trackEvent', 'feature-activated', { feature: 'exports' });
```

### Naming Consistency

Establish a naming convention and document it. Inconsistent event names (e.g., `plan-upgraded` vs `upgraded-plan` vs `upgrade_plan`) create duplicate events in Intercom that cannot be merged.

Recommended convention: `past-tense-verb-noun`, lowercase, hyphen-separated.

### Metadata and PII

Include enough metadata to enable segmentation and Workflow conditions. Avoid including personally identifiable information in event names or metadata keys. Phone numbers and email addresses belong in user attributes (set via `boot`/`update`), not in event metadata — unless the event specifically captures that data (e.g., `requested-phone-callback` where the phone number is the point of the event).

### Timing

Fire events after the action succeeds, not before. For async operations, fire the event in the success callback:

```js
async function upgradePlan(planId) {
  const result = await api.upgradePlan(planId);
  if (result.success) {
    Intercom('trackEvent', 'upgraded-plan', {
      from_plan: result.previousPlan,
      to_plan: result.newPlan,
      revenue: { amount: result.amountCents, currency: 'usd' }
    });
  }
}
```

Firing events on failure or before confirmation produces inaccurate data in Intercom and can trigger Workflows prematurely.
