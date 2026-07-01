# Component Microcopy Patterns

Sources: Yifrah (Microcopy), Podmajersky (Strategic Writing for UX), Google Material Design 3, Microsoft Writing Style Guide, Shopify Polaris

Covers: Element-by-element microcopy patterns for every standard UI component — buttons, headings, labels, tooltips, notifications, dialogs, loading states, and navigation. Do/Don't pairs and character constraints for each.

## Universal Rules

Apply these to every piece of UI text before component-specific rules.

| Rule | Rationale |
|---|---|
| Sentence case | Universal across Google, Microsoft, Apple, Shopify. Title Case feels dated and creates ambiguity with proper nouns. |
| Active voice | "File was deleted" → "You deleted the file." Reduces cognitive load. |
| Present tense | "Your message has been sent" → "Message sent." Present is shorter and more direct. |
| Second person | Address users as "you." Never "the user" or passive constructions. |
| Contractions | Use "don't," "can't," "you'll." Reads as human, not robotic. Exception: legal or compliance text. |
| Lead with the outcome | Front-load the word that matters most. Users scan — the first 2-3 words decide if they read on. |

### Writing Checklist (Per Element)

1. Can the user act on this information right now?
2. Is every word earning its place? (Shopify: "Approach content like Jenga — what's the most you can take away?")
3. Does it match the voice? (Stable qualities.) Does it match the tone? (Context-appropriate modulation.)
4. Would a user understand this without reading anything else on the page?

## Button Labels

Buttons are commitments. The label must tell the user exactly what happens when they click.

### Core Rules

- Start with a verb. The verb is the action; the noun is the object.
- Be specific. Name the outcome, not the gesture.
- Match the button label to the preceding context. If the heading says "Delete project," the button says "Delete project," not "OK."
- Limit to 1-4 words. If a button needs more, the surrounding context is failing.

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| Save changes | Submit | "Submit" is a form mechanic, not a user goal. |
| Create account | OK | "OK" forces users to re-read the dialog to understand what they're agreeing to. |
| Delete 3 items | Yes | "Yes/No" pairs are ambiguous — users must parse the question. |
| Export as PDF | Click here | "Click here" describes the input device, not the outcome. |
| Add to cart | Continue | "Continue" is acceptable only in linear flows where the next step is obvious. |

### Destructive Action Buttons

Destructive actions demand friction. Pair a descriptive red button with a safe escape.

| Pattern | Primary (destructive) | Secondary (safe) |
|---|---|---|
| Delete | Delete project | Keep project |
| Cancel subscription | Cancel subscription | Keep subscription |
| Remove member | Remove [Name] | Go back |
| Discard draft | Discard | Keep editing |

Rules for destructive buttons:
- Name the thing being destroyed in the label.
- Make the safe option visually dominant (outlined or secondary style).
- Never use "Cancel" as a button label in a cancellation dialog — it creates a double negative ("Cancel the cancel?").

### Primary vs Secondary Wording

| Primary | Secondary |
|---|---|
| Specific action verb: "Publish post" | Escape route: "Save as draft" |
| Affirmative commitment | Neutral retreat: "Not now," "Go back," "Keep editing" |
| Matches the page title or dialog heading | Provides the alternative path |

## Headings and Titles

Headings orient. They answer "Where am I?" and "What can I do here?" in under a second.

### Hierarchy Rules

| Level | Purpose | Pattern | Example |
|---|---|---|---|
| Page title | Name the place or task | Noun phrase or verb phrase | "Account settings," "Create a new project" |
| Section heading | Group related content | Short noun phrase | "Billing," "Notifications," "Team members" |
| Dialog title | State what's happening | Brief statement or question | "Delete this file?" or "Unsaved changes" |
| Card title | Identify the object | Noun or noun + qualifier | "Monthly revenue," "Recent activity" |

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| Account settings | Your Account Settings Page | Redundant. The user knows it's a page; drop "Your" and "Page." |
| Delete this file? | Warning! | "Warning" is a category, not content. Name the action. |
| Create project | Create a New Project | Drop articles and adjectives that add no information. |
| Billing | Billing Information and Payment Methods | Scan cost is too high. Shorten; let the page content explain. |

### Rules

- No periods at the end of headings.
- Sentence case (not Title Case).
- Headings are not sentences — omit articles ("a," "the") when possible.
- Dialog titles: if the dialog asks a question, phrase the title as a question. If it states a consequence, phrase it as a statement.

## Labels and Placeholder Text

Three distinct text types serve fields. Each has a job — conflating them creates confusion.

### Role Definitions

| Element | Persists? | Purpose | Example |
|---|---|---|---|
| Field label | Always visible | Identify what to enter | "Email address" |
| Placeholder text | Disappears on focus | Show format or example | "name@company.com" |
| Helper text | Always visible (below field) | Clarify requirements | "Use your work email for SSO" |

### Field Labels

