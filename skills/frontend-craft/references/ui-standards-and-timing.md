# UI Standards, Timing & Responsive Rules

Sources: WCAG 2.2 spec (W3C), Apple HIG (2025), Material Design 3, Nielsen Norman Group (response times, animation), Radix UI source, StatCounter GlobalStats (2025), European Accessibility Act (2025), CSS viewport units spec

Covers: unbreakable accessibility constraints, response time thresholds, animation duration standards, easing functions, debounce/throttle values, responsive scaling formulas, common viewport sizes, density adaptation, DPR rules, spacing relationships (Gestalt proximity), minimum component widths, platform hard rules. Every rule has a concrete number and a failure mode.

> **For static component dimensions (buttons, inputs, modals, cards, avatars, icons), see `references/ui-sizing-rules.md`.** This file covers the dynamic rules — what scales, what must never break, and when things happen.

---

## Accessibility Hard Rules (Never Break)

These are legally mandated under ADA, EAA (EU, enforced June 2025), and Section 508.

### Contrast Minimums

| Context | AA Minimum | AAA Target | Notes |
|---------|-----------|------------|-------|
| Normal text (< 24px / < 18.67px bold) | **4.5:1** | 7:1 | #757575 on white = 4.6:1 (barely passes) |
| Large text (>= 24px / >= 18.67px bold) | **3:1** | 4.5:1 | |
| UI components (borders, icons, focus) | **3:1** | — | Input borders, toggle states |
| Focus indicator change-of-contrast | **3:1** | — | WCAG 2.4.13 — focused vs unfocused pixels |
| Disabled elements | Exempt | — | But aim for 3:1 for readability |
| Placeholder text | **4.5:1** | — | Most common oversight — #999 on white fails |

### Focus Indicator Requirements (WCAG 2.4.13)

| Rule | Value |
|------|-------|
| Minimum indicator area | >= 2px thick perimeter around component |
| Contrast change | >= 3:1 between focused and unfocused state |
| Not obscured | Focused element must not be hidden by sticky headers/overlays |

```css
/* Minimum compliant focus ring */
:focus-visible {
  outline: 3px solid #2563eb;
  outline-offset: 3px;
}
```

### Zoom and Reflow

| Rule | Requirement | WCAG |
|------|-------------|------|
| Text resize | Must work at **200% zoom** without loss | 1.4.4 (AA) |
| Reflow | No horizontal scroll at **320px CSS width** | 1.4.10 (AA) |
| Text spacing override | Content survives: line-height 1.5x, paragraph spacing 2x, letter-spacing 0.12x, word-spacing 0.16x — all applied simultaneously | 1.4.12 (AA) |
| Pinch-to-zoom | Never `user-scalable=no` or `maximum-scale=1` | 1.4.4 (AA) |

```html
<!-- CORRECT viewport meta -->
<meta name="viewport" content="width=device-width, initial-scale=1">
```

```css
/* Use min-height, not height — survives text spacing override */
.card { min-height: 80px; } /* not height: 80px; overflow: hidden; */
```

### Color and Interaction

| Rule | WCAG | Level |
|------|------|-------|
| Never use color as the only differentiator | 1.4.1 | A |
| Links in body text need underline OR 3:1 contrast vs surrounding text | 1.4.1 | A |
| No flashing > 3 times/second | 2.3.1 | AA |
| No keyboard traps (focus must escape any component) | 2.1.2 | A |
| Never force single orientation without justification | 1.3.4 | AA |
| Auto-playing audio/video with sound must have pause control | 2.2.2 | A |
| Respect `prefers-reduced-motion` | 2.3.3 | AAA (de facto required) |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## Response Time Thresholds

Source: Nielsen Norman Group (Miller 1968, Card 1991, Nielsen 1993, updated 2014).

| Threshold | Duration | Perception | Required Feedback |
|-----------|----------|------------|-------------------|
| Instant | <= 100ms | Direct manipulation | None |
| Fast | 100ms–1s | Noticed but flow intact | None required |
| Slow | 1s–10s | Attention at risk | Spinner or progress bar |
| Very slow | > 10s | User will switch tasks | Percent-done with ETA |

