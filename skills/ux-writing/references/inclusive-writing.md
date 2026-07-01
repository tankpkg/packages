# Inclusive and Accessible Writing

Sources: Microsoft Writing Style Guide, Apple HIG, So (Voice Content and Usability), Metts/Welfle (Writing Is Designing), WCAG 2.2, Atlassian Design System

Covers: Making interface text work for all users — plain language, screen reader compatibility, inclusive defaults, localization readiness, RTL support, sensitive contexts, and cognitive load reduction.

## Plain Language Principles

Write for the widest possible audience. Every extra syllable is a barrier.

### Reading Level Targets

| Audience | Target Grade Level | Flesch-Kincaid Score | Example Domain |
|---|---|---|---|
| Consumer products | 7th-8th grade | 60-70 | Banking apps, e-commerce |
| Developer tools | 9th-10th grade | 50-60 | API docs, CLIs |
| Enterprise B2B | 8th-9th grade | 55-65 | SaaS dashboards |
| Accessibility-critical | 6th grade or lower | 70+ | Government, healthcare |

### Sentence and Word Rules

- Cap sentences at 25 words. Break longer sentences into two.
- Use one idea per sentence. Compound clauses increase parse time by 40%.
- Prefer common words over formal synonyms: "use" not "utilize", "start" not "initiate", "end" not "terminate".
- Avoid nominalizations: "decide" not "make a decision", "configure" not "perform configuration".
- Remove filler phrases: "in order to" → "to", "at this point in time" → "now", "due to the fact that" → "because".
- Spell out abbreviations on first use. After that, use the abbreviation only if it appears three or more times.

### Jargon Policy

| Context | Acceptable | Replace With |
|---|---|---|
| Error messages | Never use jargon | Plain description of what happened |
| Developer tools | Domain terms OK | Define on first use or link to glossary |
| Settings labels | Avoid unless standard | Descriptive phrase + help text |
| Legal/compliance | Required terms only | Pair legal term with plain summary |

Test readability with Hemingway Editor, Flesch-Kincaid scoring, or Microsoft Editor. Run checks before every release.

## Writing for Screen Readers

Screen readers linearize content. Write as if every user reads top-to-bottom, one element at a time.

### Alt Text for Images

- Functional images (icons, buttons): describe the action. "Search", "Close dialog", "Download report".
- Informational images (charts, photos): describe the content. "Bar chart showing revenue growth from $2M to $5M over Q1-Q4".
- Decorative images: use empty `alt=""`. Never omit the `alt` attribute entirely — that forces screen readers to read the file name.
- Complex images (infographics, diagrams): provide a short `alt` plus a longer description via `aria-describedby` or a linked text alternative.

### Meaningful Link Text

| Bad | Good | Why |
|---|---|---|
| "Click here" | "View your billing history" | Identifies destination |
| "Learn more" | "Learn more about two-factor authentication" | Distinguishes from other "Learn more" links |
| "Read more" | "Read the full changelog for v3.2" | Scannable in link lists |
| "Here" | "Download the accessibility report" | Understandable out of context |

Screen reader users navigate by tabbing through links. Each link must be understandable in isolation, without surrounding text.

### ARIA Labels and Live Regions

- Add `aria-label` when visible text is insufficient: icon-only buttons, abbreviated labels, ambiguous controls.
- Write ARIA labels as full phrases: `aria-label="Remove item from cart"` not `aria-label="Remove"`.
- For dynamic content updates (toasts, counters, status changes), pair the UI text with `aria-live="polite"` or `aria-live="assertive"` regions.
- Avoid redundant ARIA. If a button says "Save changes", do not add `aria-label="Save changes"` — the visible text is already the accessible name.

### Heading Hierarchy

- Use heading levels (H1-H6) in strict order. Never skip levels for visual styling.
- Write headings as concise labels: "Payment method" not "Please select your preferred payment method".
- Each page needs exactly one H1. It should match the page title or primary task.
- Screen reader users scan by heading. Every distinct section needs a heading — even sections that are visually obvious require a heading for non-visual navigation.

## Inclusive Language

Default to language that includes everyone. Exclusion is never a style choice.

