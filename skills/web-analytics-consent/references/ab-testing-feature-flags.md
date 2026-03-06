# A/B Testing and Feature Flags

Sources: PostHog documentation (posthog.com/docs/experiments), PostHog React SDK docs (posthog.com/docs/libraries/react), PostHog Node.js SDK docs (posthog.com/docs/libraries/node), Statsig documentation (docs.statsig.com), LaunchDarkly documentation (docs.launchdarkly.com), GrowthBook documentation (docs.growthbook.io), Kohavi et al. "Trustworthy Online Controlled Experiments" (2020), Fabijan et al. "The Evolution of Continuous Experimentation in Software Product Development" (2017).

---

## Feature Flag Fundamentals

Feature flags decouple deployment from release. Ship code to production, control activation separately. This enables gradual rollouts, instant kill switches, and controlled experiments without redeployment.

### Flag Types

| Type | Use Case | Example Value | PostHog API |
|------|----------|---------------|-------------|
| Boolean | Simple on/off gating | `true` / `false` | `isFeatureEnabled('flag-key')` |
| Multivariate | A/B/n experiments | `'control'` / `'test'` / `'test-2'` | `getFeatureFlag('flag-key')` |
| Remote config | Dynamic configuration | `{ price: 29, label: 'Pro' }` | `getFeatureFlagPayload('flag-key')` |

### Core Client API

```typescript
// Boolean check — returns true/false/undefined
posthog.isFeatureEnabled('new-checkout')

// Variant key — returns string variant name or boolean
posthog.getFeatureFlag('pricing-experiment')
// => 'control' | 'variant-a' | 'variant-b' | undefined

// JSON payload — returns parsed object or undefined
posthog.getFeatureFlagPayload('pricing-config')
// => { monthlyPrice: 29, annualPrice: 249 } | undefined

// React to flag changes (fires on load and on identity change)
posthog.onFeatureFlags(() => {
  const variant = posthog.getFeatureFlag('pricing-experiment')
  // update UI state
})
```

`undefined` means flags have not yet loaded. Always handle this state to prevent flicker — show a skeleton or defer rendering until flags resolve.

### Percentage Rollouts

Rollout percentage is hashed against the distinct ID, so the same user always gets the same variant. Increase rollout percentage incrementally: 5% → 20% → 50% → 100%. Never decrease percentage mid-experiment — this changes which users are included and corrupts data.

### Targeting Rules

Apply targeting before percentage rollout. Rules evaluate in order; first match wins.

| Targeting Dimension | Example Condition | Notes |
|--------------------|-------------------|-------|
| User property | `plan = 'pro'` | Set via `posthog.identify()` |
| Cohort | `cohort_id = 42` | Pre-built cohort in PostHog UI |
| Geography | `country = 'US'` | Requires GeoIP enrichment |
| Group | `organization.size > 50` | Requires group analytics |
| Early access | `$feature_enrollment/flag` | Self-serve opt-in |

---

## PostHog Experiments

Experiments in PostHog are feature flags with statistical analysis layered on top. Every experiment creates a backing feature flag automatically. Participants are assigned to variants when the flag is first evaluated; assignment is sticky.

### Setup Flow

1. Create experiment in PostHog UI — name, hypothesis, variants.
2. Define primary metric (conversion event) and secondary metrics.
3. Use the running time calculator — enter baseline conversion rate and minimum detectable effect (MDE). PostHog calculates required sample size per variant.
4. Set a predetermined end date before launching. Do not extend based on results.
5. Launch — PostHog begins assigning users and collecting data.
6. Read results only after reaching significance or the end date.

### Statistical Methods

| Aspect | Bayesian (PostHog default) | Frequentist |
|--------|---------------------------|-------------|
| Output | Probability variant is best | p-value, confidence interval |
| Interpretation | "87% chance test beats control" | "p < 0.05, reject null" |
| Early stopping | Safer — credible intervals widen | Inflates false positive rate |
| Sample size | Flexible | Fixed upfront |
| Best for | Product experiments, fast iteration | Regulatory, clinical contexts |

PostHog uses Bayesian statistics by default. The dashboard shows probability of being best and expected improvement with credible intervals.

### When to Call an Experiment

Call a winner or stop the experiment when ALL of the following are true:

- Probability of being best exceeds 95% (or falls below 5% — declare loser).
- Each variant has at least 100 conversions (not just exposures).
- The predetermined duration has elapsed.
- No significant external events (launches, holidays) contaminated the period.

Do not call experiments early based on promising early results. The peeking problem (see Statistical Pitfalls) guarantees inflated false positive rates.

---

## React Integration

### Pattern 1: Boolean Flag with useFeatureFlagEnabled

```typescript
// undefined = flags loading, false = disabled, true = enabled
const isNewCheckout = useFeatureFlagEnabled('new-checkout-flow')
if (isNewCheckout === undefined) return <CheckoutButtonSkeleton />
if (!isNewCheckout) return <LegacyCheckoutButton />
return <NewCheckoutButton />
```

### Pattern 2: Variant Key with useFeatureFlagVariantKey

```typescript
const variant = useFeatureFlagVariantKey('pricing-experiment')
if (variant === undefined) return <PricingSkeleton />
return (
  <div>
    {variant === 'control' && <OriginalPricing />}
    {variant === 'annual-emphasis' && <AnnualFirstPricing />}
    {variant === 'monthly-emphasis' && <MonthlyFirstPricing />}
  </div>
)
```

### Pattern 3: JSON Payload with useFeatureFlagPayload

```typescript
interface PricingConfig { monthlyPrice: number; annualPrice: number }
const config = useFeatureFlagPayload('pricing-config') as PricingConfig | undefined
if (!config) return <PricingCardSkeleton />
return <div><span>${config.monthlyPrice}/mo</span><span>${config.annualPrice}/yr</span></div>
```

Use remote config payloads to change copy, prices, and layout without code deploys. Keep payloads under 10KB — they are loaded on every page.

### Pattern 4: Declarative PostHogFeature Component

```typescript
// Boolean flag — match={true} shows children when flag is enabled
<PostHogFeature flag="new-dashboard" match={true} fallback={<LegacyDashboard />}>
  <NewDashboard />
</PostHogFeature>

// Multivariate — match on variant string
<PostHogFeature flag="hero-experiment" match="variant-b" fallback={<OriginalHero />}>
  <NewHero />
</PostHogFeature>
```

`PostHogFeature` automatically captures a `$feature_view` event when the matched variant renders. Use `fallback` for the control experience.

---

## Next.js Patterns

### Pattern 1: Server Component Flag Evaluation

Evaluate flags server-side to avoid client-side loading states entirely. Requires `posthog-node`.

```typescript
// app/pricing/page.tsx
import { PostHog } from 'posthog-node'
import { cookies } from 'next/headers'

async function PricingPage() {
  const client = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!)
  const distinctId = cookies().get('ph_distinct_id')?.value ?? 'anonymous'
  const flags = await client.getAllFlags(distinctId)
  await client.shutdown()

  const variant = flags['pricing-experiment'] as string | undefined
  return variant === 'variant-b' ? <NewPricing /> : <OriginalPricing />
}
```

Cache the PostHog client instance across requests in production — do not instantiate per request.

### Pattern 2: Bootstrapping Flags to Prevent Client Flicker

Server evaluates flags, passes them to the client via bootstrap. Client uses bootstrapped values immediately without a network round-trip.

```typescript
// app/layout.tsx (Server Component)
async function RootLayout({ children }: { children: React.ReactNode }) {
  const client = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!)
  const distinctId = getDistinctIdFromCookies()
  const flags = await client.getAllFlags(distinctId)
  await client.shutdown()

  return (
    <html><body>
      <PHProvider bootstrap={{ distinctId, featureFlags: flags }}>
        {children}
      </PHProvider>
    </body></html>
  )
}

// In PHProvider (client component), pass to posthog.init:
// bootstrap: { distinctId: props.bootstrap.distinctId, featureFlags: props.bootstrap.featureFlags }
// See posthog-integration.md for full PHProvider setup.
```

Bootstrapping eliminates the loading flash. Flags are available synchronously on first render.

### Pattern 3: Middleware-Based Flag Evaluation

Rewrite entire pages at the edge based on flag values. Useful for full-page A/B tests.

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { PostHog } from 'posthog-node'

