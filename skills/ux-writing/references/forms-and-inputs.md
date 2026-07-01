# Form and Input Copy

Sources: Yifrah (Microcopy), Podmajersky (Strategic Writing for UX), Shopify Polaris, Google Material Design 3, Microsoft Writing Style Guide

Covers: Copy patterns for every form element — labels, placeholders, helper text, validation, buttons, multi-step flows, and confirmation states. Forms are the highest-friction touchpoint in most apps; precise copy directly impacts conversion and completion rates.

## Field Labels

Place labels above the input. Inline labels (inside the field) vanish on focus and break accessibility. Left-aligned labels work for dense admin forms but slow scan speed on consumer-facing flows.

### Phrasing Rules

- Use sentence case: "Email address" not "Email Address"
- State what the field collects, not what the user should do: "Company name" not "Enter your company name"
- Keep to 1-3 words when possible
- Match the label to the data: "Phone number" not "Phone" when the format matters

| Do | Don't |
|---|---|
| Full name | Please enter your full name |
| Email address | Your Email Address |
| Date of birth | DOB |
| Billing address | Address for Billing Purposes |

### Required vs Optional Marking in Labels

Mark the minority. If most fields are required, mark only optional fields with "(optional)" appended to the label. If most are optional, mark required fields with "(required)" or an asterisk.

| Form composition | Mark strategy | Example |
|---|---|---|
| Mostly required fields | Append "(optional)" to the few optional ones | "Middle name (optional)" |
| Mostly optional fields | Append "(required)" or use asterisk | "Email address *" |
| All required | No marking needed — add a single note above the form | "All fields are required." |

When using asterisks, always include a legend at the top of the form: "* Required". Never rely on color alone.

## Placeholder Text

### When to Use

Use placeholders only to show expected format — never as a replacement for labels. Placeholder text disappears on focus, creating a memory burden. Screen readers may skip it entirely.

| Do | Don't |
|---|---|
| Label: "Phone number" / Placeholder: "(555) 123-4567" | Placeholder only: "Enter your phone number" |
| Label: "Website" / Placeholder: "https://example.com" | Placeholder as instruction: "Type your URL here" |
| No placeholder when the label is self-explanatory | Repeating the label as placeholder: "Email" / "Email" |

### When NOT to Use

- When the label already communicates the expected input clearly
- For critical information the user needs to reference while typing
- On fields where example data could be confused with pre-filled data (use helper text instead)

## Helper Text

Persistent text below a field that provides context the label alone cannot convey. Unlike placeholders, helper text remains visible during and after input.

### When to Add

- The field has specific format or length requirements
- The data request may confuse users ("This appears on your receipt")
- Privacy or usage context matters ("We will only use this to verify your identity")

### Phrasing

- Lead with the benefit or reason, not the constraint
- Keep to one sentence, under 80 characters
- Use sentence case, no period unless multiple sentences

| Field | Helper text |
|---|---|
| Password | At least 8 characters with one number |
| Username | This will be your public display name |
| SSN | Used only for identity verification — encrypted and never stored |
| Promo code | Find this on your invitation email |

| Do | Don't |
|---|---|
| Appears on your public profile | Warning: this will be visible to other users!!! |
| At least 8 characters | Must contain minimum 8 characters, including upper case, lower case, number and symbol |

## Input Masks and Formatting Hints

Show the expected format explicitly so users do not have to guess. Use input masks (auto-formatting as the user types) or format hints in helper text.

| Input type | Mask / hint approach | Example display |
|---|---|---|
| Phone number | Input mask with auto-grouping | (555) 123-4567 |
| Credit card | Input mask with spaces every 4 digits | 4242 4242 4242 4242 |
| Date | Placeholder showing format | MM/DD/YYYY |
| Currency | Prefix symbol, auto-decimal | $0.00 |
| ZIP / Postal code | Helper text for format | "5 digits or ZIP+4 (12345-6789)" |

When the input auto-formats, tell the user: "We will format this as you type." Avoid surprising transformations without explanation.

## Select and Dropdown Options

### Default Option Text

Use an instructional default that cannot be confused with a real selection.

| Do | Don't |
|---|---|
| "Select a country" | "Country" (repeats the label) |
| "Choose a role" | "-- Select --" (generic, unhelpful) |
| "None" (when no-selection is valid) | "" (empty default — ambiguous) |