| Specific Trigger | Threshold |
|-----------------|-----------|
| Show loading spinner | Only if wait > **300ms** |
| Show progress bar | If wait > **1s** |
| Show percentage progress | If wait > **10s** |
| Mobile page abandonment | **3s** (53% leave) |
| Desktop page abandonment | **~8s** |

### Core Web Vitals (Google, 75th percentile)

| Metric | Good | Poor | Measures |
|--------|------|------|----------|
| LCP (Largest Contentful Paint) | <= **2.5s** | > 4.0s | Main content load |
| INP (Interaction to Next Paint) | <= **200ms** | > 500ms | Responsiveness |
| CLS (Cumulative Layout Shift) | <= **0.1** | > 0.25 | Visual stability |

---

## Animation Duration Standards

Source: Material Design motion spec, NNG animation research, Radix UI defaults.

### Platform Baselines

| Platform | Enter | Exit | Standard | Max |
|----------|-------|------|----------|-----|
| Desktop | 150ms | 100ms | 200ms | 300ms |
| Mobile | 225ms | 195ms | 300ms | 400ms |
| Tablet | 290ms | 255ms | 390ms | 520ms |

### Component Durations

| Component | Duration (Desktop) | Duration (Mobile) | Easing |
|-----------|-------------------|-------------------|--------|
| Button press feedback | 150ms | 200ms | ease-out |
| Hover state transition | 150ms | — | ease-out |
| Focus ring appear | 100ms | 100ms | ease-out |
| Tooltip appear (delay) | **700ms** | — | — |
| Tooltip animation | 150ms | — | ease-out |
| Dropdown open | 150ms | 225ms | ease-out |
| Dropdown close | 100ms | 195ms | ease-in |
| Modal appear | 150ms | 225ms | ease-out |
| Modal dismiss | 100ms | 195ms | ease-in |
| Page transition | 200ms | 300ms | ease-in-out |
| Toast slide in | 150ms | 225ms | ease-out |
| Toast slide out | 100ms | 195ms | ease-in |
| Accordion expand | 200ms | 300ms | ease-out |
| Toggle switch | 200ms | 200ms | ease-in-out |
| Tab indicator slide | 200ms | 200ms | ease-in-out |
| Drawer open | 250ms | 300ms | ease-out |
| Drawer close | 200ms | 250ms | ease-in |
| Skeleton shimmer cycle | 1500ms | 1500ms | ease-in-out (loop) |

**The 300ms minimum rule:** If a request resolves in < 300ms, suppress the loading indicator entirely. If 300ms–1s, show it but hold for the full 300ms to avoid a jarring flash.

### Easing Functions

| Name | Use | CSS cubic-bezier |
|------|-----|-----------------|
| **Ease-out** (decelerate) | Elements entering | `cubic-bezier(0.0, 0.0, 0.2, 1)` |
| **Ease-in** (accelerate) | Elements leaving | `cubic-bezier(0.4, 0.0, 1.0, 1)` |
| **Ease-in-out** (standard) | Elements moving on screen | `cubic-bezier(0.4, 0.0, 0.2, 1)` |
| **Sharp** | Quick exit, may return | `cubic-bezier(0.4, 0.0, 0.6, 1)` |
| **Spring** | Interactive bounce | `cubic-bezier(0.34, 1.56, 0.64, 1)` |

**Rule:** Entering = ease-out. Exiting = ease-in. Moving = ease-in-out. Interactive = spring.

---

## Debounce & Throttle Values

| Event | Pattern | Value |
|-------|---------|-------|
| Search input | Debounce | **300ms** |
| Search (expensive API) | Debounce | 500ms |
| Form validation (inline) | Debounce | **500ms** |
| Auto-save (document) | Debounce | **1000ms** |
| Window resize | Throttle | **100ms** |
| Scroll handler | Throttle | **100ms** |
| Scroll (animation/parallax) | rAF | 16ms |
| Mouse move | Throttle | 16ms (rAF) |
| Double-click prevention | Debounce | **500ms** |

---

## Notification Auto-Dismiss

| Type | Auto-dismiss | Duration |
|------|-------------|----------|
| Success toast | Yes | **4000ms** |
| Info toast | Yes | **4000ms** |
| Warning toast | Yes | **6000ms** |
| Error toast (non-critical) | Yes | **6000ms** |
| Error toast (critical) | **No** | Persistent — require explicit dismiss |
| Undo snackbar | Yes | **5000ms** |