export async function middleware(request: NextRequest) {
  const client = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!)
  const distinctId = request.cookies.get('ph_distinct_id')?.value ?? 'anonymous'
  const variant = await client.getFeatureFlag('landing-page-experiment', distinctId)
  await client.shutdown()

  if (variant === 'variant-b') {
    return NextResponse.rewrite(new URL('/landing-b', request.url))
  }
  return NextResponse.next()
}

export const config = { matcher: ['/'] }
```

Middleware evaluation adds latency. Cache flag decisions in a cookie after first evaluation to avoid per-request PostHog calls.

---

## Common Experiment Types

### UI Experiment — Button Copy

```typescript
const variant = useFeatureFlagVariantKey('cta-experiment')
const label = variant === 'action-oriented' ? 'Start Free Trial' : 'Get Started'
return <button onClick={handleCTA}>{label}</button>
```

Track `cta_clicked` with `{ variant }` property. Primary metric: click-through rate.

### Pricing Experiment — Payload-Driven

```typescript
const config = useFeatureFlagPayload('pricing-test') as { price: number; label: string } | undefined
// Render config.price and config.label — no code change needed for new variants
```

Payload-driven experiments let non-engineers create new variants. Primary metric: plan conversion rate.

### Funnel Experiment — Onboarding Steps

Gate entire onboarding flows behind a flag. Assign on first visit to `/onboarding`. Track `onboarding_completed` as primary metric, `onboarding_step_N_completed` as secondary metrics.

### Feature Gating — Gradual Rollout with Kill Switch

```typescript
const isEnabled = useFeatureFlagEnabled('new-search-engine')
// Roll out to 5% → 25% → 100% over two weeks
// If error rate spikes, disable flag instantly — no deploy needed
```

---

## Statistical Pitfalls

### Peeking Problem

Checking results before the predetermined end date and stopping when p < 0.05 inflates the false positive rate to 26% or higher (Kohavi et al.). Commit to a sample size and duration before launch. PostHog's Bayesian approach is more robust to early stopping but still requires discipline.

### Sample Ratio Mismatch (SRM)

SRM occurs when variant assignment ratios deviate significantly from the intended split (e.g., 60/40 instead of 50/50). Causes: redirect-based experiments losing users, bot traffic, caching serving one variant more. PostHog automatically detects SRM and flags affected experiments. Investigate before reading results.

### Multiple Comparisons

Testing 10 metrics at 95% confidence yields an expected 0.5 false positives by chance. Designate one primary metric before launch. Treat secondary metrics as directional signals, not decision criteria. Apply Bonferroni correction if you must test multiple primary metrics.

### Novelty Effect

Users interact with new UI differently simply because it is new. Novelty effects inflate early results for the test variant. Run experiments for at least two weeks to let novelty decay. Segment results by new vs. returning users to detect novelty contamination.

### Survivorship Bias

Analyzing only users who completed a funnel step ignores users who dropped off. If the test variant reduces drop-off, the surviving population differs between variants. Measure from the point of assignment, not from a downstream funnel step.

---

## Experimentation Culture

### Hypothesis Format

```
We believe [changing X to Y]
will [increase/decrease metric Z]
because [causal mechanism or user insight].

Success criteria: Z increases by at least [MDE]% with 95% confidence
over [N] weeks with [N] users per variant.
```

Write the hypothesis before building. If you cannot articulate the causal mechanism, the experiment is not ready.

### Experiment Documentation Template

```markdown
## Experiment: [Name]

**Hypothesis:** We believe [X] will [Y] because [Z].
**Primary metric:** [event name, conversion definition]
**Secondary metrics:** [list]
**Variants:** control (baseline), [variant names]
**Rollout:** [%] of [segment]
**Duration:** [start date] – [end date]
**MDE:** [%] relative change
**Required sample:** [N] per variant