- Use nouns or short noun phrases: "Full name," "Phone number."
- Never end with a colon in modern UI (the field border implies the relationship).
- Keep to 1-3 words. If a label needs more, the field may need redesign.
- Required fields: mark optional fields with "(optional)" rather than marking required fields with an asterisk. Most fields are required — label the exception.

### Placeholder Text

- Format examples only: "MM/DD/YYYY," "name@company.com."
- Never use placeholders as labels. When the user types, the label disappears and they lose context.
- Never put instructions in placeholders. "Enter your email" vanishes on focus — the user loses the instruction mid-task.
- Use lighter text color (not just gray — ensure 4.5:1 contrast ratio for accessibility when visible).

### Helper Text

- Explain constraints before the user hits them: "Password must be at least 8 characters."
- Provide context: "This name appears on your public profile."
- Keep to one sentence. Two sentences means the interface needs simplification.

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| Label: "Email address" / Placeholder: "name@company.com" | Placeholder only: "Enter your email address" | Placeholder disappears. User loses context mid-typing. |
| Helper: "Must be at least 8 characters" | Placeholder: "Must be at least 8 characters" | Requirements must stay visible. |
| Label: "Phone number (optional)" | Label: "Phone number*" with legend "* = optional" | Asterisks are ambiguous. "(optional)" is explicit. |

## Tooltips and Hints

Tooltips are last-resort explanations. If the UI needs a tooltip, consider whether the primary text can be clearer first.

### When to Use

| Use a tooltip | Don't use a tooltip |
|---|---|
| Icon-only buttons that need text equivalents | To explain a core workflow (redesign the UI instead) |
| Jargon the user may not know | To repeat the label with more words |
| Feature behind a toggle that has consequences | For information the user needs before acting (use helper text) |
| Truncated text that needs full display | For required reading (users skip hover states) |

### Writing Rules

- Maximum 150 characters. Beyond that, use an inline hint or a help panel.
- One idea per tooltip. If it needs "and," split into two elements.
- No title in the tooltip unless the trigger element is ambiguous.
- Plain text only — no links, no formatting. (Links are inaccessible in hover states; keyboard users cannot reach them.)
- Start with a verb or a definition — not "This is..."

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| "Pin this item to your sidebar" | "Click this to pin" | Don't describe the interaction mechanic. |
| "API key for authenticating requests" | "This is your API key that you use to authenticate your API requests" | Remove filler. One pass of information. |
| "Available after trial ends" | "This feature is currently locked because you are on a trial plan" | Front-load the timing; omit the obvious. |

## Notifications and Toasts

Notifications interrupt. Earn the interruption with density and immediate relevance.

### Anatomy

```
[Icon] [Title — 3-5 words] [optional body — 1 sentence] [optional action]
```

### Patterns by Type

| Type | Icon | Title pattern | Body pattern | Duration |
|---|---|---|---|---|
| Success | Checkmark | Past tense outcome: "Changes saved" | Omit unless next step exists | 4-6 seconds auto-dismiss |
| Info | Info circle | Neutral statement: "New version available" | One sentence of context | Persistent or 8 seconds |
| Warning | Triangle | Present tense risk: "Storage almost full" | Consequence + threshold | Persistent until resolved |
| Error | X circle | See `references/error-messages.md` | See `references/error-messages.md` | Persistent until action taken |

### Constraints

- Snackbar/toast: maximum 2 lines on mobile (Material Design 3 spec).
- One action button maximum on toasts. Two actions belong in a banner or dialog.
- Action button label: verb, not "Dismiss." Give the user a forward path: "Upgrade," "Undo," "View."
- No exclamation marks in success messages (Atlassian). Celebration inflation devalues real wins.
- No periods in toast titles. Period in body text only if it is a complete sentence.

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| "Changes saved" | "Your changes have been successfully saved!" | Strip filler. No "successfully" — success is implied by the checkmark. |
| "3 files uploaded" | "Upload complete" | Specificity builds confidence. Name the count. |
| "Connection lost. Retrying..." | "Something went wrong" | Name the problem. Vague messages erode trust. |
| Action: "Undo" | Action: "OK" | "OK" acknowledges. "Undo" gives control. |

## Confirmation Dialogs

Confirmation dialogs exist to prevent irreversible mistakes. If the action is reversible, skip the dialog.

### When to Confirm

| Confirm | Skip confirmation |
|---|---|
| Permanent deletion | Archiving (reversible) |
| Payment or billing change | Saving a draft |
| Removing another user's access | Toggling a non-critical setting |
| Exiting with unsaved changes | Navigation within the app |

### Anatomy

```
[Title: Name the action or consequence]
[Body: 1-2 sentences — what happens and whether it's reversible]
[Secondary button: safe exit]  [Primary button: confirm action]
```

### Title Patterns

| Scenario | Title | Why |
|---|---|---|
| Deleting data | "Delete [object name]?" | Question format signals a decision point. |
| Losing unsaved work | "Unsaved changes" | Statement format signals a status. |
| Removing a person | "Remove [Name] from [Team]?" | Include the person's name — specificity prevents mistakes. |
| Irreversible action | "This can't be undone" | When the consequence is more important than the action. |

