# Funnels, Session Recordings, and Heatmaps

Sources: PostHog documentation (posthog.com/docs), Microsoft Clarity documentation (clarity.microsoft.com), Google Analytics 4 documentation (support.google.com/analytics), Plausible Analytics documentation (plausible.io/docs), Mixpanel Event Naming Guide (mixpanel.com/blog/event-naming-best-practices), Amplitude Data Taxonomy Guide (amplitude.com/blog/data-taxonomy), IAPP Privacy Tech Vendor Report 2024, Web Analytics Association Standards 2023.

---

## Event Naming Taxonomy

Consistent event naming is the foundation of reliable funnel analysis. Inconsistent names produce broken funnels, duplicate metrics, and dashboards that contradict each other. Establish a taxonomy before instrumentation begins and enforce it through code review.

### Object-Action Framework

Name every event as `object_action` in snake_case with a past-tense verb. The object is the noun (what was acted on), the action is what happened. This produces names that read as completed facts, which matches how analytics tools store and query them.

Structure: `{object}_{action}` or `{context}_{object}_{action}` for disambiguation.

Rules:
- Use snake_case throughout. Never camelCase, PascalCase, or kebab-case.
- Use past-tense verbs: `submitted`, `clicked`, `viewed`, `completed`, `failed`.
- Put the noun first so events sort together in autocomplete and dashboards.
- Keep names under 40 characters. Longer names indicate the event is too specific.
- Never embed property values in the event name. Use properties for that.

### Event Naming Examples

| Bad Name | Problem | Good Name |
|---|---|---|
| `click` | No object, no context | `signup_button_clicked` |
| `formSubmit` | camelCase, present tense | `signup_form_submitted` |
| `user_signed_up_with_google` | Value embedded in name | `signup_completed` + `{method: "google"}` |
| `pageView` | camelCase | `page_viewed` |
| `addToCart` | camelCase, present tense | `product_added_to_cart` |
| `ERROR` | Uppercase, no context | `payment_failed` |
| `step1_completed` | Brittle, breaks on reorder | `onboarding_profile_completed` |
| `btn_click_header_nav_logo` | Too granular, no value | `logo_clicked` |
| `purchase` | Ambiguous (initiated or completed?) | `order_completed` |
| `video_play_button_clicked_homepage` | Context in name, not property | `video_played` + `{location: "homepage"}` |

### Property Conventions

Attach context as properties, not as name variants. Every event should carry a consistent set of base properties automatically (user ID, session ID, timestamp, URL, referrer). Add domain-specific properties per event type.

Standard base properties (set once in your analytics wrapper):
- `user_id` — authenticated user identifier, null for anonymous
- `session_id` — current session identifier
- `page_url` — full URL at time of event
- `page_path` — pathname only, for grouping
- `referrer` — document.referrer at session start

Event-specific properties follow the same snake_case convention: `product_id`, `plan_name`, `error_code`, `step_number`.

### Taxonomy Governance

Maintain a single source-of-truth event dictionary in your repository (a JSON or YAML file listing every event name, its properties, and its owner). Run a linter in CI that rejects events not in the dictionary. This prevents the taxonomy from drifting as the team grows.

---

## Funnel Analysis

Funnels measure the percentage of users who complete a sequence of steps. Use funnels to identify where users drop off in signup flows, checkout sequences, onboarding, and feature adoption paths.

### PostHog Funnels

PostHog funnels support three step-order modes:

**Sequential (default):** Users must complete steps in the defined order, but other events may occur between steps. Use this for most funnels — it reflects real user behavior where users navigate away and return.

**Strict sequential:** Users must complete steps in exact order with no other events in between. Use this only when intermediate events indicate abandonment, such as a payment flow where any navigation away means failure.

**Any order:** Users must complete all steps but in any sequence. Use this for feature adoption funnels where the order of discovery does not matter.

Configure the mode in the funnel insight settings panel under "Step order."

**Exclusion steps:** Add an exclusion step to filter out users who performed a specific action between two funnel steps. For example, exclude users who visited the pricing page between signup and activation — this isolates users who converted without price hesitation. Exclusion steps are available in sequential and strict sequential modes.

