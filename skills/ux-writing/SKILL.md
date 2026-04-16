---
name: "@tank/ux-writing"
description: |
  Write clear, effective interface copy — microcopy, error messages, onboarding
  flows, form labels, empty states, notifications, and every word users read
  inside an app. Covers voice and tone design, component-level microcopy
  patterns, error message formulas, content design process, form copy,
  inclusive/accessible writing, and localization readiness.
  Synthesizes Yifrah (Microcopy), Podmajersky (Strategic Writing for UX),
  Winters (Content Design), Metts/Welfle (Writing Is Designing), Hall
  (Conversational Design), Fenton/Lee (Nicely Said), Ben-David (The Business
  of UX Writing), plus Google Material Design, Apple HIG, Microsoft,
  Shopify Polaris, Atlassian, and NN/g research.

  Trigger phrases: "UX writing", "microcopy", "UI copy", "interface copy",
  "error message", "empty state", "onboarding copy", "button label",
  "form copy", "placeholder text", "validation message", "toast message",
  "notification copy", "voice and tone", "content design", "UX text",
  "confirmation dialog", "call to action", "CTA copy", "helper text",
  "loading message", "success message", "permission request copy",
  "write the copy for", "what should this button say",
  "how to word this error", "write microcopy for"
---

# UX Writing

## Core Philosophy

1. **Clarity is non-negotiable.** Users scan, they don't read. Every word
   must earn its place — if removing it changes nothing, remove it.
2. **Write the conversation, not the interface.** Imagine explaining the
   action to someone sitting next to you. That's the copy.
3. **Microcopy is UX.** A confusing error message is a broken feature.
   Copy is as functional as code — it directly impacts task completion,
   conversion rates, and support ticket volume.
4. **Voice is stable, tone adapts.** The product sounds like itself
   everywhere, but dials warmth up for onboarding and seriousness up for
   errors. Define voice once, map tone per context.
5. **Every component has a pattern.** Buttons, errors, empty states,
   tooltips, forms — each has proven formulas. Use them instead of
   reinventing from scratch.

## Quick-Start: Common Problems

### "Write error message copy"

1. Apply the three-part formula: [What happened] + [Why] + [How to fix]
2. Match severity tier to tone (critical = direct, warning = advisory)
3. Avoid "invalid", "oops", error codes, blame language
   -> See `references/error-messages.md`

### "Write copy for an empty state"

1. Apply the four-part formula: [What's missing] + [Why empty] + [Next step] + [Action button]
2. Match empty state type (first-use, no results, cleared, error-caused)
3. Frame as opportunity, not absence
   -> See `references/empty-states-onboarding.md`

### "What should this button say?"

1. Start with a verb — describe the action, not the noun
2. Be specific: "Save changes" not "Submit", "Delete project" not "OK"
3. For destructive actions, name what's being destroyed
   -> See `references/component-microcopy.md`

### "Write form labels and helper text"

1. Labels above inputs, sentence case, no colons
2. Mark the minority (optional fields if most are required, or vice versa)
3. Use helper text for format hints — never rely on placeholder text alone
   -> See `references/forms-and-inputs.md`

### "Define voice and tone for our product"

1. Run the voice discovery workshop (3-5 voice attributes)
2. Map tone per context using the dial model
3. Document with Do/Don't examples per attribute
   -> See `references/voice-and-tone.md`

### "Make this copy accessible / localization-ready"

1. Target 7th-8th grade reading level, max 25 words per sentence
2. Avoid idioms, metaphors, cultural references, humor that won't translate
3. Budget 30-40% word expansion for translated strings
   -> See `references/inclusive-writing.md`

## Decision Trees

### What to Write First

| Signal | Start With |
|--------|------------|
| New product / no voice defined | Voice and tone framework |
| Specific screen needs copy | Component-level patterns for that element |
| High error/support volume | Error messages and form validation |
| Low activation / high churn | Empty states and onboarding |
| Redesign / content audit | Content design process |
| International audience | Inclusive writing + localization |

### Tone by Context

| UI Context | Tone Setting | Reasoning |
|------------|-------------|-----------|
| Onboarding / welcome | Warm, encouraging | User is uncertain — build confidence |
| Success / completion | Brief, satisfied | Don't over-celebrate routine tasks |
| Error / failure | Direct, helpful | Frustration is high — solve fast |
| Destructive action | Serious, precise | Consequences are real — no ambiguity |
| Empty state | Inviting, optimistic | Motivate the first action |
| Loading / waiting | Calm, transparent | Reduce anxiety about progress |
| Settings / admin | Neutral, informative | Task-focused, no personality needed |
| Payment / financial | Careful, reassuring | Money triggers anxiety — build trust |

### Copy Length by Component

| Component | Target Length | Hard Limit |
|-----------|-------------|------------|
| Button label | 1-3 words | 5 words |
| Toast / snackbar | 1-2 lines | 2 lines mobile |
| Tooltip | 1-2 sentences | 150 characters |
| Dialog title | 3-8 words | 1 line |
| Error inline | 1 sentence | 2 sentences |
| Empty state body | 1-3 sentences | 4 sentences |
| Helper text | 1 sentence | 80 characters |

## Reference Index

| File | Contents |
|------|----------|
| `references/voice-and-tone.md` | Voice discovery workshop, tone mapping (Apple dials, Google axes, NN/g dimensions), voice documentation, antipatterns |
| `references/component-microcopy.md` | Element-by-element patterns: buttons, headings, labels, tooltips, notifications, dialogs, loading, navigation |
| `references/error-messages.md` | Error anatomy formula, severity tiers, inline/form/system/payment/404 patterns, antipattern catalog |
| `references/empty-states-onboarding.md` | Empty state types, first-run experience, permission requests, feature discovery, success states, upgrade copy |
| `references/content-design-process.md` | Content-first design, discovery, workflow, pair writing, crits, testing, measuring impact, style guides |
| `references/forms-and-inputs.md` | Labels, placeholders, helper text, validation, selects, checkboxes, file uploads, multi-step, submit/confirm |
| `references/inclusive-writing.md` | Plain language, screen readers, inclusive language, localization, RTL, sensitivity, cognitive load |