### Gender-Neutral Defaults

- Use "they/them/their" as the default singular pronoun. It has been standard in English since the 14th century.
- Address users directly with "you/your" — this avoids gendered pronouns entirely and is the preferred UI writing pattern.
- Replace gendered terms with neutral alternatives:

| Replace | With |
|---|---|
| Guys, ladies | Everyone, team, folks |
| Mankind | Humanity, people |
| Man-hours | Person-hours, labor hours |
| Manpower | Workforce, staffing |
| Chairman | Chair, chairperson |
| Master/slave | Primary/replica, leader/follower, main/secondary |
| Whitelist/blacklist | Allowlist/blocklist |
| Grandfathered | Legacy, exempt |
| Sanity check | Confidence check, coherence check |

### Ability and Disability

- Use person-first language by default: "person with a disability" not "disabled person". Follow the preference of the specific community when known — some Deaf and autistic communities prefer identity-first language.
- Never use disability as metaphor: "blind to the issue", "lame excuse", "crazy prices", "falling on deaf ears".
- Describe interface actions without assuming physical ability:

| Assumes Ability | Inclusive Alternative |
|---|---|
| "See the results below" | "The results appear below" |
| "Watch the tutorial" | "View the tutorial" or "Follow the tutorial" |
| "Click the button" | "Select the button" |
| "Tap and hold" | "Select and hold" or "Long press" |

### Age, Culture, and Family

- Do not assume family structure. Use "parent or guardian" not "mom or dad". Use "household" not "family" when referring to shared accounts.
- Avoid age-based assumptions. "Even your grandmother could use it" is patronizing. Describe simplicity without referencing age groups.
- Do not assume cultural context. Holidays, seasons, food references, sports metaphors, and humor conventions vary globally.
- Avoid referencing skin color or ethnicity in examples unless directly relevant.

## Localization-Ready Writing

Write English that translates well. Localization problems start in the source language.

### What Breaks in Translation

| Pattern | Problem | Fix |
|---|---|---|
| Idioms and metaphors | "It's a piece of cake" has no equivalent in most languages | Use literal, direct language |
| Humor and wordplay | Puns and cultural jokes fail silently | Remove or replace with neutral phrasing |
| String concatenation | `"You have " + count + " items"` breaks grammar in languages with different word order | Use ICU MessageFormat: `{count, plural, one {# item} other {# items}}` |
| Hardcoded plurals | `item + (count > 1 ? "s" : "")` fails in languages with 3+ plural forms (Arabic has 6) | Use CLDR plural rules via i18n library |
| Embedded variables mid-sentence | "Welcome back, {name}!" works in English but {name} placement varies by language | Allow translators to reorder variables |
| Sentence fragments as UI | "Settings > Advanced > Network" may need restructuring | Provide full translatable strings, not fragments |

### Date, Time, and Number Awareness

- Never hardcode date formats. "03/04/2025" means March 4 (US) or April 3 (most of the world).
- Use relative time for recent events: "2 minutes ago", "Yesterday". Let the i18n library handle formatting.
- Do not assume decimal points. Many European locales use commas: 1.234,56 not 1,234.56.
- Currency placement varies: $100 (US), 100€ (France), ¥100 (Japan). Always use locale-aware formatting.

### Word Expansion Budgets

UI layouts must accommodate text expansion when translated from English.

| Target Language | Expansion Factor | Notes |
|---|---|---|
| German | 30-40% longer | Compound words are common |
| French | 15-20% longer | Articles and prepositions add length |
| Finnish | 30-40% longer | Agglutinative — words accumulate suffixes |
| Japanese | 10-20% shorter | Kanji compress meaning |
| Arabic | 20-25% longer | Right-to-left, different numeral widths |
| Chinese (Simplified) | 10-30% shorter | Dense logographic script |

Design UI with expansion in mind:
- Avoid fixed-width containers for text. Use flexible layouts.
- Buttons need 30-40% extra width headroom.
- Navigation labels: keep English under 15 characters to give translators room.
- Never truncate translated text — it may cut mid-word or mid-meaning.

### Translatable String Rules