**Conversion window:** Set the maximum time allowed between the first and last step. Default is 14 days. Shorten this for high-intent flows (checkout: 1 hour) and lengthen it for long sales cycles (enterprise trial: 90 days).

**Funnel correlation analysis:** After building a funnel, open the "Correlation analysis" tab. PostHog automatically identifies event properties and person properties that are statistically correlated with higher or lower conversion. This surfaces non-obvious signals — for example, that users who set a profile photo in step 2 convert at 3x the rate of those who skip it. Use correlation results to prioritize product changes, not as causal proof.

**Breakdown:** Split funnel results by a property (browser, plan, country, cohort) to compare conversion rates across segments. Breakdowns reveal whether a drop-off is universal or concentrated in a specific segment.

### GA4 Funnels

GA4 funnels live in the Explorations section (not standard reports). Create a Funnel Exploration from the Explore tab.

**Open funnels:** Users can enter the funnel at any step. A user who completes step 3 without completing steps 1 and 2 still appears in step 3. Use open funnels when users have multiple entry paths to a feature.

**Closed funnels:** Users must complete step 1 to be counted in subsequent steps. This is the standard funnel model. Use closed funnels for linear flows like checkout or signup.

**Step types:** Each step can be a page view (user visited a specific page) or an event (user triggered a specific event). Mix both types in a single funnel.

**Elapsed time:** GA4 shows the median time between each step pair. Use this to identify steps where users stall — a long median time between steps 2 and 3 suggests friction or confusion at step 2.

**Segment comparison:** Apply up to four segments to a funnel exploration to compare conversion rates across user groups. Explorations are private by default — share them explicitly with teammates via the share button.

**Limitations:** GA4 funnels are limited to 10 steps. Funnel Explorations expire after 60 days of inactivity. GA4 applies sampling to Explorations when the dataset exceeds thresholds — check the sampling indicator in the top-right of the exploration. Sampled results are unreliable for small segments.

### Plausible Funnels

Plausible funnels are available on paid plans. Configure them in the Goals section of your site settings.

**Step types:** Each step is either a page visit (URL match) or a custom event. Combine both types in a single funnel.

**Step limits:** Funnels support 2 to 8 steps. For longer flows, split into multiple funnels with overlapping steps.

**Aggregate only:** Plausible funnels show aggregate conversion rates per step. There is no user-level drill-down — you cannot identify which specific users dropped off or replay their sessions from a funnel. This is by design: Plausible's privacy model does not track individual users.

**URL matching:** Use exact URLs or wildcard patterns (e.g., `/checkout/*`) for page-visit steps. Wildcard matching aggregates all matching paths into a single step.

**Use case fit:** Plausible funnels are appropriate for marketing site flows (landing page to signup) and simple product flows where aggregate rates are sufficient. For user-level investigation, pair Plausible with PostHog or Clarity.

---

## Session Recordings

Session recordings capture a video-like replay of individual user sessions. Use recordings to investigate specific drop-off points identified in funnel analysis, reproduce reported bugs, and understand how users interact with new features.

### PostHog Session Recordings

Initialize PostHog with recording enabled:

```javascript
posthog.init('YOUR_KEY', {
  session_recording: {
    maskAllInputs: true,
    maskTextSelector: null,
    recordCrossOriginIframes: false,
  },
  disable_session_recording: false,
})
```

**Input masking:** `maskAllInputs: true` is the default and masks all `<input>`, `<textarea>`, and `<select>` values before they leave the browser. Never disable this without legal review. To mask all text on the page (for highly sensitive UIs), set `maskTextSelector: "*"` — this replaces all text nodes with asterisks.

**Element-level masking:** Add the CSS class `ph-no-capture` to any element to exclude it from recordings entirely. The element's position and size are still captured, but its content is replaced with a placeholder block. Use this for elements that display sensitive data that `maskAllInputs` does not cover (e.g., a `<div>` showing a credit card number).