### Option Labeling

- Use parallel phrasing across all options
- Front-load the distinguishing word: "Monthly billing" / "Annual billing" not "Billing — monthly"
- Sort logically: alphabetical for long lists, frequency-based for short lists, chronological for dates

### Sorting Order

| List type | Sort by |
|---|---|
| Countries / states | Alphabetical, with user's detected country first |
| Frequency options (Daily, Weekly) | Logical sequence, not alphabetical |
| Plan tiers | Low to high (or high to low if upselling) |

## Checkbox and Radio Copy

### Statement Phrasing

Write checkboxes as affirmative statements the user agrees to by checking. Write radio buttons as noun phrases or short declarative options the user selects between.

| Type | Do | Don't |
|---|---|---|
| Checkbox | "Send me weekly updates" | "Do you want weekly updates?" |
| Checkbox | "I agree to the Terms of Service" | "Terms of Service agreement" |
| Radio | "Standard shipping (5-7 days)" | "Click here for standard" |
| Radio | "Pay monthly" / "Pay annually" | "Monthly?" / "Annual?" |

### Group Labels

Every checkbox or radio group needs a visible group label (the `<legend>` in a `<fieldset>`). Phrase it as a question or instruction:

- "How would you like to be contacted?"
- "Select your plan"
- "Notification preferences"

### Positive Framing

Frame options positively. Let users opt in to what they want, not opt out of what they do not want.

| Do | Don't |
|---|---|
| "Send me product updates" | "Uncheck to stop receiving emails" |
| "Keep me signed in" | "Don't sign me out" |

## File Upload Instructions

Communicate accepted formats, size limits, and quantity constraints before the user attempts an upload.

### Pre-Upload Messaging

Place format and size constraints as helper text beneath the upload area:

- "Accepted formats: JPG, PNG, or PDF. Max 10 MB."
- "Upload up to 5 files. Each file must be under 25 MB."

### Drag-and-Drop Messaging

| State | Copy |
|---|---|
| Default | "Drag files here or browse" |
| Hover / dragover | "Drop files to upload" |
| Uploading | "Uploading 3 files..." with progress indicator |
| Success | "3 files uploaded" with file names listed |
| Failure | "invoice.pdf could not be uploaded — file exceeds 10 MB" |

| Do | Don't |
|---|---|
| "Drag files here or browse" | "Click or drag and drop files into this area to upload" |
| "PNG or JPG, up to 5 MB" | "Supported file types: .png, .jpg, .jpeg, .gif, .bmp, .tiff" |

## Inline Validation Copy

Validate as the user completes each field — not on submit only. Show feedback adjacent to the field, not in a banner at the top of the form.

### Timing

| Validation type | When to trigger |
|---|---|
| Format errors (email, phone) | On blur (after the user leaves the field) |
| Character/length limits | Real-time as the user types |
| Availability checks (username) | After a debounce (300-500ms after last keystroke) |
| Required field empty | On blur or on submit — never while the user is still in the field |

### Tone by Severity

| Severity | Tone | Example |
|---|---|---|
| Success | Neutral confirmation | "Username is available" |
| Warning | Helpful, non-blocking | "This password is weak — consider adding numbers or symbols" |
| Error | Direct, solution-first | "Enter an email address — for example, name@company.com" |

### Phrasing Rules

- State what to do, not what went wrong: "Enter a valid phone number" not "Invalid phone number"
- Never use "invalid" — it is jargon and feels accusatory (Shopify Polaris, Google Material Design 3)
- Include an example when the correct format is not obvious
- Keep to one line — under 60 characters

| Do | Don't |
|---|---|
| Enter a 10-digit phone number | Error: Invalid phone format |
| Passwords must be at least 8 characters | Too short |
| Enter a date in MM/DD/YYYY format | Bad date |
| This field is required | Required! |

Cross-reference: see `error-messages.md` for error message patterns beyond inline validation.

## Form Progress and Multi-Step

### Step Labels

Label each step with what the user accomplishes in it, not a generic number.

| Do | Don't |
|---|---|
| "1. Shipping / 2. Payment / 3. Review" | "Step 1 / Step 2 / Step 3" |
| "Account details" | "Page 1 of 3" |

### Progress Indicators

