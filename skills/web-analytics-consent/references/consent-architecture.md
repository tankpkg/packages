# Consent Architecture and Legal Framework

Sources: GDPR (Regulation 2016/679), ePrivacy Directive (2002/58/EC as amended 2009), CCPA (Cal. Civ. Code 1798.100+), EDPB Guidelines 05/2020 on consent, EDPB Guidelines 2/2019 on legitimate interest, CNIL enforcement decisions 2022-2024, EU Digital Omnibus Proposal COM(2025)87, ICO Cookie Guidance 2023, Plausible Analytics documentation, PostHog documentation.

---

## The Dual Regulatory Framework

Web analytics sits at the intersection of two distinct legal regimes. Conflating them produces incorrect compliance strategies.

**ePrivacy Directive (2002/58/EC)** governs access to and storage of information on a user's device. Article 5(3) states that storing or accessing information on terminal equipment requires the user's prior informed consent, unless the operation is strictly necessary to provide a service explicitly requested by the user. This directive applies regardless of whether the data is personal. A cookie containing only a random session token still triggers Article 5(3).

**GDPR (Regulation 2016/679)** governs the processing of personal data. It applies once data is collected and linked to an identifiable individual. Analytics that produce personal data — IP addresses, persistent identifiers, behavioral profiles — require a lawful basis under Article 6.

The practical consequence: a single analytics implementation may require compliance with both regimes simultaneously. A cookie that stores a user ID triggers ePrivacy consent for the storage act and GDPR lawful basis for the subsequent processing of that identifier as personal data.

### When Each Regime Applies

| Trigger | Applicable Law | Default Position |
|---|---|---|
| Setting a cookie (any content) | ePrivacy Directive | Consent required unless strictly necessary |
| Reading localStorage or IndexedDB | ePrivacy Directive | Consent required unless strictly necessary |
| Processing an IP address | GDPR | Lawful basis required |
| Building a behavioral profile | GDPR | Consent required (Article 6(1)(a)) |
| Aggregated, non-identifiable statistics | Neither (if truly anonymous) | No consent required |
| Fingerprinting without storage | GDPR if identifiable | Lawful basis required |

---

## GDPR Consent Requirements

When consent is the chosen lawful basis under Article 6(1)(a), it must satisfy all five conditions simultaneously. Failure on any single condition invalidates the consent.

### The Five Conditions

**Freely given.** The user must have a genuine choice. Consent is not freely given when refusal results in denial of service, when consent is bundled with terms of service, or when the consent interface makes rejection significantly harder than acceptance. The CNIL fined Google 150 million EUR and Facebook 60 million EUR in 2022 specifically because their interfaces provided a single-click "Accept all" button while requiring multiple steps to reject. Regulators treat asymmetric UI as coercion.

**Specific.** Consent must be obtained separately for each distinct purpose. A single checkbox covering "analytics and marketing" is invalid. Users must be able to consent to analytics without consenting to advertising, and vice versa.

**Informed.** The user must understand what they are consenting to before giving consent. This requires identifying the controller, naming third-party processors, describing the purpose, and stating the retention period. Vague language such as "improve your experience" does not satisfy this requirement.

**Unambiguous.** Consent requires a clear affirmative act. Pre-ticked checkboxes, continued browsing, and scrolling do not constitute consent. The user must take a deliberate action — clicking a button, toggling a switch — that unambiguously signals agreement.

**Withdrawable.** Withdrawing consent must be as easy as giving it. If consent was given via a single click, withdrawal must also be achievable via a single click. Consent management platforms must provide a persistent mechanism — typically a footer link or floating button — that reopens the preference center at any time.

### Consent Records

Maintain a record of each consent event containing: timestamp, user identifier (session-level, not persistent), consent version, purposes accepted, purposes rejected, and the UI state presented. This record must be producible on regulatory request. Store consent records for the duration of the consent plus any applicable statute of limitations (typically three years in EU jurisdictions).

---

## What Counts as Strictly Necessary

The ePrivacy exemption for "strictly necessary" operations is narrow. Apply it only when the technical operation is essential to deliver a service the user has explicitly requested. Interpret "explicitly requested" as an active user-initiated action, not passive site visit.

### Necessary Without Consent

- Session cookies that maintain login state across page requests
- Shopping cart cookies that persist item selections during a session
- Load balancer cookies that route requests to the correct server
- Security cookies that prevent cross-site request forgery
- Cookies that store the user's consent preferences (the consent cookie itself)
- Language preference cookies set in direct response to a user's language selection

