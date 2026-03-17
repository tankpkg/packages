# Responsive Design, Interaction Patterns & UX Writing

Sources: Krug (Don't Make Me Think), Wroblewski (Mobile First), WCAG 2.2, MDN Web Docs, Nielsen Norman Group research

Covers: mobile-first CSS, content-driven breakpoints, input method detection, safe areas, responsive images, layout adaptation, interactive states, focus management, form design, native dialog/popover, keyboard navigation, UX writing patterns, error messages, empty states, voice/tone, accessibility writing, translation planning.

---

## Responsive Design

### Mobile-First: The Right Direction

Mobile-first means writing base styles for the smallest viewport, then layering complexity upward with `min-width` queries. Desktop-first with `max-width` forces mobile browsers to download and parse styles they immediately override. Mobile-first also forces prioritization: when you can only show three things, you discover which three actually matter.

```css
/* Base is mobile; complexity added upward */
.card { display: block; padding: 1rem; }

@media (min-width: 640px) {
  .card { display: flex; padding: 1.5rem; }
}

@media (min-width: 1024px) {
  .card { padding: 2rem; gap: 2rem; }
}
```

### Content-Driven Breakpoints

Don't chase device sizes — let content dictate where to break. Resize the browser until the layout looks wrong, then add a breakpoint there. Three breakpoints usually suffice: `640px`, `768px`, `1024px`. Avoid breakpoints entirely for fluid values using `clamp()`.

```css
h1 { font-size: clamp(1.5rem, 4vw + 0.5rem, 3rem); }

.container {
  padding-inline: clamp(1rem, 5vw, 3rem);
  max-width: clamp(320px, 90vw, 1200px);
}
```

### Detect Input Method, Not Screen Size

Screen size does not tell you how someone is interacting. Laptops have touchscreens. Tablets have keyboards. Use media features that describe the actual input device.

| Media Feature | Values | Meaning |
|---------------|--------|---------|
| `pointer: fine` | Mouse, trackpad, stylus | Precise — small targets OK |
| `pointer: coarse` | Finger touch | Imprecise — needs 44×44px minimum |
| `hover: hover` | Mouse, trackpad | Hover states are reliable |
| `hover: none` | Touch, game controllers | Hover states are invisible |

```css
/* Base: touch-friendly */
.btn { min-height: 44px; padding: 0.75rem 1.25rem; }

@media (pointer: fine) {
  .btn { min-height: 32px; padding: 0.5rem 1rem; }
}

/* Only add hover effects when hover is reliable */
@media (hover: hover) {
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
  }
}
```

### Safe Areas (Notch and Home Indicator)

Enable `viewport-fit=cover` in the meta tag, then use `env(safe-area-inset-*)`. Wrap in `max()` to preserve minimum padding on devices without safe areas.

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

```css
.footer-nav {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
  padding-left: max(1rem, env(safe-area-inset-left));
  padding-right: max(1rem, env(safe-area-inset-right));
}
```

### Responsive Images

`srcset` with width descriptors tells the browser which file to use. The `sizes` attribute tells it how wide the image renders — without it, the browser assumes 100vw and downloads unnecessarily large files. Use `<picture>` when the crop or composition changes between viewports, not just the resolution.

```html
<!-- Resolution switching -->
<img
  src="hero-800.jpg"
  srcset="hero-400.jpg 400w, hero-800.jpg 800w, hero-1600.jpg 1600w"
  sizes="(min-width: 1024px) 50vw, (min-width: 640px) 75vw, 100vw"
  alt="Team working in the office"
  loading="lazy"
>

<!-- Art direction: different crops per viewport -->
<picture>
  <source media="(min-width: 768px)" srcset="hero-wide.jpg">
  <source media="(max-width: 767px)" srcset="hero-square.jpg">
  <img src="hero-wide.jpg" alt="Team working in the office">
</picture>
```

### Layout Adaptation Patterns

**Navigation stages** — match navigation complexity to available space:

| Viewport | Pattern |
|----------|---------|
| Mobile | Hamburger + off-canvas drawer (`<dialog>` or fixed overlay) |
| Tablet | Horizontal compact — icons only or short labels |
| Desktop | Full horizontal with labels and secondary actions |

**Tables on mobile** — convert to card-style stacked rows using `display: block` and `data-label` attributes:

```css
@media (max-width: 639px) {
  table, thead, tbody, tr, th, td { display: block; }
  thead tr { position: absolute; top: -9999px; left: -9999px; }
  td { padding-left: 50%; position: relative; }
  td::before { content: attr(data-label); position: absolute; left: 0.75rem; font-weight: 600; }
}
```

**Progressive disclosure** — use `<details>/<summary>` for secondary content. No JavaScript, accessible by default, collapses on mobile without hiding on desktop.

### Testing Reality

DevTools device emulation misses: actual touch feel, real CPU/memory constraints, network latency, font rendering differences, browser chrome consuming viewport height, and battery-saving CPU throttling. Test on at least one real iPhone and one real Android. A cheap mid-range Android (under $200) reveals performance issues invisible in simulators and on flagship devices.

---

## Interaction Patterns

### The Eight Interactive States

Every interactive element needs all eight states designed. The most common miss: designing hover without designing focus — keyboard users never see hover states.

| State | When It Applies | Visual Treatment |
|-------|----------------|-----------------|
| Default | Resting | Base style |
| Hover | Mouse over element | Subtle lift, color shift, cursor change |
| Focus | Keyboard or programmatic focus | Visible ring (see below) |
| Active | Being pressed | Scale down, color darken |
| Disabled | Action unavailable | 50–60% opacity, `not-allowed` cursor |
| Loading | Async action in progress | Spinner or skeleton, prevent re-click |
| Error | Validation or action failed | Red border/text, error message |
| Success | Action completed | Green confirmation, brief then resolves |

### Focus Rings Done Right

Never use `outline: none` without a replacement. Use `:focus-visible` to show rings only for keyboard navigation — mouse clicks won't trigger it. WCAG 2.2 requires 3:1 contrast, at least 2px thick, offset from the element.

```css
:focus { outline: none; }

:focus-visible {
  outline: 3px solid #2563eb;
  outline-offset: 3px;
  border-radius: 4px;
}

@media (prefers-color-scheme: dark) {
  :focus-visible { outline-color: #60a5fa; }
}

@media (forced-colors: active) {
  :focus-visible { outline: 3px solid ButtonText; }
}
```

### Form Design

**Placeholders are not labels.** Placeholder text disappears when typing, leaving users unable to verify what a field is for. Always use a visible `<label>` associated via `for`/`id`.

**Validate on blur, not on keystroke.** Showing errors while someone is still typing is aggressive. Exception: password strength meters, which provide real-time guidance users expect.

**Error placement:** errors belong below the field they describe. Connect with `aria-describedby` so screen readers announce the error when the field receives focus.

```html
<div class="field">
  <label for="email">Email address</label>
  <input type="email" id="email" aria-describedby="email-error" aria-invalid="true">
  <p id="email-error" class="error-text" role="alert">
    Enter a valid email address (example@domain.com)
  </p>
</div>
```

### Native `<dialog>` and the `inert` Attribute

The native `<dialog>` element provides a built-in focus trap, Escape key to close, and correct ARIA role. Use `showModal()` for modal behavior. Apply `inert` to background content to prevent focus and pointer events from reaching it.

```js
const dialog = document.getElementById('confirm-dialog');
const main = document.getElementById('main-content');

function openDialog() {
  main.inert = true;
  dialog.showModal();
}

dialog.addEventListener('close', () => { main.inert = false; });
```

### Popover API

The Popover API handles tooltips, dropdowns, and menus without z-index management. It renders in the top layer, light-dismisses on outside click, and is accessible by default.

```html
<button popovertarget="user-menu">Account</button>

<div id="user-menu" popover>
  <a href="/profile">Profile</a>
  <a href="/settings">Settings</a>
</div>
```

No JavaScript required for basic open/close. Add `popover="manual"` to disable light-dismiss when you need explicit control.

### Destructive Actions — Undo Beats Confirm

Users click through confirmation dialogs mindlessly. The undo pattern is more effective: remove the item from the UI immediately, show a toast with an undo action, then actually delete after the toast expires (5–7 seconds).

| Pattern | When to Use | Example |
|---------|-------------|---------|
| Undo toast | Reversible within session | Archive email, delete draft |
| Confirmation dialog | Irreversible or high-cost | Delete account, publish to production |
| Typed confirmation | Catastrophic, no recovery | Delete workspace, drop database |

### Keyboard Navigation — Roving Tabindex

For component groups (tab bars, radio groups, toolbars), only one item should be in the tab order at a time. Arrow keys move focus within the group. Tab moves to the next component entirely.

```js
class TabGroup {
  constructor(container) {
    this.tabs = Array.from(container.querySelectorAll('[role="tab"]'));
    this.currentIndex = 0;
    this.tabs[0].tabIndex = 0;
    this.tabs.slice(1).forEach(tab => (tab.tabIndex = -1));
    container.addEventListener('keydown', e => this.handleKey(e));
  }

  handleKey(e) {
    const dir = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (dir === undefined) return;
    e.preventDefault();
    this.moveTo((this.currentIndex + dir + this.tabs.length) % this.tabs.length);
  }

  moveTo(index) {
    this.tabs[this.currentIndex].tabIndex = -1;
    this.currentIndex = index;
    this.tabs[index].tabIndex = 0;
    this.tabs[index].focus();
  }
}
```

### Skip Links

Place a visually hidden link as the first focusable element in the document. Show it on focus so keyboard users can bypass navigation.

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<nav>...</nav>
<main id="main-content">...</main>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 1rem;
  padding: 0.5rem 1rem;
  background: #1e293b;
  color: white;
  border-radius: 0 0 4px 4px;
  z-index: 9999;
}
.skip-link:focus { top: 0; }
```

### Gesture Discoverability

Swipe-to-delete and long-press are invisible interactions. Three strategies: (1) **partial reveal** — show a sliver of the action behind the item on load, then snap back; (2) **coach marks** — on first use only, show an animated hint, store completion in `localStorage`; (3) **visible fallback** — always provide a non-gesture path (three-dot menu, explicit button). Gestures are shortcuts, not the only path.

---

## UX Writing

### Button Labels — Verb + Object Pattern

Button labels should describe the action and its target. Generic labels force users to re-read surrounding context.

| Avoid | Use Instead | Why |
|-------|-------------|-----|
| OK | Save changes | Describes what is saved |
| Submit | Create account | Names the outcome |
| Yes | Delete message | Confirms the specific action |
| Cancel | Keep editing | Describes what the user keeps |
| Click here | Download PDF | Describes action and format |
| Continue | Next: Shipping | Shows progress and destination |

For destructive actions, include the count: "Delete 5 items" not "Delete selected" — users need to know the scope before confirming.

### Error Message Formula

Every error answers three questions: (1) What happened? (2) Why? (3) How to fix it? Never blame the user. Never use technical jargon.

| Situation | Template | Example |
|-----------|----------|---------|
| Format error | "[Field] must be [format]" | "Phone number must include area code" |
| Missing required | "Enter your [field]" | "Enter your billing address" |
| Permission denied | "You don't have permission to [action]. [How to get it]." | "Ask an admin to grant access." |
| Network error | "Couldn't [action]. Check your connection and try again." | — |
| Server error | "Something went wrong. Try again in a moment." | — |
| Conflict | "[Item] already exists. [Resolution]." | "That username is taken. Try adding numbers." |

### Empty States as Opportunities

Three-part structure: briefly acknowledge the empty state, explain the value of filling it, provide one clear action.

| Type | Tone | Action |
|------|------|--------|
| First-use (never had data) | Welcoming | Primary CTA to create first item |
| No results (search/filter) | Neutral, helpful | Clear filters or broaden search |
| Cleared (user deleted everything) | Neutral | Undo or create new |
| Error prevented load | Apologetic | Retry button |

Avoid: clipart with no meaning, generic "Nothing here yet" with no guidance, or empty states that look like broken pages.

### Voice vs Tone

Voice is the brand's consistent personality. Tone adapts to the emotional context of the moment.

| Moment | Tone | Example |
|--------|------|---------|
| Success / completion | Celebratory, brief | "You're all set!" / "Invoice sent." |
| Error / failure | Empathetic, helpful | "We couldn't process that. Here's what to try." |
| Loading / waiting | Reassuring, specific | "Uploading your file…" not "Loading…" |
| Destructive confirmation | Serious, clear | "This will permanently delete your account." |
| Onboarding | Encouraging, low-pressure | "Nothing is permanent yet — take a look around." |

Never use humor for errors. Users who are frustrated do not find jokes helpful.

### Writing for Accessibility

Link text must make sense out of context — screen reader users often navigate by listing all links on a page.

| Avoid | Use Instead |
|-------|-------------|
| Click here | View pricing plans |
| Read more | Read more about our refund policy |
| Download | Download the Q3 report (PDF, 2.4 MB) |

Alt text describes information, not the image. For charts: "Revenue increased 40% from Q1 to Q4" not "Bar chart". For decorative images, use `alt=""`. For icon-only buttons, use `aria-label`.

```html
<img src="chart.png" alt="Revenue increased 40% from Q1 to Q4 2024">
<img src="divider.svg" alt="">