### Session Timeouts

| Context | Timeout | Warning at |
|---------|---------|-----------|
| Banking/healthcare | 15 min | 2 min before |
| General SaaS | 30–60 min | 2 min before |
| API request (client) | 30s | — |
| Optimistic update revert | 5s | — |

---

## Responsive Scaling

### Common Viewport Widths (CSS px, 2025)

| Device | Width | DPR |
|--------|-------|-----|
| iPhone SE / 13 Mini | 375px | 2–3x |
| **iPhone 14/15** | **390–393px** | **3x** |
| iPhone Plus/Pro Max | 430px | 3x |
| Mid-range Android | 360–393px | 2–3x |
| Large Android (Galaxy S) | 412px | 2.6x |
| iPad Mini | 744px | 2x |
| iPad Air/Pro 11" | 820px | 2x |
| iPad Pro 12.9" | 1024px | 2x |
| Budget laptop | 1366px | 1x |
| **Standard desktop** | **1920px** | **1x** |
| MacBook Pro 14" | 1512px | 2x |
| 4K monitor | 1920px | 2x |

**Design floor: 375px. Design target: 390px mobile, 1440px desktop.**

### Fluid Scaling with clamp()

```css
/* Font: scales 16px→18px between 375px→1440px viewport */
body { font-size: clamp(1rem, 0.4vw + 0.9rem, 1.125rem); }

/* Hero heading: 32px→56px */
.hero-title { font-size: clamp(2rem, 4vw + 0.8rem, 3.5rem); }

/* Section padding: 48px→96px */
.section { padding-block: clamp(3rem, 8vw, 6rem); }

/* Container padding: 16px→48px */
.container { padding-inline: clamp(1rem, 5vw, 3rem); }

/* Container width */
.container { width: min(1280px, 100% - clamp(32px, 5vw, 96px)); margin-inline: auto; }
```

### Viewport Units

| Goal | Unit | Reason |
|------|------|--------|
| Hero height | `min-height: 100dvh` | Tracks visible area as mobile toolbar collapses |
| Login screen | `min-height: 100svh` | Conservative — never hidden by browser chrome |
| Modal max height | `max-height: 85dvh` | Stay within visible area |
| Full-bleed width | `width: 100%` | NOT `100vw` — avoids scrollbar overflow on Windows |

```css
.hero {
  min-height: 100vh;   /* fallback */
  min-height: 100dvh;  /* modern */
}
```

### Breakpoint Behavior Rules

**< 768px (mobile):**
- Navigation: bottom tab bar or hamburger
- Tables: horizontal scroll or card view
- Modals: full-screen bottom sheet
- Tooltips: tap-to-reveal (no hover)
- Layout: single column
- Sidebar: hidden (drawer)

**768–1023px (tablet):**
- Navigation: rail or collapsible sidebar
- Two-column layouts viable
- Modals: centered sheet (not full-screen)
- Touch targets still >= 44px

**>= 1024px (desktop):**
- Persistent navigation
- Hover states active
- Dense data tables viable
- Multi-panel layouts

### Grid Column Rules (Material Design 3)

| Viewport | Columns | Gutter | Margin |
|----------|---------|--------|--------|
| 0–599px | 4 | 16px | 16px |
| 600–904px | 8 | 16px | 32px |
| 905–1239px | 12 | 24px | auto |
| 1240px+ | 12 | 24px | auto (max 1440px) |

### Density Adaptation

| Mode | Button Height | Use |
|------|--------------|-----|
| Spacious | 48px | Marketing, onboarding |
| Default | 40px | General apps |
| Compact | 36px | Power users, data-heavy |
| Dense | 32px | Dashboards, tables |

Never auto-compact on mobile — always comfortable/spacious on touch.

### DPR (Device Pixel Ratio) Rules

- Always provide **2x images minimum**, 3x for hero/product
- Cap canvas DPR at 2 for performance (3x doubles pixel count with minimal visible gain)
- Use SVG for all icons — resolution-independent, no DPR handling needed
- Hairline borders: `0.5px` on 2x screens, `0.333px` on 3x

```css
@media (min-resolution: 2dppx) {
  .hairline { border-width: 0.5px; }
}
```

