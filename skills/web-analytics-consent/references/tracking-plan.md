# Tracking Plan Design

Sources: PostHog documentation (posthog.com/docs), Amplitude Data Taxonomy Guide (amplitude.com/blog/data-taxonomy-playbook), Segment Analytics Academy (segment.com/academy), Mixpanel Tracking Plan Best Practices (mixpanel.com/blog/tracking-plan), Avo documentation (avo.app/docs), Heap Analytics Engineering Blog, Snowplow Analytics documentation

---

## Why Tracking Plans Matter

Without a tracking plan, analytics data degrades into noise. Teams independently instrument the same user action under different names — `button_click`, `ButtonClicked`, `click_button` — producing three separate events that measure the same thing. Dashboards break when engineers rename events without notifying data consumers. New hires cannot discover what is already tracked, so they add duplicate events. Properties drift: one team sends `user_id` as a string, another as an integer. After 18 months, the event schema is unmaintainable and a full re-instrumentation is the only path forward.

A tracking plan is the contract between product, engineering, and data. It defines what to track, why, and exactly how — before a single line of analytics code is written.

For event naming conventions (Object_Action framework, snake_case rules), see `references/funnels-sessions-heatmaps.md`. For base property conventions (user_id, session_id, platform), see `references/funnels-sessions-heatmaps.md`.

---

## What to Track at Each Stage

Match instrumentation depth to product maturity. Over-tracking at MVP wastes engineering time and creates noise. Under-tracking at Scale leaves growth levers invisible.

### MVP Stage (5-10 events)

Focus exclusively on the critical path: can users reach value, and do they return?

| Event | Trigger | Why It Matters |
|---|---|---|
| `user_signed_up` | Account creation completes | Top of funnel; source attribution |
| `onboarding_completed` | User finishes setup flow | Activation rate; predicts retention |
| `core_action_performed` | Primary value action taken | The "aha moment"; define per product |
| `session_started` | App opened after 24h gap | Retention signal; DAU/WAU/MAU |
| `upgrade_intent_shown` | Paywall or pricing page viewed | Purchase intent before conversion |
| `subscription_started` | Payment succeeds | Revenue; MRR calculation |
| `subscription_cancelled` | Cancellation confirmed | Churn; triggers exit survey |
| `error_encountered` | Unhandled exception or API failure | Quality signal; blocks activation |

Define `core_action_performed` specifically for your product. For a document editor it is `document_created`. For a communication tool it is `message_sent`. For a data pipeline it is `pipeline_run_succeeded`. One event, precisely named.

### Growth Stage (20-40 events)

Once product-market fit is established, instrument the full funnel and feature surface.

**Onboarding funnel** — track each discrete step so you can identify where users drop:

- `onboarding_step_viewed` (with `step_name` property)
- `onboarding_step_completed`
- `onboarding_step_skipped`
- `profile_setup_completed`
- `integration_connected` (with `integration_name`)
- `sample_data_imported`
- `first_invite_sent`

**Feature adoption** — one event per major feature, fired on first meaningful use:

- `feature_discovered` (with `feature_name`, `discovery_source`)
- `feature_activated` (first successful use)
- `feature_used` (subsequent uses; throttle to avoid volume explosion)
- `feature_disabled`

**Collaboration** — `invite_sent` (with `invitee_role`), `invite_accepted`, `content_shared` (with `share_destination`), `comment_added`.

**Billing lifecycle** — `trial_started`, `trial_converted`, `trial_expired`, `plan_upgraded`, `plan_downgraded`, `payment_failed`, `invoice_paid`.

**Engagement** — `notification_received` (with `notification_type`, `channel`), `notification_clicked`, `search_performed` (with `query_length`, `results_count`; never log the query string itself), `export_completed`.

**Error signals** — `api_error_encountered` (with `endpoint`, `status_code`), `validation_error_shown` (with `field_name`), `rate_limit_hit`.

### Scale Stage (50-100+ events)

At scale, instrumentation supports experimentation, performance optimization, and support deflection.

**Experimentation:**

- `experiment_enrolled` (with `experiment_id`, `variant`)
- `experiment_converted`
- `feature_flag_evaluated` (with `flag_key`, `value`) — use sampling; do not fire on every page load

**Performance** — `page_load_slow` (with `lcp_ms`, `connection_type`), `api_latency_high` (with `endpoint`, `p95_ms`), `bundle_load_failed`.

**Micro-interactions** (only when A/B testing UI changes) — `tooltip_viewed`, `modal_dismissed`, `empty_state_cta_clicked`.