<button aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false">...</svg>
</button>
```

### Translation Planning

UI strings expand and contract when translated. Designs that fit English perfectly will break in German or Finnish.

| Language | Typical Expansion | Notes |
|----------|-------------------|-------|
| German | +30% | Compound nouns, long words |
| French | +20% | Articles, gendered nouns |
| Finnish | +30–40% | Agglutinative, very long words |
| Spanish | +20–25% | Articles, longer verb forms |
| Chinese (Simplified) | −30% characters | Same rendered width due to larger glyphs |

Rules that prevent translation bugs:
- **Keep numbers separate from strings.** Use ICU message format: `{count, plural, one {# item} other {# items}}`.
- **Full sentences as single strings.** Never concatenate — word order varies by language.
- **Avoid abbreviations.** "Jan", "Tue" don't translate cleanly. Use locale-aware date APIs.
- **Leave 30–40% extra space** in buttons, nav items, and table headers.

### Terminology Consistency

Pick one term per concept and use it everywhere — UI labels, error messages, documentation, support content.

| Inconsistent Terms | Chosen Term | Rationale |
|--------------------|-------------|-----------|
| Delete / Remove / Trash | Delete | Most universally understood as permanent |
| Settings / Preferences / Options | Settings | Matches OS conventions |
| Sign in / Log in / Login | Sign in | Matches Apple/Google convention |
| Create / Add / New | Create | Implies bringing something into existence |
| Edit / Modify / Update | Edit | Shortest, most familiar |

Document chosen terms in a shared glossary. Include the terms to avoid so writers don't accidentally reintroduce inconsistency.