### Not Necessary — Consent Required

- Analytics cookies that track page views, sessions, or user journeys
- A/B testing cookies that assign users to experiment variants
- Heatmap and session recording scripts that capture interaction data
- Advertising cookies that build interest profiles
- Social media tracking pixels embedded by third parties
- Performance monitoring that identifies individual users across sessions

The test is not whether the business finds the data useful, but whether the service would fail to function without the specific storage operation. Analytics data improves the service; it does not enable the service to function.

---

## Legitimate Interest for Analytics

Article 6(1)(f) permits processing where the controller has a legitimate interest that is not overridden by the data subject's interests or fundamental rights. The EDPB has clarified the scope of this basis for analytics contexts.

### The Three-Part Test

Apply all three parts. Failure at any stage means legitimate interest is unavailable.

**Part 1 — Purpose test.** The interest must be legitimate: lawful, clearly articulated, and real rather than speculative. Basic reach measurement — understanding how many people visit a site and which pages are popular — qualifies. Building behavioral profiles for advertising does not. The EDPB has explicitly rejected legitimate interest as a basis for behavioral advertising.

**Part 2 — Necessity test.** The processing must be necessary to achieve the purpose. If the same insight can be obtained with less privacy-invasive means, the more invasive approach fails this test. Aggregate page view counts do not require persistent user identifiers. If cookieless analytics achieves the same measurement goal, cookie-based analytics cannot claim necessity.

**Part 3 — Balancing test.** The controller's interest must not be overridden by the data subject's reasonable expectations. Consider: the nature of the data, the relationship between controller and subject, the likely impact on the subject, and whether the subject would reasonably expect this processing. Users visiting a website do not reasonably expect to be tracked across sessions for analytics purposes without notice.

### When Legitimate Interest Applies to Analytics

Legitimate interest may support basic, aggregated, cookieless analytics where:
- No persistent identifier is stored on the device
- IP addresses are not retained beyond the processing moment
- Data is aggregated before storage
- No cross-site tracking occurs
- The user can reasonably anticipate that site operators measure traffic

### When Legitimate Interest Does Not Apply

- Any analytics that sets cookies or writes to localStorage
- Session replay and heatmap tools that capture individual interactions
- Analytics that link behavior across multiple sessions
- Any analytics shared with or sold to third parties
- Behavioral advertising, regardless of how it is labeled

---

## GDPR vs CCPA: Structural Differences

The two regimes reflect fundamentally different regulatory philosophies. Building a single consent flow that satisfies both requires understanding where they diverge.

| Dimension | GDPR (EU/EEA) | CCPA (California) |
|---|---|---|
| Default position | No processing without lawful basis | Processing permitted by default |
| Model | Opt-in | Opt-out |
| Consent for analytics | Required (unless cookieless + LI) | Not required; opt-out right applies |
| Right to opt out | N/A (must opt in) | Right to opt out of sale/sharing |
| Applicability threshold | Any processing of EU residents' data | >$25M revenue, OR 100K+ consumers, OR 50%+ revenue from data sales |
| Sensitive data | Explicit consent required | Opt-in required for sensitive categories |
| Enforcement | Data protection authorities, up to 4% global turnover | California AG, private right of action for data breaches |
| Consent record requirement | Yes, demonstrable | No formal record requirement |
| Right to withdraw | Must be as easy as giving consent | Right to opt back in after opting out |

### Practical Implications for Analytics

Under GDPR, analytics cookies require prior consent from EU visitors. The site must not fire analytics scripts until consent is recorded. Under CCPA, analytics processing may begin immediately; the obligation is to honor opt-out requests and to disclose data sharing in a privacy policy.

For sites with global audiences, implement GDPR-compliant opt-in consent for EU/EEA visitors and CCPA-compliant opt-out mechanisms for California residents. Geolocation-based consent logic is acceptable and common. Use the visitor's IP address to determine jurisdiction at page load, before any tracking fires.

CCPA's "sale or sharing" definition is broad. Passing analytics data to Google Analytics constitutes "sharing" under CCPA if Google uses that data for cross-context behavioral advertising. Google's default GA4 configuration does this. Enable Google's "Restricted Data Processing" mode for California visitors to avoid CCPA sale/sharing obligations.

---

## Consent Categories

Structure consent into four standard categories. This taxonomy aligns with IAB TCF 2.2 purposes and is recognized by major regulators.

