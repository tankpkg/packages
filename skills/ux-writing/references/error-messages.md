# Error Message Patterns

Sources: Yifrah (Microcopy), Podmajersky (Strategic Writing for UX), Shopify Polaris, Microsoft Writing Style Guide, NN/g error message guidelines

Covers: Error message anatomy, severity-driven tone, inline validation, form submission errors, system/network failures, payment-specific copy, 404 recovery, and antipattern catalog.

## Error Message Anatomy

Every error message answers three questions in order:

1. **What happened** — State the effect on the user, not the system.
2. **Why it happened** — Include only when the cause is actionable or non-obvious.
3. **How to fix it** — Give a concrete next step. Link to help if the fix is complex.

The universal formula:

```
[What happened] + [Why, if helpful] + [How to fix]
```

### Applying the Formula

| Situation | Bad | Good |
|---|---|---|
| File too large | "Upload failed" | "This file is over 25 MB. Compress it or choose a smaller file." |
| Duplicate email | "Invalid entry" | "This email is already registered. Log in instead or use a different email." |
| Session expired | "Error 401" | "Your session expired. Log in again to continue." |
| Unsupported format | "Cannot process file" | "PDFs and DOCs are supported. Convert your file and try again." |

### Structural Rules

- Lead with the user impact, not the technical cause.
- Use sentence case. Never all-caps for error headings.
- End with a path forward — a button, a link, or explicit instructions.
- One idea per sentence. Keep sentences under 25 words.
- Use present tense: "Your password doesn't match" not "Your password didn't match."

## Severity Levels

Match visual treatment, placement, and tone to the severity of the problem.

| Severity | Visual Treatment | Placement | Tone | Example |
|---|---|---|---|---|
| Critical/Blocker | Red border, error icon, prominent banner | Top of page or blocking modal | Direct, serious, no humor | "Payment failed. Your card was not charged. Try again or use a different payment method." |
| Warning | Yellow/amber border, warning icon | Inline or banner | Calm, advisory | "Your subscription renews tomorrow. Update your payment method if needed." |
| Info/Suggestion | Blue or neutral, info icon | Inline or toast | Neutral, helpful | "Passwords with 12+ characters are stronger." |

### Tone by Severity

- **Critical:** Strip all personality. No jokes, no "oops," no exclamation marks. Be precise and empathetic.
- **Warning:** Moderate personality. State the risk and the remedy without alarm.
- **Info:** Light personality is acceptable. Frame as guidance, not correction.

## Inline Validation Errors

Inline errors appear beside individual form fields. Timing and phrasing determine whether users feel helped or harassed.

### Timing

| Event | Show Error? | Rationale |
|---|---|---|
| User focuses empty required field, then leaves | No | Punishes exploration. User may intend to return. |
| User types, content is invalid, then leaves field | Yes | User attempted input; feedback is useful. |
| User submits form with empty required fields | Yes | Explicit action taken; surface all issues. |
| User corrects an error mid-typing | Remove error as soon as input becomes valid | Immediate positive feedback reduces frustration. |

Do not validate on blur for empty required fields. This is the most common inline validation mistake — it scolds users before they've tried.

### Placement

- Display the error message directly below the field.
- Use `aria-describedby` to associate the message with the input.
- Pair with a red border on the field — color alone is insufficient (colorblind users).
- Never replace the field label with the error. Both must be visible simultaneously.

### Phrasing Patterns

| Pattern | Don't | Do |
|---|---|---|
| Required field | "This field is required" | "Enter your email address" |
| Format mismatch | "Invalid email" | "Enter an email like name@example.com" |
| Too short | "Too short" | "Use at least 8 characters" |
| Too long | "Maximum length exceeded" | "Use 100 characters or fewer (you've used 142)" |
| Number out of range | "Invalid value" | "Enter a number between 1 and 100" |
| Pattern mismatch | "Invalid format" | "Use only letters, numbers, and hyphens" |

### Password Field Specifics

- Show requirements upfront as a checklist, not after failure.
- Check off each requirement in real time as the user types.
- If showing requirements on error, list all unmet rules — not just the first one.