---

## Spacing Relationships (Gestalt Proximity)

### The 1:2 Rule

```
Space within a group  :  Space between groups  =  1 : 2
```

| Relationship | Spacing |
|-------------|---------|
| Label to its input | 4–8px |
| Input to next label | 16–24px |
| Form group to form group | 32–48px |
| Nav items within group | 4–8px |
| Between nav groups | 16–24px |

### Heading Margin Rule (2:1 Above/Below)

Headings belong to content *below* them. More space above signals new section.

| Element | Margin Top | Margin Bottom |
|---------|-----------|--------------|
| H1 | 0 (page top) | 0.75em |
| H2 | 2em | 0.75em |
| H3 | 1.5em | 0.5em |
| H4 | 1.25em | 0.5em |
| Paragraph | 0 | 1em |

### Card Padding Rule

Card internal padding >= gap between cards in the grid. If cards have 16px gap, internal padding >= 16px.

---

## Minimum Component Widths

| Component | Minimum | Notes |
|-----------|---------|-------|
| Button | **80px** | Below this, labels feel cramped |
| Icon button | **40x40px** | Touch target |
| Input (generic) | **160px** | Usable but tight |
| Input (name) | **200px** | Fits "Christopher" |
| Input (email) | **240px** | Fits most addresses |
| Input (phone) | **160px** | 10-digit format |
| Input (address) | **280px** | Street address |
| Input (zip/postal) | **100px** | 5-digit zip |
| Input (credit card) | **200px** | 16 digits + spaces |
| Dropdown/select | **120px** | Minimum for options |
| Modal (mobile) | **320px** | Mobile minimum |
| Modal (desktop) | **480px** | Standard |
| Card | **280px** | Below this content breaks |
| Text column | **280px** (~35ch) | Minimum readable |
| Text column (optimal) | **520–640px** (~65ch) | Sweet spot |

**Match input width to expected content** — uniform-width inputs signal "I don't know what you'll type."

---

## Platform Hard Rules

### iOS

| Rule | Requirement |
|------|-------------|
| Safe area insets | Must use `env(safe-area-inset-*)` |
| Dynamic Type | Body text must scale with system font size |
| Touch target | >= 44x44pt (App Store rejection if violated) |
| Status bar | Never place interactive content underneath |
| Home indicator zone | Never obscure with persistent UI (34pt) |

### Android

| Rule | Requirement |
|------|-------------|
| Touch target | >= 48x48dp |
| Edge-to-edge | Content must draw behind system bars (API 35+) |
| Target spacing | >= 8dp between adjacent targets |

---

## Quick-Reference Cheat Sheet

```
ACCESSIBILITY
  Text contrast:      >= 4.5:1 (normal), >= 3:1 (large/UI)
  Focus indicator:    3px ring, 3:1 change-contrast
  Touch target:       >= 44px (Apple), >= 48dp (Material)
  Zoom support:       Must work at 200%
  Reflow:             No h-scroll at 320px width
  Color alone:        Never the only differentiator
  Flash limit:        Never > 3 flashes/sec
  Reduced motion:     Always respect prefers-reduced-motion

TIMING
  Instant:            <= 100ms (no feedback)
  Show spinner:       Only after 300ms wait
  Show progress bar:  After 1s wait
  Show percentage:    After 10s wait
  Mobile abandonment: 3s

ANIMATION (Desktop)
  Hover/focus:   100–150ms  ease-out
  Dropdown:      150ms      ease-out (open), 100ms ease-in (close)
  Modal:         150ms      ease-out (open), 100ms ease-in (close)
  Page:          200ms      ease-in-out
  Toggle:        200ms      ease-in-out

DEBOUNCE
  Search: 300ms   Validation: 500ms   Auto-save: 1000ms
  Scroll/resize: 100ms (throttle)

TOASTS
  Success/Info: 4s   Warning/Error: 6s   Critical: never auto-dismiss
  Undo window: 5s

RESPONSIVE
  Mobile floor:    375px CSS width
  Desktop target:  1440px design, 1280px max-content
  Hero height:     100dvh (with 100vh fallback)
  Modal max:       85dvh height, min(90vw, 640px) width
  Images:          Always 2x minimum srcset
```