## Results
**Winner:** [variant or no significant difference]
**Primary metric:** [observed change, credible interval]
**Decision:** [ship / revert / iterate]
**Learnings:** [what we learned about users]
```

### Launch Checklist

- [ ] Hypothesis written with causal mechanism
- [ ] Primary metric defined and tracking verified
- [ ] Sample size calculated with running time calculator
- [ ] End date set and calendar reminder added
- [ ] Variants reviewed by a second engineer
- [ ] Flag key follows naming convention (`[team]-[description]-[type]`)
- [ ] Rollout starts at 5% or less for risky changes
- [ ] Kill switch tested — disabling flag reverts to control
- [ ] Monitoring alert set for error rate spike
- [ ] Experiment documented in team wiki

### Kill Criteria

| Signal | Threshold | Action |
|--------|-----------|--------|
| Error rate increase | > 2x baseline | Disable flag, investigate |
| Revenue per user drop | > 5% in test variant | Disable flag, investigate |
| Crash rate increase | Any statistically significant increase | Disable flag immediately |
| SRM detected | PostHog flags it | Pause, investigate assignment |
| P99 latency increase | > 200ms | Disable flag, optimize |

---

## Feature Flag Lifecycle

### Temporary vs Permanent Flags

| Type | Purpose | Lifespan | Example |
|------|---------|----------|---------|
| Experiment flag | A/B test, gradual rollout | Days to weeks | `checkout-redesign-exp` |
| Release flag | Safe deployment, kill switch | Days to months | `new-search-engine` |
| Entitlement flag | Feature gating by plan | Permanent | `advanced-analytics` |
| Ops flag | Circuit breaker, maintenance | Permanent | `disable-email-sending` |

### Flag Debt and Cleanup

A flag is stale when: the experiment concluded more than 30 days ago, the feature shipped to 100% more than 60 days ago, or no code references the flag key.

Cleanup process: search codebase for flag key, remove conditional branches, delete flag in PostHog, update tests. Assign flag ownership to the creating team. Review stale flags in quarterly tech debt sessions.

Knight Capital lost $440M in 45 minutes in 2012 because a stale feature flag activated dead code in production — flag hygiene is a safety issue, not just housekeeping.

---

## Platform Comparison

| Platform | Free Tier | Flags | Experiments | Self-Host |
|----------|-----------|-------|-------------|-----------|
| PostHog | 1M events/mo | Unlimited | Unlimited | Yes (open source) |
| Statsig | 2M events/mo | Unlimited | Unlimited | No |
| LaunchDarkly | No free tier | — | — | No |
| GrowthBook | Free (self-host) | Unlimited | Unlimited | Yes (primary model) |
| Unleash | Free (self-host) | Unlimited | Limited | Yes (primary model) |
| Optimizely | No free tier | — | — | No |

**PostHog** — analytics, session replay, and flags in one platform; best for early-stage products wanting unified data.
**Statsig** — enterprise-grade experimentation with CUPED variance reduction; strong free tier for high-volume products.
**LaunchDarkly** — enterprise compliance (SOC 2, HIPAA), audit logs, dedicated support; justified for regulated industries.
**GrowthBook** — connects to existing data warehouse (BigQuery, Snowflake, Redshift); best for data-mature teams.
**Unleash** — self-hosted flags with no vendor dependency; requires infrastructure to manage.

---

## Quick Reference Card

### Client-Side API

```typescript
posthog.isFeatureEnabled('flag-key')           // boolean | undefined
posthog.getFeatureFlag('flag-key')             // string | boolean | undefined
posthog.getFeatureFlagPayload('flag-key')      // JsonType | undefined
posthog.onFeatureFlags(callback)               // fires on load + identity change
posthog.reloadFeatureFlags()                   // force refresh
```

### React Hooks

```typescript
useFeatureFlagEnabled('flag-key')              // boolean | undefined
useFeatureFlagVariantKey('flag-key')           // string | boolean | undefined
useFeatureFlagPayload('flag-key')              // JsonType | undefined
```

### React Component

```typescript
<PostHogFeature flag="flag-key" match="variant" fallback={<Control />}>
  <Variant />
</PostHogFeature>
```

### Server-Side API (posthog-node)

```typescript
const client = new PostHog(key)
await client.isFeatureEnabled('flag-key', distinctId)
await client.getFeatureFlag('flag-key', distinctId)
await client.getAllFlags(distinctId)
await client.shutdown()
```

### Bootstrapping Pattern

```typescript
// Server: const flags = await client.getAllFlags(distinctId)
// Client init: posthog.init(key, { bootstrap: { distinctId, featureFlags: flags } })
// Result: flags available synchronously, no loading flash
```