### Body Text Rules

- State the consequence explicitly: "This will permanently delete all 12 files in this folder."
- Include counts and names: "Remove Alex from the Design team? They'll lose access to 4 shared projects."
- If reversible, say so: "You can restore this from Trash within 30 days."
- If irreversible, say so: "This action can't be undone."
- Never use "Are you sure?" — it adds a question without adding information.

### Button Pairing

| Context | Destructive button | Safe button |
|---|---|---|
| Delete | "Delete [object]" | "Keep [object]" |
| Discard | "Discard changes" | "Keep editing" |
| Remove user | "Remove [Name]" | "Cancel" |
| Leave page | "Leave without saving" | "Stay on page" |

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| Title: "Delete 'Q3 Report'?" / Body: "This file will be permanently deleted." / Buttons: "Delete file" / "Keep file" | Title: "Are you sure?" / Body: "Do you want to delete this?" / Buttons: "Yes" / "No" | Every element must carry specific information. Generic text forces re-reading. |
| "Remove Alex from Design? They'll lose access to 4 shared projects." | "Remove this member from the team?" | Names and numbers eliminate ambiguity. |

## Loading States

Loading is dead time. Use it to set expectations and maintain the user's sense of progress.

### Patterns by Wait Duration

| Duration | Pattern | Copy guidance |
|---|---|---|
| < 1 second | No indicator needed | Instant feedback via state change (button → disabled). |
| 1-3 seconds | Spinner with label | Short verb phrase: "Saving..." "Loading dashboard..." |
| 3-10 seconds | Progress bar or skeleton | Describe what's loading: "Loading your projects..." |
| 10-30 seconds | Progress bar + percentage or step | Name the stage: "Processing images (3 of 12)..." |
| > 30 seconds | Background task with notification | "We'll notify you when the export is ready." |

### Spinner and Progress Labels

- Use the gerund (verb + "-ing"): "Uploading," "Generating report."
- Include the object when context is ambiguous: "Loading dashboard" not just "Loading."
- End with ellipsis (...) to signal ongoing activity. No period.
- Never say "Please wait" — it shifts the cognitive burden to patience instead of progress.

### Skeleton Screens

Skeleton screens replace content with placeholder shapes. No text is needed on the skeleton itself. The value is spatial continuity — the user sees the layout before the data.

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| "Uploading 3 files..." | "Please wait while we upload your files" | Remove "please wait." Name the count. |
| "Generating report (2 of 5)..." | "Loading..." | Progress steps reduce perceived wait time. |
| "This may take a few minutes. We'll email you when it's done." | "Processing. Do not close this window." | Give the user freedom; don't trap them. |

## Navigation and Menus

Navigation text is wayfinding. Users scan it to build a mental model of the product.

### Menu Items

- Use nouns for destinations: "Dashboard," "Settings," "Team."
- Use verbs for actions: "Create project," "Import data," "Invite member."
- Never mix nouns and verbs at the same level — pick one pattern per menu section.
- 1-2 words maximum for top-level navigation. Save longer labels for submenus.

### Breadcrumbs

- Mirror the page titles exactly. "Settings > Notifications" not "Settings > Notification preferences" if the page title is "Notifications."
- Truncate the middle, not the ends: "Home > ... > Project settings > Integrations."
- The current page in the breadcrumb is not a link.

### Tab Labels

- Nouns only: "Overview," "Activity," "Members," "Settings."
- Parallel structure: if one tab is a plural noun, all tabs should be plural nouns.
- Include counts when useful: "Comments (12)," "Issues (3)."
- Maximum 1-2 words per tab. Tabs with 3+ word labels signal an information architecture problem.

### Do / Don't

| Do | Don't | Why |
|---|---|---|
| Dashboard · Projects · Team · Settings | Home · View Projects · Manage Your Team · System Settings | Inconsistent patterns and unnecessary verbs inflate scan cost. |
| Overview · Activity · Members | General · What's Happening · People on This Project | Parallel structure, minimal words. |
| Comments (12) | Comments | Counts set expectations and surface activity. |

## Character Constraint Quick Reference

| Component | Recommended limit | Source |
|---|---|---|
| Button label | 1-4 words | Cross-system consensus |
| Toast title | 3-5 words | Atlassian, Material Design 3 |
| Toast body | 1 sentence, ≤ 60 characters | Material Design 3 (2-line mobile max) |
| Tooltip | ≤ 150 characters | Shopify Polaris |
| Dialog title | 3-8 words | Material Design 3 |
| Dialog body | 1-2 sentences | Cross-system consensus |
| Field label | 1-3 words | Shopify Polaris |
| Helper text | 1 sentence | Podmajersky |
| Tab label | 1-2 words | Cross-system consensus |
| Top-level nav item | 1-2 words | Cross-system consensus |
| Breadcrumb segment | Match page title | Material Design 3 |
| Loading label | Verb + object, ≤ 30 characters | Microsoft Style Guide |
| Section heading | 1-3 words | Shopify Polaris |
