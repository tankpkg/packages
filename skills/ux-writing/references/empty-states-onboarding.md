# Empty States and Onboarding Copy

Sources: Yifrah (Microcopy), Podmajersky (Strategic Writing for UX), Metts/Welfle (Writing Is Designing), NN/g empty state guidelines, Atlassian Design System

Covers: Copy patterns for empty screens, first-run experiences, onboarding flows, permission requests, feature discovery, zero-data dashboards, success celebrations, and upgrade gates.

## Empty State Anatomy

Every empty state follows a four-part formula:

```
[What's missing] + [Why it's empty] + [What to do next] + [Action button]
```

**What's missing** names the absent content in the user's language. Say "No projects yet" not "0 items found." Frame the absence around the user's goal, not the system's data model.

**Why it's empty** gives a one-sentence explanation calibrated to the empty state type. First-use states explain the feature. No-results states explain the filter. Error-caused states explain the failure. Skip this element when the reason is self-evident.

**What to do next** provides a concrete instruction. Use imperative form: "Create your first project" not "You can create a project." One action path. If multiple paths exist, pick the most common and link the rest.

**Action button** uses a verb-noun label matching the instruction. "Create project" not "Get started." The button is the bridge from empty to populated — make it specific.

### Do/Don't: First-Use Empty State

| Do | Don't |
|---|---|
| **No invoices yet.** Create your first invoice to start tracking payments. [Create invoice] | **It's empty in here!** There are currently no items to display in this section. [Get started] |
| **Your dashboard is ready.** Add a widget to see your metrics at a glance. [Add widget] | **Nothing to show.** You haven't added anything yet. Please add some content to see it here. [OK] |

## Empty State Types

| Type | When it appears | Tone | Pattern |
|---|---|---|---|
| First-use | User has never created content here | Welcoming, instructive | Explain the value of the feature + single clear CTA |
| No results | Search or filter returns nothing | Helpful, neutral | Restate the query + suggest broadening + offer reset |
| Cleared/completed | User finished all tasks or cleared items | Celebratory or calm | Acknowledge completion + suggest what's next |
| Error-caused | Content failed to load | Reassuring, direct | State the problem + offer retry or workaround |
| No permission | User lacks access rights | Respectful, informative | Explain what's here + who to contact for access |

### First-Use Empty States

Frame around the value the user will unlock, not the mechanics of the feature.

```
Your reports will appear here.
Track revenue, usage, and growth — all in one place.
[Create your first report]
```

Avoid "Welcome to the Reports section!" — the page heading already communicates where they are. Use the body copy to sell the outcome.

### No-Results Empty States

Mirror the user's search intent back to them, then offer escape routes.

```
No results for "quarterly review"
Try different keywords, check for typos, or clear your filters.
[Clear filters]
```

Never blame the user. "Your search didn't match anything" implies the user failed. "No results for [query]" keeps it neutral.

### Cleared/Completed Empty States

Match the emotional weight of the accomplishment. Inbox-zero deserves acknowledgment. Clearing a notification list does not.

| Context | Copy |
|---|---|
| All tasks complete | **All caught up.** Completed tasks move to your archive. |
| Inbox cleared | **Nothing new.** You've handled everything. |
| Cart emptied | **Your cart is empty.** Browse products to find something you like. |

### Error-Caused Empty States

See `references/error-messages.md` for full error writing patterns. In empty state context, keep the error explanation brief and pair it with a retry action.

```
Couldn't load your projects.
Check your connection and try again.
[Retry]
```

### No-Permission Empty States

Respect the user's position. Avoid making them feel locked out or lesser.

```
Projects is available on the Team plan.
Talk to your admin to upgrade, or explore other features.
[Contact admin]  [Explore features]
```

Never say "You don't have permission." Say what the content is and how to get access.

## First-Run Experience

### Welcome Screens

A welcome screen earns exactly one interaction before the user's patience expires. Spend it on orientation, not celebration.

**Structure:**

1. Headline: State the core value in 6 words or fewer
2. Subhead: One sentence expanding on the benefit
3. Primary CTA: The most important first action
4. Secondary link: Skip or explore on their own