```
Do:  "Your password needs:
      [x] 8+ characters
      [ ] One uppercase letter
      [ ] One number"

Don't: "Password invalid"
Don't: "Password must contain an uppercase letter" (then, after fixing: "Password must contain a number")
```

## Form Submission Errors

When a form submission fails, the user has already committed effort. Respect that investment.

### Page-Level Error Summary

Display a summary banner at the top of the form:

```
Do:  "2 fields need your attention"
     - Email address: Enter a valid email like name@example.com
     - Phone number: Enter a 10-digit phone number

Don't: "There were errors in your submission"
Don't: "Please fix the following errors and resubmit"
```

Scroll the user to the summary banner after submission. Each item in the summary links to its corresponding field.

### Batch Error Rules

- Count and state how many fields need attention: "3 fields need your attention."
- Anchor-link each error to its field. Clicking an error in the summary focuses that field.
- Keep inline errors visible simultaneously — the summary is a navigation aid, not a replacement.
- Preserve all valid input. Never clear the form on error.
- Disable the submit button only while a request is in flight, not as validation feedback.

### Server-Side Validation Errors

When the server rejects input the client didn't catch:

- Map server error codes to human-readable inline messages.
- Place each message at its corresponding field, identical to client-side errors.
- If a server error doesn't map to a specific field, show it in the page-level summary.

```
Do:  "This username is taken. Try another one."
Don't: "Error: DUPLICATE_KEY_VIOLATION on field 'username'"
```

## System and Network Errors

Users don't know or care about HTTP status codes, DNS resolution, or server architecture. Translate system failures into outcomes and actions.

### Connection and Timeout Errors

```
Do:  "Couldn't connect. Check your internet connection and try again."
Do:  "This is taking longer than usual. Wait a moment or try again."

Don't: "ERR_CONNECTION_TIMED_OUT"
Don't: "Request failed with status code 504"
```

### Server Unavailable

```
Do:  "Something went wrong on our end. Try again in a few minutes."
Do:  "We're fixing a problem right now. Check status.example.com for updates."

Don't: "500 Internal Server Error"
Don't: "The server encountered an unexpected condition"
```

### Permission Denied

```
Do:  "You don't have access to this page. Contact your admin to request access."
Don't: "403 Forbidden"
Don't: "Access denied"
```

### Rate Limiting

```
Do:  "You've made too many requests. Wait 30 seconds and try again."
Don't: "429 Too Many Requests"
```

### Offline States

- Detect offline status and show a persistent, non-dismissable banner.
- State what still works: "You're offline. You can still view saved items."
- Auto-dismiss the banner when connectivity returns.

### General Principles for System Errors

- Never expose stack traces, error codes, or internal identifiers to users.
- Log technical details to the console or error reporting service — not the UI.
- Offer a retry action where applicable. Auto-retry silently for transient failures; show the error only after retries exhaust.
- Include a status page link for extended outages.

## Payment and Financial Errors

Payment errors carry emotional weight. Users feel vulnerability around money. Every word must convey security and competence.

### Core Rules

- Never blame the user. "Your card was declined" is better than "You entered an invalid card."
- Never expose specific decline reasons from the payment processor — they can be misleading or reveal fraud signals.
- Always confirm what didn't happen: "Your card was not charged."
- Offer alternatives immediately.

### Common Payment Errors