- Write complete sentences, not fragments that get assembled at runtime.
- Isolate UI strings into resource files. Never embed user-facing text in code logic.
- Provide translator context: comments explaining where the string appears, what it refers to, and any character limits.
- Avoid reusing identical English strings for different contexts. "Post" (noun) and "Post" (verb) need separate translation keys.

## Right-to-Left Considerations

Arabic, Hebrew, Farsi, and Urdu require mirrored layouts. Text direction affects more than alignment.

### RTL Layout Impact on Copy

- UI mirrors horizontally. Back arrows point right. Progress bars fill right-to-left. Navigation flows right-to-left.
- Icons with directional meaning (arrows, send, reply) must flip. Icons without direction (home, settings, search) stay the same.
- Bidirectional text (mixing RTL and LTR in one string) needs explicit Unicode direction marks. Example: a Hebrew sentence containing an English brand name.
- Numbers in RTL languages still read left-to-right. Phone numbers, dates, and numeric IDs do not mirror.

### Writing Guidelines for RTL

- Test every string in RTL context. Text that reads naturally in English may break visual flow when mirrored.
- Avoid left/right directional references in copy. "The menu on the left" fails in RTL. Use "the navigation menu" or positional labels that adapt.
- Ensure text alignment responds to `dir="rtl"`. Use logical CSS properties (`margin-inline-start`) rather than physical ones (`margin-left`).
- Punctuation placement follows the language direction. Parentheses, quotation marks, and brackets must adapt.

## Sensitivity and Emotional Context

Some interface moments carry emotional weight. Write with extra care when users face stress, fear, or vulnerability.

### Money and Financial Difficulty

- State amounts clearly. No hidden fees revealed in small print.
- Use neutral language around financial status. "Your account balance is $0" not "You have no money".
- Avoid celebratory language for charges: "Payment of $500 processed successfully!" reads differently to someone struggling financially. Prefer: "Payment of $500 confirmed."
- Provide clear next steps for failed payments without shame: "We couldn't process your payment. Update your payment method to continue."

### Health and Medical

- Use precise, non-alarmist language. "Your results are ready for review" not "Important health alert!"
- Never diagnose or imply diagnosis in UI copy. Present data; let professionals interpret.
- Allow users to skip or dismiss health-related prompts without judgment.
- Respect that health information is deeply personal. Minimize data collection language to what is strictly necessary.

### Legal and Compliance

- Pair legal language with plain-language summaries. Show the legal text for compliance; show the summary for comprehension.
- Do not hide consent in walls of text. Surface the key commitment clearly: "You agree to a 12-month subscription at $10/month."
- Label required disclosures explicitly. "Required by law" helps users understand why they are reading dense text.

### Personal Data and Privacy

- Explain why data is collected before asking for it. "We use your location to show nearby stores" preceding the permission request.
- Use precise language about data handling: "stored on your device", "sent to our servers", "shared with partners". Avoid vague terms like "processed" without explanation.
- Give clear confirmation when data is deleted: "Your account data has been permanently deleted. This cannot be undone."

### Account Deletion and Destructive Actions

- Use direct, unambiguous language: "Delete your account and all data permanently" not "Deactivate".
- State consequences explicitly before the action: "You will lose: 47 projects, 3 team memberships, and all billing history."
- Require explicit confirmation with clear, non-tricky phrasing. The cancel button should say "Keep my account" not "Cancel".
- Avoid guilt-tripping retention copy: "Are you sure? We'll miss you!" manipulates users during a vulnerable moment.

## Color and Visual References in Text

Never rely on color alone to convey meaning. WCAG 1.4.1 requires information conveyed by color to also be available without it.

### Problematic Patterns

| Fails Accessibility | Accessible Alternative |
|---|---|
| "Fields marked in red are required" | "Required fields are marked with an asterisk (*)" |
| "Click the green button to continue" | "Select Continue to proceed" |
| "See the highlighted items" | "See the items marked with a star icon" |
| "Errors are shown in red below" | "2 errors found. See details below each field." |

### Guidelines