**Remote masking configuration (March 2025+):** PostHog supports configuring masking rules from the dashboard without a code deploy. Navigate to Project Settings > Session Replay > Masking to add CSS selectors that are applied server-side. Use this to respond quickly to privacy incidents.

**Sampling strategies:**

Use sampling to control recording volume and cost. PostHog supports four sampling mechanisms — combine them:

1. **Sample rate:** Set `sampleRate` between 0 and 1 in the SDK config. A value of 0.2 records 20% of sessions randomly. Apply this as a baseline to cap volume.

2. **URL triggers:** In the PostHog dashboard under Session Replay settings, configure URL patterns that trigger recording regardless of sample rate. Use this to always record sessions on high-value pages (checkout, onboarding) while sampling everything else.

3. **Event triggers:** Configure specific events that start a recording when fired. For example, trigger recording when `payment_failed` fires to capture every failure session without recording all sessions.

4. **Exception triggers:** Enable automatic recording when a JavaScript exception is captured. This ensures you have a replay for every error report. Requires the PostHog exception autocapture to be enabled.

**Minimum duration filter:** Set a minimum session duration (in seconds) to exclude very short sessions from storage. Sessions under 2 seconds are typically bots or accidental page loads. Configure this in Project Settings > Session Replay > Minimum duration.

**Linked funnels:** From a funnel drop-off step in PostHog, click "Watch recordings" to open session replays filtered to users who dropped off at that step. This is the primary workflow for funnel investigation.

### Microsoft Clarity Session Recordings

Clarity provides unlimited session recordings at no cost. There is no sampling limit — every session is recorded by default.

**Automatic behavior detection:** Clarity automatically tags sessions with:

- **Rage clicks:** User clicked the same element three or more times in rapid succession, indicating frustration with an unresponsive element.
- **Dead clicks:** User clicked an element that produced no visible response, indicating a broken interaction or misleading affordance.
- **Quick back:** User navigated to a page and immediately returned to the previous page, indicating the page did not meet their expectation.

Filter the recordings list by these tags to surface problematic sessions without manual review.

**AI Copilot:** Clarity's AI Copilot summarizes batches of up to 250 recordings into a natural-language report describing common user behaviors, friction points, and patterns. Use this to get a rapid overview before watching individual recordings. Access it from the Recordings tab via the "Summarize" button.

**Data retention:** Clarity retains recordings for 13 months.

**Privacy controls:** Clarity masks input fields by default. Configure additional masking rules in the Clarity dashboard under Masking. Clarity does not support element-level masking via CSS classes — use the dashboard masking rules instead.

**Integration with PostHog:** If you use both tools, link Clarity session IDs to PostHog events by passing the Clarity session URL as a PostHog event property. This lets you jump from a PostHog funnel drop-off directly to the Clarity recording.

---

## Heatmaps

Heatmaps aggregate interaction data across many sessions into a visual overlay on a page screenshot. Use heatmaps to understand where users click, how far they scroll, and which areas attract attention — without watching individual recordings.

### Heatmap Types

**Click heatmaps:** Show the density of click events across the page. High-density areas indicate elements users interact with most. Low-density areas on interactive elements indicate elements users ignore. Use click heatmaps to validate that primary CTAs receive attention and to identify unexpected click targets.

**Scroll heatmaps:** Show what percentage of sessions reached each vertical position on the page. The fold line (where most users stop scrolling) is visible as a sharp drop in the gradient. Use scroll heatmaps to determine how much of a page users actually see and to decide where to place critical content.

**Area heatmaps (move maps):** Show where users move their mouse cursor. Mouse movement correlates loosely with visual attention — users tend to move the cursor toward content they are reading. Use area heatmaps as a proxy for attention when eye-tracking data is unavailable.

### Technical Internals

Understanding how heatmaps work prevents misinterpretation of the data.

1. **DOM snapshot:** When the heatmap script loads, it captures a snapshot of the page's DOM structure and computed styles. This snapshot is used to reconstruct the page for the overlay.

2. **Event coordinate capture:** Click and mouse-move events are captured with their x/y coordinates relative to the viewport. Scroll depth is captured as a percentage of total page height.