| Category | Description | Consent Required | Examples |
|---|---|---|---|
| Necessary | Operations essential to service delivery | No | Session cookies, CSRF tokens, consent storage |
| Analytics | Measurement of site usage and performance | Yes (GDPR); opt-out (CCPA) | GA4, PostHog, Plausible with cookies |
| Functionality | Enhanced features beyond core service | Yes | Language preferences beyond session, saved preferences |
| Marketing | Advertising, retargeting, behavioral profiling | Yes | Meta Pixel, Google Ads, LinkedIn Insight Tag |

Do not create subcategories that obscure the nature of processing. Regulators have penalized consent interfaces that use euphemistic category names to make marketing consent appear more benign than it is.

Present categories in a layered interface: a first layer with category-level toggles and a second layer with per-vendor detail. The IAB TCF 2.2 standard provides a vendor list and purpose taxonomy that satisfies this requirement for participating vendors.

---

## Cookieless Analytics: Legal Basis Without Consent

Several analytics tools are designed to operate without setting cookies or writing to persistent storage. These tools can, in some jurisdictions and configurations, rely on legitimate interest rather than consent.

### How Cookieless Identification Works

Plausible Analytics, Fathom Analytics, and Umami use a daily rotating hash to distinguish unique visitors without persistent identifiers. The hash is computed from the visitor's IP address, User-Agent string, and the site's domain. The hash changes every 24 hours and is never stored — not in a cookie, not in localStorage, not in a database. The same visitor on consecutive days produces different hashes. This approach counts unique visitors within a day without tracking individuals across days or across sites.

Because no information is stored on or read from the user's device, Article 5(3) of the ePrivacy Directive does not apply. Because the hash is not retained and cannot be used to identify an individual, GDPR's definition of personal data is not engaged (subject to the caveat below regarding IP addresses).

### The ePrivacy Caveat for Client-Side Storage

The ePrivacy exemption applies only when no storage or access occurs on the user's device. This includes:

- Cookies (all types, all durations)
- localStorage
- sessionStorage
- IndexedDB
- Cache API
- Service Worker storage
- Web SQL (deprecated but still covered)

A tool that avoids cookies but writes analytics data to localStorage is not cookieless in the legal sense. It still triggers Article 5(3) and requires consent. Verify each tool's actual storage behavior, not its marketing claims.

### PostHog Memory Persistence

PostHog supports `persistence: 'memory'` configuration, which prevents the SDK from writing to cookies or localStorage. In this mode, the distinct ID is held only in JavaScript memory and lost on page reload. This configuration avoids ePrivacy obligations for the storage act.

However, memory persistence alone does not eliminate all consent requirements. If PostHog's `identify()` method is called with a user ID, that creates a personal data processing event requiring a lawful basis. Session replay captures keystrokes, clicks, and page content — this is personal data processing that requires consent regardless of persistence configuration. Evaluate each PostHog feature independently.

### Cookieless Tools and Legitimate Interest

For tools that genuinely avoid device storage and do not retain identifiable data, legitimate interest is a plausible basis in many EU jurisdictions. The analysis must still pass the three-part test. Document the assessment. Note that some EU data protection authorities — particularly the Austrian DSB and the French CNIL — have taken the position that IP addresses are always personal data and that any analytics involving IP addresses requires consent or pseudonymization before processing.

The safest approach: use server-side IP anonymization (truncate the last octet before any processing or storage) and document this in the legitimate interest assessment.

---

## Data Retention Requirements

Retention periods must be disclosed in the privacy notice and enforced technically. Storing data beyond the disclosed retention period is a GDPR violation independent of the lawful basis used to collect it.

| Tool | Default Retention | Configurable | Notes |
|---|---|---|---|
| Google Analytics 4 | 2 months (events), 14 months (user data) | Yes, up to 14 months for events | Configure in Admin > Data Settings > Data Retention |
| PostHog Cloud | 1 year | Yes, on paid plans | Self-hosted: unlimited, operator responsibility |
| Microsoft Clarity | 13 months | No | Rolling 13-month window, not configurable |
| Plausible Analytics | Unlimited aggregate | N/A | No individual-level data retained |
| Fathom Analytics | Unlimited aggregate | N/A | No individual-level data retained |
| Umami | Operator-defined | Yes | Self-hosted; configure database retention policy |

Set retention periods to the minimum necessary for the stated purpose. If analytics data is used for monthly reporting, 14 months of retention is defensible. If used only for real-time dashboards, 30 days may be the maximum justifiable period.