| Situation | Message |
|---|---|
| Card declined (generic) | "This card was declined. Try a different card or contact your bank." |
| Insufficient funds | "This card was declined. Try a different payment method." (Never state "insufficient funds" — it's private.) |
| Expired card | "This card has expired. Update the expiration date or use a different card." |
| Incorrect CVV | "Check your security code and try again." |
| Billing address mismatch | "Check your billing address matches your card statement and try again." |
| Duplicate transaction | "It looks like this was already submitted. Check your order history before trying again." |
| Currency not supported | "This card doesn't support [currency]. Try a different card." |
| 3D Secure failure | "Verification wasn't completed. Try again and complete the verification step." |

### Fraud and Security

- Never tell users their transaction was flagged for fraud.
- Use the same "card was declined" language for fraud rejections as for legitimate declines.
- If manual review is needed: "Your order is being reviewed. We'll email you within 24 hours."

## 404 and Not Found Patterns

"Not found" is an error, but it's also a navigation opportunity. The goal is recovery, not a dead end.

### Page Not Found (404)

```
Do:  Heading: "Page not found"
     Body: "This page doesn't exist or may have moved."
     Actions: [Go to homepage] [Search]

Don't: "404 Not Found"
Don't: "Oops! Looks like you're lost! :("
```

- Show the URL that failed — helps users spot typos.
- Suggest likely destinations based on URL patterns.
- Include search if the site has one.
- Keep the main navigation intact. Never hide the nav on a 404.

### Search With No Results

```
Do:  "No results for 'foobar'"
     "Check your spelling or try a broader search term."
     [Show popular searches or categories]

Don't: "0 results"
Don't: "Your search did not match any documents"
```

- Offer spelling correction suggestions automatically.
- Show related or popular items to keep the user in a browsing flow.
- If filters are active, suggest removing filters.

### Deleted or Archived Content

```
Do:  "This item was deleted"
     "It was removed on March 15, 2026."
     [Go to your items]

Do:  "This project was archived"
     "Contact the project owner to restore it."

Don't: "Resource not found"
```

- Distinguish between "never existed," "was deleted," and "was archived."
- Each case requires a different recovery path.

## Error Message Antipatterns

| Antipattern | Why It Fails | Fix |
|---|---|---|
| "Invalid" (e.g., "Invalid email") | No guidance on what's wrong or how to fix it | State the expected format: "Enter an email like name@example.com" |
| "An error has occurred" | Says nothing the user can act on | State the specific error and the fix |
| Raw error codes ("ERR_422", "NullPointerException") | Meaningless to users, signals broken product | Map every code to a human sentence |
| Blame language ("You entered the wrong password") | Creates adversarial relationship | Neutral framing: "That password doesn't match our records" |
| Over-apologizing ("We're so sorry!") | Erodes confidence, reads as insincere at scale | One "sorry" max per flow, only for genuine disruption |
| "Oops!" / "Uh oh!" / "Whoopsie!" | Trivializes the user's problem, especially for critical errors | Remove. Use direct, calm language |
| Exclamation marks in errors | Reads as shouting or panic | Use periods. Reserve exclamation marks for celebrations |
| "Please try again later" (with no context) | User doesn't know when "later" is or what went wrong | State the cause and a specific timeframe if possible |
| Jargon ("SMTP relay failure") | Only meaningful to engineers | Translate to outcomes: "Your email couldn't be sent" |
| Double negatives ("Not invalid") | Increases cognitive load | Positive framing: "This entry is valid" |
| Hiding errors (silent failure) | User thinks action succeeded when it didn't | Always surface feedback for user-initiated actions |
| Generic "Something went wrong" for all errors | Prevents self-service resolution | Differentiate errors so users can resolve what's within their control |

## Writing Error Messages Checklist

Use this when reviewing error copy before shipping.

### Content

- [ ] States what happened in terms the user understands
- [ ] Explains why only if the reason is actionable
- [ ] Provides a concrete next step or action
- [ ] Uses the user's language, not system language
- [ ] Avoids "invalid," "error," "failed," and "please try again" as standalone messages

### Tone

- [ ] Does not blame the user
- [ ] Does not over-apologize
- [ ] Does not use humor for critical errors
- [ ] Matches severity level (serious for critical, calm for warnings)
- [ ] Uses no exclamation marks

### Formatting

- [ ] Sentence case
- [ ] One idea per sentence
- [ ] Under 25 words per sentence
- [ ] Action button uses a specific verb (not "OK" or "Dismiss")

### Accessibility

- [ ] Error is associated with its field via `aria-describedby`
- [ ] Color is not the only indicator (icon or text accompanies red border)
- [ ] Error is announced to screen readers via `aria-live="polite"` or `role="alert"`
- [ ] Focus moves to the first error or the error summary on submission

### Placement and Timing

- [ ] Inline errors appear below their field, not in a tooltip or modal
- [ ] Page-level summary appears at the top and links to each field
- [ ] Errors don't appear on blur for empty required fields
- [ ] Errors clear immediately when the user corrects the input
- [ ] Valid input is preserved on form resubmission