**Integrations** — `webhook_delivered` (with `destination`, `status_code`), `api_key_created`, `oauth_app_authorized`, `data_sync_completed` (with `source`, `records_synced`, `duration_ms`).

**Support signals** — `help_article_viewed` (with `article_id`), `support_chat_opened`, `in_app_survey_submitted` (with `survey_id`, `score`).

---

## Tracking Plan Document Format

Maintain the tracking plan as a versioned spreadsheet (Google Sheets, Notion database, or Avo). Every event gets one row. Every property gets a sub-row or a linked property library entry.

### Event Schema Columns

| Column | Type | Description |
|---|---|---|
| Event Name | string | Exact string sent to analytics (e.g., `subscription_started`) |
| Description | string | One sentence: what user action triggers this event |
| Trigger | string | Precise UI or system condition (e.g., "Payment API returns 200") |
| Platform | enum | `web`, `mobile_ios`, `mobile_android`, `server`, `all` |
| Properties | list | Names of all properties sent with this event |
| Owner | string | Team or individual responsible for maintaining this event |
| Status | enum | `planned`, `implemented`, `deprecated`, `removed` |
| Date Added | date | When the event was first instrumented |
| Destinations | list | Which tools receive this event (PostHog, Amplitude, Intercom, etc.) |

### Property Sub-Schema

For each property listed in an event row, document:

| Column | Type | Description |
|---|---|---|
| Property Name | string | Exact key sent (e.g., `plan_name`) |
| Type | enum | `string`, `number`, `boolean`, `array`, `object` |
| Required | boolean | Whether the property must always be present |
| Enum Values | list | If string, the allowed values (e.g., `free`, `pro`, `enterprise`) |
| PII | boolean | Whether this property contains personal data |
| Example Value | any | A realistic sample value |
| Notes | string | Edge cases, deprecation notes, migration instructions |

### Status Lifecycle

```
planned → implemented → deprecated → removed
```

Never delete rows. Mark events as `deprecated` with a deprecation date and migration note. Archive removed events in a separate sheet tab. This preserves the audit trail when debugging historical data.

---

## TypeScript Typed Event Wrapper

Untyped analytics calls — `posthog.capture('some_event', { prop: value })` — allow typos, missing required properties, and wrong value types to reach production silently. A typed wrapper catches these at compile time.

### EventMap Type Definition

Define a map from event name to its required and optional properties:

```typescript
// analytics/events.ts

export interface BaseEventProperties {
  // Cross-reference: base properties (user_id, session_id, etc.)
  // are defined in funnels-sessions-heatmaps.md
}

export interface EventMap {
  user_signed_up: {
    signup_method: 'email' | 'google' | 'github' | 'saml';
    referral_source?: string;
    invite_token?: string;
  };
  onboarding_completed: {
    steps_completed: number;
    steps_skipped: number;
    duration_seconds: number;
    completion_method: 'manual' | 'guided' | 'skipped';
  };
  subscription_started: {
    plan_name: 'free' | 'pro' | 'team' | 'enterprise';
    billing_interval: 'monthly' | 'annual';
    trial_converted: boolean;
    mrr_usd: number;
    coupon_applied?: string;
  };
  subscription_cancelled: {
    plan_name: string;
    cancellation_reason: string;
    days_active: number;
    mrr_lost_usd: number;
  };
  feature_activated: {
    feature_name: string;
    discovery_source: 'onboarding' | 'tooltip' | 'search' | 'direct_nav' | 'email';
  };
  experiment_enrolled: {
    experiment_id: string;
    variant: string;
    enrollment_source: 'page_load' | 'api' | 'manual';
  };
}
```

### Typed Track Function

```typescript
// analytics/track.ts
import posthog from 'posthog-js';
import type { EventMap } from './events';

export function track<E extends keyof EventMap>(
  event: E,
  properties: EventMap[E]
): void {
  if (typeof window === 'undefined') return;

  posthog.capture(event, properties);
}
```

Usage — TypeScript enforces the correct event name and all required properties:

```typescript
// Correct — compiles
track('subscription_started', {
  plan_name: 'pro',
  billing_interval: 'annual',
  trial_converted: true,
  mrr_usd: 79,
});

// Error: Argument of type '"subscriptionStarted"' is not assignable
track('subscriptionStarted', { ... });

// Error: Property 'billing_interval' is missing
track('subscription_started', {
  plan_name: 'pro',
  trial_converted: true,
  mrr_usd: 79,
});
```

### Server-Side Wrapper

For server events (payment webhooks, background jobs), use the same EventMap with the Node.js client:

```typescript
// analytics/server-track.ts
import { PostHog } from 'posthog-node';
import type { EventMap } from './events';

const client = new PostHog(process.env.POSTHOG_KEY!, {
  host: process.env.POSTHOG_HOST,
});

export function serverTrack<E extends keyof EventMap>(
  distinctId: string,
  event: E,
  properties: EventMap[E]
): void {
  client.capture({ distinctId, event, properties });
}

// Flush before serverless function exits
export async function flushAnalytics(): Promise<void> {
  await client.shutdown();
}
```

---

## Event Governance

Instrumentation without governance produces the same chaos as no tracking plan. Governance is the process that keeps the plan accurate as the product evolves.

### CI Linting for Event Names

Add a CI step that validates every `track()` call against the EventMap. Use `ts-morph` to parse the AST and reject unknown event names:

```typescript
// scripts/lint-analytics.ts — run in CI: ts-node scripts/lint-analytics.ts
import { Project, SyntaxKind } from 'ts-morph';
import { EventMap } from '../src/analytics/events';

const validEvents = new Set(Object.keys({} as EventMap));
const project = new Project({ tsConfigFilePath: 'tsconfig.json' });
const errors: string[] = [];

for (const file of project.getSourceFiles('src/**/*.{ts,tsx}')) {
  for (const call of file.getDescendantsOfKind(SyntaxKind.CallExpression)) {
    const expr = call.getExpression().getText();
    if (expr !== 'track' && expr !== 'serverTrack') continue;
    const eventName = call.getArguments()[0]?.getText().replace(/['"]/g, '');
    if (eventName && !validEvents.has(eventName)) {
      errors.push(`${file.getFilePath()}:${call.getStartLineNumber()} — unknown event "${eventName}"`);
    }
  }
}

if (errors.length > 0) { console.error('Analytics lint errors:\n' + errors.join('\n')); process.exit(1); }
```

### Code Review Checklist for Analytics PRs

Include in pull request template when `analytics/events.ts` is modified:

- New event added to tracking plan spreadsheet with all columns filled
- Event has at least two meaningful properties beyond base properties
- No PII in any property value (no email, name, IP address)
- Destinations column updated — does this event need to reach Intercom or just PostHog?
- Owner assigned
- If replacing an existing event, old event marked `deprecated` with migration date

### Deprecation Workflow

Follow this sequence to remove an event without breaking dashboards:

1. **Mark deprecated** — Set status to `deprecated` in tracking plan. Add deprecation date and reason. Add a code comment above the `track()` call.
2. **Notify data consumers** — Ping the team in Slack. List every dashboard, chart, and cohort that uses this event. Give a 30-day migration window.
3. **Migrate dashboards** — Update all charts to use the replacement event. Verify data continuity by running both events in parallel for one week.
4. **Remove from code** — Delete the `track()` call and remove the event from `EventMap`. The TypeScript compiler will surface any remaining usages.
5. **Archive in tracking plan** — Move the row to the `Archived` sheet tab. Do not delete.

### Avo as Dedicated Tooling

For teams with 5+ engineers contributing analytics, consider Avo (avo.app). Avo generates type-safe tracking functions from a visual tracking plan, enforces schemas in CI, and provides a branch-based review workflow for analytics changes. It replaces the manual EventMap approach above with a generated SDK. The tradeoff is vendor dependency and cost; the benefit is a single source of truth that non-engineers can edit.

---

## Group Analytics for B2B

B2C analytics centers on individual users. B2B analytics requires a second dimension: the company (workspace, organization, account). A user's behavior is often less important than their company's behavior — which plan is the company on, how many seats are active, is the company expanding or contracting?

### Identifying Groups in PostHog

```typescript
// When a user logs in or switches workspace
posthog.group('company', workspace.id, {
  name: workspace.name,
  plan: workspace.plan,                    // 'free' | 'pro' | 'enterprise'
  mrr_usd: workspace.mrr,
  seat_count: workspace.activeUserCount,
  industry: workspace.industry,
  company_size: workspace.employeeRange,   // '1-10' | '11-50' | '51-200' | '201-1000' | '1000+'
  created_at: workspace.createdAt,
  trial_ends_at: workspace.trialEndsAt,
  health_score: workspace.healthScore,
});
```

All subsequent `posthog.capture()` calls on this client will automatically attach the group context. Events become queryable at both the user level and the company level.

### Group Properties to Track

| Property | Type | Why |
|---|---|---|
| `plan` | enum | Segment by tier; measure plan-level retention |
| `mrr_usd` | number | Weight cohorts by revenue; identify high-value accounts |
| `seat_count` | number | Expansion signal; track seat growth over time |
| `active_seat_count` | number | Engagement; seats paid vs seats used |
| `industry` | string | Vertical segmentation; product-market fit by industry |
| `company_size` | enum | ICP fit; enterprise vs SMB behavior differences |
| `created_at` | ISO date | Cohort analysis by signup month |
| `health_score` | number | Composite retention signal; trigger CSM alerts |
| `integrations_connected` | number | Stickiness; integrations correlate with retention |
| `trial_ends_at` | ISO date | Conversion urgency; trigger upgrade campaigns |