Include retention periods in the consent notice presented to users. "We retain analytics data for 14 months" is a required disclosure, not optional detail.

---

## EU Digital Omnibus Proposal

The European Commission published the EU Digital Omnibus proposal in November 2025 (COM(2025)87). This proposal would amend the ePrivacy Directive and is not yet law. Do not treat it as current compliance guidance.

### Proposed Changes Relevant to Analytics

**Aggregated audience measurement exemption.** The proposal would exempt analytics that produce only aggregated, non-identifiable statistics from the ePrivacy consent requirement. If enacted, this would allow basic traffic measurement without a consent banner, provided the data is genuinely aggregated and no individual-level data is retained.

**Browser-level privacy signal recognition.** The proposal would require websites to respect browser-level privacy signals, including the Global Privacy Control (GPC) header. Sites would be legally obligated to treat a GPC signal as an opt-out from non-necessary processing, without requiring the user to interact with a consent banner.

**Anticipated Timeline.** The proposal must pass through the European Parliament and Council. Based on typical legislative timelines for ePrivacy amendments, implementation is not expected before 2027-2028. Member states would then have a transposition period. Plan current implementations for existing law; monitor the proposal's progress for future architecture decisions.

Do not implement the proposed exemptions as if they are current law. Regulators enforce existing law, not proposed amendments.

---

## Enforcement Landscape

Cookie-specific fines exceeded 100 million EUR across EU jurisdictions in 2024. Enforcement has concentrated on three violation patterns:

**Asymmetric consent interfaces.** Interfaces where accepting all cookies requires one click but rejecting requires multiple steps or navigation to a separate page. The CNIL's Google and Facebook decisions established that this pattern constitutes coercion, invalidating the resulting consent.

**Pre-ticked boxes and implied consent.** Consent interfaces that pre-select analytics or marketing categories, or that treat continued browsing as consent. Both practices have been found invalid by multiple DPAs.

**Consent walls.** Requiring consent to analytics as a condition of accessing content. The EDPB's Guidelines 05/2020 state that consent is not freely given when refusal results in denial of service, unless the controller offers an equivalent service without tracking.

The ICO, CNIL, and German DPAs have all issued guidance stating that "reject all" must be available at the same level of prominence as "accept all." Implement a three-button first layer: "Accept All," "Reject All," and "Manage Preferences."

---

## GDPR Compliance Checklist

Use this checklist before deploying any analytics implementation. Each item maps to a specific legal requirement.

### Legal Basis

- [ ] Identify the lawful basis for each analytics tool and each processing purpose
- [ ] Document the legitimate interest assessment if relying on Article 6(1)(f)
- [ ] Confirm that behavioral advertising does not rely on legitimate interest
- [ ] Verify that consent is the basis for all cookie-based analytics for EU visitors

### Consent Interface

- [ ] "Accept All" and "Reject All" are available at the same prominence on the first layer
- [ ] Pre-ticked boxes are not used for any non-necessary category
- [ ] Consent is not bundled with terms of service acceptance
- [ ] The interface does not deny service to users who reject non-necessary cookies
- [ ] Each consent category is described in plain language identifying the purpose and processors

### Technical Implementation

- [ ] No analytics scripts fire before consent is recorded for EU visitors
- [ ] Consent state is stored and respected across sessions
- [ ] Withdrawal mechanism is accessible at all times (footer link or floating button)
- [ ] Withdrawal is as easy as giving consent (single interaction)
- [ ] Consent records are stored with timestamp, version, and accepted/rejected purposes

### Data Minimization and Retention

- [ ] IP addresses are anonymized before storage (last octet truncated at minimum)
- [ ] Retention periods are configured to the minimum necessary in each tool
- [ ] Retention periods are disclosed in the privacy notice
- [ ] Data deletion requests can be fulfilled within 30 days

### Third-Party Processors

- [ ] Data processing agreements are in place with all analytics vendors
- [ ] Third-party vendors are named in the consent notice
- [ ] Data transfers outside the EEA have a valid transfer mechanism (SCCs, adequacy decision)
- [ ] Google Analytics Restricted Data Processing is enabled for CCPA jurisdictions

### Documentation

- [ ] Privacy notice describes all analytics processing, purposes, and retention periods
- [ ] Legitimate interest assessments are documented and dated
- [ ] Consent records are retained for the duration of consent plus three years
- [ ] DPA registration is current if required in the relevant jurisdiction