- Reference elements by label, position, or icon — never by color alone.
- Pair color indicators with text labels, icons, or patterns. A red error badge also needs the word "Error" or an error icon.
- Status indicators need text equivalents: green dot + "Online", yellow dot + "Away", red dot + "Offline".
- Charts and graphs need patterns, labels, or textures in addition to color differentiation.

## Cognitive Load Reduction

Reduce the mental effort required to parse interface text. Every unnecessary word is a tax on attention.

### Chunking Information

- Group related information under clear headings.
- Use bullet lists for 3+ items. Inline lists ("A, B, and C") work for 2-3 short items only.
- Limit choices presented at once. Show 3-5 options; hide the rest behind progressive disclosure.
- Separate instructions from context. Lead with what to do, then explain why.

### Progressive Disclosure in Copy

- Show essential information first. Move details behind expandable sections, tooltips, or "Learn more" links.
- Label progressive disclosure clearly. "Show advanced options" tells users what is hidden. "More" does not.
- Default to the simplest path. Advanced users will find settings; beginners need guidance.

### One Idea Per Sentence

| Overloaded | Split |
|---|---|
| "Enter your email address, which we'll use to send you a verification code that expires in 10 minutes." | "Enter your email address. We'll send a verification code. The code expires in 10 minutes." |
| "Your subscription renews automatically on the 1st of each month unless you cancel before the renewal date in your account settings." | "Your subscription renews on the 1st of each month. Cancel anytime in Account Settings." |

### Scannable Structure

- Front-load keywords. Put the most important word first in headings, labels, and list items.
- Use consistent patterns. If one list item starts with a verb, all items start with a verb.
- Keep parallel structure. Inconsistent formatting forces users to re-parse each item.
- Use whitespace intentionally. Dense blocks of text signal "skip this" to most users.

## Writing for Diverse Literacy Levels

Design for the full spectrum — multilingual users, non-native speakers, varying technical comfort.

### Multilingual Audiences

- Use short, simple sentences. They translate more accurately and are easier for non-native readers.
- Avoid phrasal verbs when possible: "submit" not "send in", "cancel" not "call off", "continue" not "go on".
- Provide visual context alongside text. Icons, illustrations, and layout reinforce meaning when language is a barrier.
- Consider offering language switching prominently — not buried in a footer link.

### Technical vs Non-Technical Paths

- Offer layered explanations. A simple label for everyone, a technical detail for power users.
- Example: "Two-factor authentication" as the label, "Requires a 6-digit code from your authenticator app (TOTP)" as help text.
- Never assume everyone knows acronyms. Expand on first use, even common ones like "URL" or "API" in consumer-facing products.

### Readability Across Education Levels

- Write for the lowest common denominator without being condescending. Short sentences and common words are not "dumbed down" — they are clear.
- Use examples to clarify abstract concepts. "Enter a strong password (example: Sunset-Tiger-42!)" is clearer than "Enter a strong password."
- Test with real users across literacy levels. Readability scores are proxies, not guarantees.

## Localization Testing Checklist

Run these checks before shipping any localized release.

| Test | Method | Pass Criteria |
|---|---|---|
| Pseudo-localization | Replace strings with accented characters (ëñüß) and padding | UI renders without clipping, overflow, or layout breaks |
| String length stress | Inject German-length strings (140% of English) into all UI elements | No truncation, no overlapping, no broken layouts |
| Plural forms | Test 0, 1, 2, 5, 11, 21 in each locale | Correct plural form for every count in every language |
| RTL mirror | Switch to Arabic or Hebrew locale | Layout mirrors correctly, bidirectional text renders properly |
| Concatenation audit | Search codebase for string concatenation with variables | All dynamic strings use ICU MessageFormat or equivalent |
| Date/time/number | Display dates, times, currencies in each locale | Locale-appropriate formatting throughout |
| Cultural review | Native speaker reviews all strings in context | No offensive, confusing, or culturally inappropriate content |
| Context screenshots | Provide translators with screenshots of every string in situ | Translations match the UI context, not just the isolated string |
| Character encoding | Verify UTF-8 handling for CJK, Arabic, Thai, Devanagari | No mojibake, no missing characters, no rendering artifacts |
| Truncation audit | Check all fixed-width elements across locales | No meaningful content cut off; ellipsis used appropriately |