| Do | Don't |
|---|---|
| **Ship faster with automated deploys.** Connect your repo to deploy on every push. [Connect repository] | **Welcome to DeployPro!** We're so excited you've joined us. There's so much to explore. Let's get started on your journey! [Let's go!] |

Avoid "Welcome to [Product]" as a headline — it wastes the most prominent real estate on information the user already knows.

### Feature Tours

Write tour steps as micro-tasks, not feature descriptions.

| Step pattern | Example |
|---|---|
| **Bad:** "This is the sidebar. It contains navigation." | Describes furniture. |
| **Good:** "Pin your most-used projects here for quick access." | Teaches a behavior. |

Each tooltip in a tour should answer: "What can I do here that I couldn't figure out alone?" If the answer is nothing, cut the step.

**Tour copy rules:**

- 3-5 steps maximum per tour
- Lead each step with a verb: "Drag," "Click," "Pin," "Filter"
- End the tour with a productive action, not "You're all set!"
- Offer "Skip tour" on every step, not just the first

### Progressive Onboarding

Reveal complexity gradually. Teach features at the moment they become relevant, not in a front-loaded tutorial.

| Stage | Writing approach |
|---|---|
| First session | Explain only what's needed for the first task |
| After first success | Introduce one adjacent feature ("Now that you've created a project, invite your team") |
| Power-user threshold | Surface shortcuts and advanced features via contextual tips |

## Permission Requests

### Why Before What

Users grant permissions at higher rates when they understand the benefit before seeing the system dialog. Use a pre-permission screen.

**Pre-permission pattern:**

```
[Benefit headline]
[1-sentence explanation of why the permission helps them]
[Allow] [Not now]
```

**Example:**

```
Get notified when tasks are assigned to you.
We'll send a push notification so you never miss a deadline.
[Turn on notifications]  [Not now]
```

### Benefit-Led Framing

| Do | Don't |
|---|---|
| **Find nearby stores** — Location access shows stores within walking distance. | **Allow location access?** This app wants to use your location. |
| **Import contacts to find your team** — We'll check if anyone you know is already here. | **Access your contacts?** We need your contact list to function properly. |

Frame the permission as a feature the user is activating, not a resource the app is demanding.

### Declining Gracefully

When a user declines, acknowledge it without guilt. Explain what they'll miss and how to re-enable later.

```
No problem. You can turn on notifications anytime in Settings.
```

Never re-prompt immediately after a decline. Wait until the user encounters a moment where the permission would have helped.

## Onboarding Flows

### Signup Copy

Reduce friction at every field. Each piece of signup text should either reduce anxiety or accelerate completion.

| Element | Pattern |
|---|---|
| Headline | State the benefit of signing up, not "Create an account" |
| Social auth buttons | "[Logo] Continue with Google" — verb + provider name |
| Email field label | "Work email" or "Email" — never "Enter your email address" |
| Password requirements | Show requirements upfront, validate inline, never reveal only on error |
| Submit button | "Create account" or "Start free trial" — never "Submit" |
| Terms | "By creating an account, you agree to our [Terms] and [Privacy Policy]." — one line, links only |

### Email Verification

The verification screen is a dead zone where users abandon. Keep them engaged.

```
Check your email
We sent a verification link to ada@example.com.
Didn't get it? [Resend email]  [Change email address]
```

Provide both "Resend" and "Change email" — users mistype addresses more often than they think. Display the address they entered so they can spot typos.

### Profile Completion

Use progress indicators with copy that frames completion as a benefit, not an obligation.

| Do | Don't |
|---|---|
| **3 steps to a complete profile** — Complete profiles get 40% more responses. | **Your profile is incomplete!** Please fill out all required fields. |
| **Add a photo** — Teams with photos collaborate 2x faster. | **Upload profile picture** (required) |

Defer non-essential fields. Ask for the minimum at signup and request details when they become relevant.

## Feature Discovery

### Tooltips and Spotlights

Contextual tips appear when the user first encounters a feature. Write them as quick wins.

**Tooltip formula:** [What you can do] + [How to do it] — in 15 words or fewer.

```
Filter by date range — click the calendar icon to narrow results.
```

### Coachmarks

Numbered coachmarks walk through a complex interface. Limit to 3-4 per sequence.

| Step | Copy pattern |
|---|---|
| 1 | **Start here.** [Verb] + [object] to [outcome]. |
| 2 | **Then try this.** [Verb] + [object] for [benefit]. |
| 3 | **One more thing.** [Verb] + [object] when you need [advanced use]. |
| Finish | [Productive CTA] — not "Got it!" |

### Walkthrough Copy Rules

- Anchor each step to a visible UI element
- Use present tense: "Click here to filter" not "You will be able to filter"
- Dismiss options: "Got it" for single tips, "Skip" + step count for sequences
- Never block the primary workflow — coachmarks overlay, never prevent action
- Trigger by behavior, not by calendar ("first time visiting this page" not "3 days after signup")

## Success States and Celebrations

### When to Celebrate

| Situation | Response |
|---|---|
| First-ever completed action (first deploy, first invoice) | Celebrate: short congratulation + next step |
| Routine completed action (100th commit) | Quiet: confirmation only |
| Milestone achievement (10 projects, 1-year anniversary) | Celebrate if user opted into gamification |
| Cleared inbox or task list | Acknowledge calmly: "All caught up." |
| Upgrade or purchase | Confirm + reassure: "Your plan is now active." |

### Celebration Copy

Keep celebrations proportional to effort. Over-celebrating trivial actions feels patronizing.

| Do | Don't |
|---|---|
| **First deploy complete.** Your site is live at example.com. [View site] | **AMAZING! You did it! Your first deploy is done! We're so proud of you!** |
| **Invoice sent.** You'll get a notification when Alex views it. | **Woohoo! Invoice successfully sent! Great job!** |

One exclamation mark per screen, maximum. Atlassian's guideline: no exclamation marks in success messages at all. Calibrate to your product's voice.

### Streak and Reward Copy

If the product uses streaks, badges, or gamification:

- State the achievement factually: "7-day streak" not "OMG 7 days!"
- Connect it to real value: "7-day streak — you've reviewed 23 PRs this week"
- Let the visual (animation, badge, confetti) carry the emotional weight; the copy stays grounded

## Zero-Data Dashboards

Dashboards with charts and tables are the hardest empty states because the page structure implies data should exist.

### Charts With No Data

Replace the chart area with a contextual message, not a broken or blank chart.

```
Revenue will appear here after your first sale.
Connect a payment provider to start tracking.
[Connect Stripe]
```

Never render empty axes and gridlines with "No data" floating in the center. Replace the entire chart region.

### Tables With No Data

| Approach | When to use |
|---|---|
| Single-row message inside the table | User expects a table and may add rows (e.g., team members) |
| Replace table with centered empty state | Table is not the primary UI metaphor (e.g., dashboard widget) |

Table-row message pattern:

```
| Name | Role | Status |
| --- | --- | --- |
| No team members yet. [Invite your team] to start collaborating. | | |
```

### System Status Communication

When data will arrive automatically (analytics, logs, monitoring), communicate the system state:

```
Waiting for data...
Events will appear here within a few minutes of connecting your app.
[View setup guide]
```

Use "Waiting for data" (the system is working) not "No data yet" (the user failed to provide something).

## Upgrade and Paywall Copy

### Feature Gates

When a free user encounters a paid feature, frame the gate as a value proposition, not a restriction.

| Do | Don't |
|---|---|
| **Unlock advanced analytics** — See conversion funnels, retention curves, and custom reports. [See plans] | **This feature is not available on your plan.** Upgrade to access it. [Upgrade] |
| **Custom domains are available on Pro.** Use your own domain to match your brand. [Compare plans] | **Error: Feature restricted.** You must upgrade. |

### Value Framing Rules

- Name the specific features they'll unlock, not "premium features"
- Lead with the benefit ("See conversion funnels") before the mechanism ("available on Pro")
- Use "See plans" or "Compare plans" over "Upgrade now" — let users evaluate before committing
- Never use "Error" or "Restricted" language for intentional feature gates
- Provide a way to dismiss or go back — gates should inform, not trap

### Trial Expiry Copy

Progressive urgency, not sudden panic:

| Days remaining | Tone | Example |
|---|---|---|
| 7+ | Informational | "Your trial ends in 10 days. [See plans]" |
| 3-6 | Gentle nudge | "3 days left in your trial. Keep your data by choosing a plan. [Choose plan]" |
| 1 | Urgent, not alarming | "Your trial ends tomorrow. [Upgrade to keep access]" |
| Expired | Matter-of-fact | "Your trial has ended. Your data is saved for 30 days. [Choose a plan] [Export data]" |

Never threaten data loss without providing an export option. State the retention period explicitly.