3. **Coordinate normalization:** Because users have different viewport widths, coordinates are normalized to a reference width (typically 1280px for desktop). This allows clicks from different screen sizes to be overlaid on the same page snapshot. Normalization is imperfect for highly responsive layouts where element positions shift significantly.

4. **Density map overlay:** Captured coordinates are aggregated into a density grid. A Gaussian blur is applied to smooth the distribution. The result is rendered as a color gradient overlay (typically blue-green-yellow-red from low to high density) on top of the page snapshot.

**Implication:** Heatmaps are most accurate for pages with stable layouts. Pages with significant A/B test variants, personalization, or dynamic content produce misleading heatmaps because the DOM snapshot may not match what individual users saw.

### PostHog Heatmaps

PostHog heatmaps are accessed via the Toolbar — a browser overlay activated from the PostHog dashboard.

**Activation:** In PostHog, navigate to Toolbar and authorize your domain. Install the PostHog Toolbar browser extension or use the bookmarklet. Navigate to your site while the Toolbar is active to see the heatmap overlay.

**Heatmap types available:** Clickmap (click density), Scrollmap (scroll depth), and Heatmap (combined). Switch between types using the Toolbar panel.

**URL matching:** PostHog heatmaps support wildcard URL matching. Use `*` to match any path segment (e.g., `/product/*/reviews` matches all product review pages). This aggregates heatmap data across parameterized URLs into a single view.

**Data source:** PostHog heatmaps use the same event stream as your other PostHog analytics. No additional instrumentation is required beyond the standard PostHog snippet.

**Filtering:** Filter heatmap data by date range, device type, and person properties using the Toolbar panel. This allows comparison of click patterns between user segments.

### Microsoft Clarity Heatmaps

Clarity heatmaps are available for all recorded pages at no cost.

**Heatmap types:** Click heatmaps, scroll heatmaps, and area (move) heatmaps. Access them from the Heatmaps tab in the Clarity dashboard.

**Predictive heatmaps:** Clarity generates predictive heatmaps for pages with insufficient recorded data by using a machine learning model trained on similar pages. Predictive heatmaps are labeled clearly in the UI. Treat them as directional estimates, not measured data.

**Device segmentation:** Clarity automatically segments heatmaps by device type (desktop, tablet, mobile). Always review each segment separately — click patterns and scroll depth differ significantly between device types. A CTA that receives heavy clicks on desktop may be below the fold on mobile.

**Filtering:** Filter heatmaps by date range, browser, country, and custom segments defined in the Clarity dashboard.

---

## Mobile vs Desktop Analysis

Always analyze mobile and desktop sessions separately. Combining them produces misleading averages that represent neither experience accurately.

Key differences to account for:
- Scroll depth is typically lower on mobile due to longer pages and smaller viewports.
- Click targets that are easy to hit on desktop may be too small on mobile, producing rage clicks.
- Navigation patterns differ: mobile users rely on back buttons and swipe gestures that desktop users do not use.
- Conversion rates typically differ by 20-40% between mobile and desktop for e-commerce flows.

In PostHog, use breakdown by `$device_type` on funnels and create separate recording filters for mobile sessions. In Clarity, use the device segmentation controls on heatmaps and filter recordings by device type.

---

## Privacy and Consent Requirements

Different analytics features carry different consent obligations. Apply the minimum consent requirement for each feature you use.

| Feature | Consent Required | Basis |
|---|---|---|
| Cookieless pageview analytics (Plausible, Fathom, Umami) | No | Legitimate interest / no personal data |
| PostHog in cookieless mode (`persistence: "memory"`) | No | No persistent identifier |
| PostHog with cookies (default) | Yes | Cookie sets persistent user ID |
| GA4 (any configuration) | Yes | Cookies + cross-site tracking |
| Session recordings (any tool) | Yes | Captures user behavior, potentially personal data |
| Heatmaps (any tool) | Yes | Aggregated from individual session data |
| Microsoft Clarity (any feature) | Yes | Cookies + session recording by default |