### Groups vs Cohorts

A **group** is a persistent entity (company) that events associate with. A **cohort** is a dynamic filter at query time (e.g., "Pro plan companies from Q1 with no integrations"). Groups are the data structure; cohorts are the query.

Update group properties server-side when they change, not only on login:

```typescript
// In your billing webhook handler
async function handleSubscriptionUpgraded(event: StripeEvent) {
  const workspace = await db.workspace.findById(event.metadata.workspaceId);

  // Update PostHog group properties
  serverClient.groupIdentify({
    groupType: 'company',
    groupKey: workspace.id,
    properties: {
      plan: workspace.plan,
      mrr_usd: workspace.mrr,
    },
  });
}
```

---

## Identity Resolution

Analytics data is only as useful as its identity graph. Stitching anonymous sessions to identified users — and resolving the same user across devices — determines whether your funnel analysis reflects reality.

### Anonymous to Identified Stitching

PostHog assigns a random `distinct_id` to every anonymous visitor. When the user signs up or logs in, call `identify()` to merge the anonymous session history with the identified profile:

```typescript
// On successful login or signup
posthog.identify(
  user.id,           // Your internal user ID — never use email
  {
    email: user.email,
    name: user.name,
    created_at: user.createdAt,
    plan: user.plan,
  }
);
```

PostHog merges the anonymous `distinct_id` history into the identified profile. All events captured before `identify()` — including the signup funnel — are attributed to the correct user.

### Cross-Device Tracking

When a user logs in on a second device, call `identify()` with the same `user.id`. PostHog resolves both device sessions to the same person. Do not call `posthog.reset()` on login — only call it on logout to start a fresh anonymous session.

```typescript
// On logout
posthog.reset();
// A new anonymous distinct_id is assigned for the next visitor on this device
```

### Cost Optimization with person_profiles

PostHog charges per identified user profile. For high-traffic marketing pages where most visitors never sign up, use `person_profiles: 'identified_only'` to avoid creating profiles for anonymous visitors:

```typescript
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  person_profiles: 'identified_only',
  // Anonymous events are still captured but no profile is created
  // until posthog.identify() is called
});
```

This reduces costs significantly for B2C products with large anonymous traffic volumes. The tradeoff is that pre-signup funnel analysis requires joining anonymous events to identified profiles after the fact, which PostHog handles automatically when `identify()` is called.

### Never Use Email as distinct_id

Using email as the `distinct_id` creates three problems: it exposes PII in event logs, it breaks when users change their email address, and it prevents merging accounts if a user signs up with a different email on a second device. Always use your internal immutable user ID (UUID or integer primary key).

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| PII in event properties | GDPR violation; legal liability; cannot delete from analytics warehouse | Audit all string properties; hash or omit email, name, IP; use user IDs only |
| Events with no properties | Unqueryable; you know the event happened but not to whom or in what context | Every event needs at minimum the base properties plus 2 domain-specific properties |
| Inconsistent naming across platforms | Web fires `subscription_started`, mobile fires `SubscriptionStarted`; funnels break | Enforce naming in EventMap; share the type definition across web and mobile codebases |
| Tracking UI state instead of business outcomes | `modal_opened` tells you nothing; `upgrade_intent_shown` tells you conversion intent | Ask "what business question does this answer?" before adding any event |
| Dynamic values in event names | `product_123_viewed`, `product_456_viewed` creates unbounded event cardinality; dashboards explode | Use `product_viewed` with a `product_id` property |
| Double-firing from frontend and backend | Payment events fired by both Stripe webhook handler and checkout UI; revenue appears doubled | Designate one authoritative source per event; document in tracking plan |
| Not filtering internal employees | Your own team's usage inflates activation and retention metrics | Add an `is_employee` person property; exclude from all product metrics dashboards |
| Tracking the same metric multiple ways | `subscription_started` and `payment_succeeded` both measure new MRR; reports disagree | One canonical event per business metric; document which event is the source of truth |
| Missing timestamps on server events | Server events arrive out of order; funnels show impossible sequences | Always pass `timestamp` explicitly on server-side `capture()` calls |
| No sampling on high-volume events | `scroll_depth_changed` fires 50 times per page; 10M events/month from one event | Sample high-frequency events at 10% or use session recording instead |