Show both position and total: "Step 2 of 4" or a segmented progress bar with labels. Communicate time expectation when possible: "About 2 minutes left."

### Save and Resume

When forms can be saved mid-flow, tell the user:

- Auto-save: "Your progress is saved automatically"
- Manual save: "Save and continue later" (button label)
- Returning: "Welcome back — pick up where you left off"

| Do | Don't |
|---|---|
| "Your progress is saved automatically" | (silently auto-saving with no indication) |
| "Save and continue later" | "Save draft" (ambiguous — draft of what?) |

## Submit Button Copy

### Action-Specific Labels

Name the button after the action it performs. Generic labels ("Submit", "OK", "Continue") create uncertainty about what will happen.

| Context | Do | Don't |
|---|---|---|
| Account creation | "Create account" | "Submit" |
| Payment | "Place order" / "Pay $49.00" | "Continue" |
| Newsletter | "Subscribe" | "Submit" |
| Search filters | "Apply filters" | "Go" |
| Settings | "Save changes" | "OK" |
| Destructive | "Delete project" | "Yes" / "Confirm" |

### Loading State

Replace button text with a present-participle verb matching the action:

- "Create account" becomes "Creating account..."
- "Place order" becomes "Placing order..."
- "Save changes" becomes "Saving..."

Disable the button during loading to prevent duplicate submissions.

### Disabled State

When a submit button is disabled because the form is incomplete, do not rely on the disabled state alone. Provide a visible explanation:

- Tooltip on hover: "Complete all required fields to continue"
- Inline note beneath the button: "Fill in the highlighted fields above"

| Do | Don't |
|---|---|
| Disabled button + note explaining why | Grayed-out button with no explanation |
| "Complete all required fields to continue" | (nothing — user clicks repeatedly, confused) |

## Success and Confirmation

### Immediate Feedback

After submission, confirm the action and tell the user what happens next.

| Action | Confirmation copy |
|---|---|
| Account created | "Account created. Check your email to verify." |
| Order placed | "Order confirmed. You will receive a confirmation email at alex@example.com." |
| Settings saved | "Changes saved." (inline, near the save button — no page redirect) |
| File uploaded | "Resume uploaded successfully." |

### Confirmation Details

For transactional forms (orders, bookings, registrations), display a summary:

- Order number or reference ID
- Key details (items, dates, amounts)
- Next step: "You will receive a confirmation email within 5 minutes"
- Escape hatch: "Something wrong? Contact support" or "Edit order"

### Receipt and Summary Patterns

- Lead with the most important confirmation: "Your order is confirmed"
- Follow with specifics in a structured summary (table or key-value list)
- Close with the next expected event and a timeline: "Ships within 2 business days"

| Do | Don't |
|---|---|
| "Order confirmed. Shipping in 2-3 days." | "Success!" (what succeeded? what now?) |
| "Check your email to verify your account" | "Thank you for registering" (no next step) |

## Password and Security Fields

### Strength Indicators

Show password strength as the user types. Use a visual meter paired with a text label.

| Strength | Label | Color |
|---|---|---|
| Weak | "Weak" | Red |
| Fair | "Fair" | Orange |
| Strong | "Strong" | Green |

Avoid numeric scores ("3/5") — they are meaningless without context.

### Requirements Display

List password requirements upfront, and check them off in real time as the user meets each one:

- "At least 8 characters" (checked/unchecked)
- "One uppercase letter" (checked/unchecked)
- "One number or symbol" (checked/unchecked)

| Do | Don't |
|---|---|
| List requirements visibly before input | Reveal requirements only after a failed attempt |
| Check off each requirement as met | "Password does not meet requirements" (which ones?) |

### Show/Hide Toggle

Label the toggle with the action it will perform:

- "Show password" (when hidden)
- "Hide password" (when visible)

Place the toggle inside or adjacent to the password field. Use an eye icon paired with the text label for both visual and accessible clarity.

### Security Context

For sensitive fields (SSN, tax ID, bank account), add helper text explaining why the data is needed and how it is protected:

- "Required for tax reporting. Encrypted and stored securely."
- "We never share your financial information with third parties."

| Do | Don't |
|---|---|
| "Encrypted and stored securely" | "Don't worry, it's safe" (vague, patronizing) |
| "Required for identity verification" | "We need this" (no reason given) |