**Recordings always require consent.** Even if a recording tool masks inputs, the act of capturing user behavior constitutes processing of personal data under GDPR. Gate recording initialization behind consent confirmation.

**Heatmaps always require consent.** Heatmap data is derived from individual session recordings or click events tied to sessions. The aggregated output does not eliminate the consent requirement for the underlying data collection.

**Cookieless tools do not require consent** in most EU jurisdictions when configured correctly. Verify that your specific tool configuration does not set cookies or create persistent identifiers before relying on this exemption. Consult your legal team for jurisdiction-specific guidance.

For consent banner implementation and CMP integration, see `vanilla-cookieconsent.md`. For legal framework details, see `consent-architecture.md`.

---

## Data Retention

Retention limits affect how far back you can query funnels and access recordings. Plan your analysis cadence around these limits.

| Tool | Event Retention | Recording Retention | Notes |
|---|---|---|---|
| PostHog (free cloud) | 1 year | 1 year | Recordings count against monthly quota |
| PostHog (paid cloud) | Configurable | Configurable | Up to 7 years on enterprise |
| PostHog (self-hosted) | Unlimited | Disk-limited | You manage storage |
| Microsoft Clarity | 13 months | 13 months | Fixed, cannot be extended |
| GA4 (free) | 2 months (events) / 14 months (user-level) | Not available | User-level data expires at 14 months |
| GA4 (360) | Up to 50 months | Not available | Requires paid 360 subscription |
| Plausible | Unlimited | Not available | Aggregate data only, no recordings |

**Practical implication:** If you need year-over-year funnel comparison, GA4's 14-month user retention is sufficient for annual cohort analysis. PostHog free tier's 1-year retention covers most product analytics needs. Clarity's 13-month retention covers annual seasonal analysis.

---

## Recommended Analytics Stacks

Select a stack based on project stage and requirements. Avoid adding tools that duplicate capabilities you already have.

### Early Stage (Pre-Product-Market Fit)

**Stack:** PostHog free cloud + Microsoft Clarity free

**Rationale:** PostHog provides event analytics, funnels, session recordings, and feature flags in a single free tier. Clarity adds unlimited recordings and heatmaps at no cost. Together they cover all behavioral analytics needs without budget. Both require consent infrastructure.

**Consent requirement:** Both tools require a consent banner. Implement vanilla-cookieconsent with a single analytics category covering both tools.

### Growth SaaS (Post-PMF, Marketing Site + Product)

**Stack:** PostHog paid + Plausible (marketing site) + Clarity (supplemental heatmaps)

**Rationale:** PostHog handles product analytics with higher event and recording quotas. Plausible provides cookieless marketing site analytics that do not require consent, reducing friction for new visitors. Clarity supplements PostHog recordings with free unlimited recordings and predictive heatmaps.

**Consent requirement:** Plausible requires no consent. PostHog and Clarity require consent. Use a two-category consent setup: one for cookieless analytics (Plausible, always on) and one for behavioral analytics (PostHog + Clarity, opt-in).

### E-Commerce

**Stack:** GA4 + Microsoft Clarity + PostHog (exception tracking only)

**Rationale:** GA4 provides the e-commerce event schema (purchase, add_to_cart, begin_checkout) that integrates with Google Ads and Merchant Center. Clarity provides heatmaps and recordings for UX investigation. PostHog exception tracking captures JavaScript errors in the checkout flow without requiring a full PostHog instrumentation.

**Consent requirement:** All three tools require consent. Implement a consent banner with a single analytics category. Use GA4 consent mode v2 to send cookieless pings before consent is granted, preserving conversion modeling.

### Privacy-First / EU-Focused

**Stack:** Plausible or Fathom only

**Rationale:** If your audience is primarily EU-based and your product does not require user-level behavioral analytics, a cookieless tool eliminates the consent banner entirely. This reduces page load friction and avoids the 20-40% consent rejection rate that degrades data quality in other stacks.

**Consent requirement:** None, when configured correctly. Verify with legal counsel for your specific jurisdiction.
