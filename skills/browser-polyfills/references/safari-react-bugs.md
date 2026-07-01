# Safari React and Next.js Bug Fixes

Sources: WebKit Bug Tracker, MDN Web Docs, production React/Next.js codebases (Cal.com, MUI, Vercel)

Each entry: Problem -> Cause -> Fix -> Versions affected. Focus is mobile Safari (iOS), where WebKit cannot be replaced.

---

## 1. Date Parsing

**Problem:** `new Date(string)` returns `Invalid Date` for many formats Chrome accepts. Breaks date displays, form validation, and any component rendering formatted dates.

**Cause:** Safari strictly follows the ECMAScript spec — only ISO 8601 with a `T` separator is mandated. Chrome/Firefox accept informal formats as a convenience extension.

### Formats that break in Safari

| Format | Example | Result |
|--------|---------|--------|
| Space-separated datetime | `"2024-01-15 14:30:00"` | `Invalid Date` |
| US slash format | `"01/15/2024"` | `Invalid Date` |
| Non-padded ISO | `"2024-1-5"` | `Invalid Date` (pre-iOS 26) |
| Abbreviated month | `"Jan 15, 2024"` | `Invalid Date` |
| RFC 2822 without timezone | `"Mon, 15 Jan 2024 14:30:00"` | `Invalid Date` |

### Safe formats

| Format | Example |
|--------|---------|
| ISO 8601 with T and Z | `"2024-01-15T14:30:00Z"` |
| ISO 8601 with T and offset | `"2024-01-15T14:30:00+05:30"` |
| Unix timestamp (number) | `new Date(1705329000000)` |

**WebKit PR #49500:** Fixes non-padded dates (`"2024-1-5"`) in iOS 26+. Do not rely on it — users will be on older iOS for years.

**Fix:** Replace `new Date(string)` with `parseISO` from `date-fns`.

```ts
// Bad — breaks on Safari for most server-returned strings
const date = new Date("2024-01-15 14:30:00");

// Good
import { parseISO, format } from "date-fns";
const date = parseISO("2024-01-15T14:30:00Z");

// Normalize space-separated dates from legacy APIs
const iso = rawString.replace(" ", "T");
const date = parseISO(iso);
```

**Versions affected:** All Safari. Space-separator bug never fixed. Non-padded date bug fixed iOS 26+ only.

---

## 2. Input Zoom on iOS Safari

**Problem:** Tapping any `<input>`, `<select>`, or `<textarea>` with `font-size` below 16px causes iOS Safari to zoom the entire page. The zoom persists after the keyboard closes.

**Cause:** iOS Safari zooms to ensure legibility when a form element receives focus. The threshold is exactly 16px.

**Fix:** Set `font-size: 16px` on form elements, scoped to iOS only.

```css
/* Scoped to iOS Safari — no effect on desktop */
@supports (-webkit-touch-callout: none) {
  input,
  select,
  textarea {
    font-size: 16px;
  }
}
```

For Tailwind:

```css
@layer base {
  @supports (-webkit-touch-callout: none) {
    input, select, textarea { @apply text-base; }
  }
}
```

If the design requires visually smaller inputs, use `transform: scale()` to shrink appearance while keeping the DOM font size at 16px.

Do not disable viewport zooming (`user-scalable=no`) — this breaks accessibility and violates WCAG 1.4.4.

**Versions affected:** All iOS Safari. Intentional behavior, no fix planned.

---

## 3. 100vh / Viewport Height

**Problem:** `height: 100vh` does not fill the visible screen. Browser chrome (address bar, tab bar) overlaps content, hiding elements at the bottom of `100vh` containers.

| Era | Behavior |
|-----|----------|
| Pre-iOS 15 | `100vh` = full viewport including browser chrome |
| iOS 15.4 | `dvh` unit added — `100dvh` = visible area |
| iOS 26 | Regression: `100dvh` inconsistent in some PWA contexts |

**Fix:** Layered CSS fallback.

```css
.full-height {
  height: 100vh;           /* old browsers */
  height: 100dvh;          /* iOS 15.4+ */
  height: -webkit-fill-available; /* iOS < 15.4 */
}
```

For Next.js, target `#__next` in `globals.css`:

```css
html, body, #__next { height: 100%; }
```

For JavaScript-driven layouts, use the Visual Viewport API:

```ts
function useViewportHeight() {
  const [height, setHeight] = React.useState(
    () => window.visualViewport?.height ?? window.innerHeight
  );
  React.useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const handler = () => setHeight(vv.height);
    vv.addEventListener("resize", handler);
    return () => vv.removeEventListener("resize", handler);
  }, []);
  return height;
}
```

**Versions affected:** All iOS Safari for `100vh`. `dvh` from iOS 15.4. iOS 26 regression in PWA contexts.

---

## 4. Scroll Lock

**Problem:** `overflow: hidden` on `<body>` does not prevent scrolling on iOS Safari. Modals and overlays allow the background page to scroll through them.

**Cause:** iOS uses a native momentum scrolling system that ignores `overflow: hidden` on the document root.

**Fix:** Use `position: fixed` on the body, capturing and restoring scroll position.

```ts
let scrollY = 0;

export function lockScroll(): void {
  scrollY = window.scrollY;
  document.body.style.position = "fixed";
  document.body.style.top = `-${scrollY}px`;
  document.body.style.width = "100%";
  document.body.style.overflowY = "scroll"; // prevent layout shift
}

export function unlockScroll(): void {
  document.body.style.position = "";
  document.body.style.top = "";
  document.body.style.width = "";
  document.body.style.overflowY = "";
  window.scrollTo(0, scrollY);
}

// Hook
function useScrollLock(active: boolean) {
  React.useEffect(() => {
    if (!active) return;
    lockScroll();
    return () => unlockScroll();
  }, [active]);
}
```

For scrollable content inside the modal, add `overflow-y: auto` and `overscroll-behavior: contain`.

**Versions affected:** All iOS Safari. OS-level behavior.

---

## 5. z-index / Stacking Context

**Problem:** Elements with high `z-index` appear behind other elements in Safari. Commonly breaks modals, tooltips, and sticky headers.

**Cause:** Safari requires an explicit stacking context before `z-index` takes effect. Chrome/Firefox infer stacking contexts more permissively.

**Fix:** Force a stacking context with `transform: translateZ(0)` or `isolation: isolate`.

```css
.modal-overlay {
  position: fixed;
  z-index: 1000;
  transform: translateZ(0); /* establishes stacking context */
}

.dropdown-container {
  position: relative;
  isolation: isolate;
  z-index: 50;
}
```

When debugging: check whether any ancestor has `transform`, `filter`, or `will-change` — these create new stacking contexts that cap descendant z-index values.

**Versions affected:** All Safari. Stricter than other browsers but consistent.

---

## 6. Modal Scaling When Keyboard Opens

**Problem:** When a keyboard opens inside a modal (e.g., autofocused search input), the modal shrinks, shifts, or scales on iOS Safari.

**Cause:** When the iOS keyboard opens, the viewport shrinks. Modals using `transform` for centering recalculate relative to the new viewport size, causing a visible jump.

**Fix:** Avoid `transform` on modal overlay containers. Use `position: fixed` with explicit dimensions.

```css
/* Bad — transform causes scaling when keyboard opens */
.modal { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); }

/* Good — no transform on the overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  width: min(90vw, 480px);
  max-height: 80vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
```

If you need entry animations, apply `transform` to the inner content element, not the overlay.

**Versions affected:** All iOS Safari.

---

## 7. PWA / Service Worker Limitations

**Problem:** Push notifications, background sync, and permission APIs behave differently on iOS Safari compared to Android Chrome.

| Feature | iOS Safari | Notes |
|---------|-----------|-------|
| Push notifications | iOS 16.4+ only | Requires home screen install |
| Background sync | Not supported | No timeline |
| Periodic background sync | Not supported | — |
| `Notification.permission` | iOS 16.4+ | Reliable |
| `navigator.permissions.query({ name: "notifications" })` | Unreliable | Returns `"prompt"` even when denied |

**Fix — push notification guard:**

```ts
async function requestPushPermission(): Promise<boolean> {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches;

  if (isIOS && !isStandalone) {
    showInstallPrompt(); // must be installed to home screen
    return false;
  }
  if (!("Notification" in window)) return false;
  return (await Notification.requestPermission()) === "granted";
}
```

**Fix — permission check:** Use `Notification.permission` directly, not `navigator.permissions.query`.

```ts
// Bad — returns "prompt" even when denied on iOS
const { state } = await navigator.permissions.query({ name: "notifications" });

// Good
const state = Notification.permission; // "default" | "granted" | "denied"
```

**Versions affected:** Push requires iOS 16.4+. Background sync unsupported.

---

## 8. WebSocket Connection Dropping

**Problem:** WebSocket connections close when the user switches tabs or locks their iOS device. The `close` event is not reliably fired, so reconnection logic does not trigger.

**Cause:** iOS aggressively suspends background network connections to preserve battery.

**Fix:** Server-side heartbeat with client-side reconnection.

```ts
class ReliableWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly url: string) { this.connect(); }

  private connect() {
    this.ws = new WebSocket(this.url);
    this.ws.addEventListener("message", (e) => {
      if (e.data === "ping") { this.ws?.send("pong"); return; }
      this.onMessage(e.data);
    });
    this.ws.addEventListener("close", () => this.scheduleReconnect());
    this.ws.addEventListener("error", () => this.ws?.close());
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }

  onMessage(_data: string) {}
  destroy() { if (this.reconnectTimer) clearTimeout(this.reconnectTimer); this.ws?.close(); }
}
```

The server sends `"ping"` every 25–30 seconds. If the client misses 3 pings, the server closes the connection, triggering the client's `close` event and reconnection.

**Versions affected:** All iOS Safari. OS-level behavior.

---

## 9. fetch with keepalive on Page Unload

**Problem:** `fetch` with `keepalive: true` — used to send analytics on navigation — fails silently on iOS Safari. The request is dropped.

**Cause:** Safari's `keepalive` implementation is unreliable on iOS when the page unloads.

**Fix:** Use `navigator.sendBeacon()` instead.

```ts
// Bad — keepalive unreliable on iOS Safari
window.addEventListener("pagehide", () => {
  fetch("/api/session-end", { method: "POST", keepalive: true, body: JSON.stringify({ sessionId }) });
});

// Good
window.addEventListener("pagehide", () => {
  const blob = new Blob([JSON.stringify({ sessionId })], { type: "application/json" });
  navigator.sendBeacon("/api/session-end", blob);
});
```

Use `pagehide` instead of `beforeunload` or `unload` — those events are not reliably fired on iOS Safari.

**Versions affected:** All iOS Safari for keepalive. `sendBeacon` available from iOS 11.3+.

---

## Quick Reference

| Bug | Symptom | Fix |
|-----|---------|-----|
| Date parsing | `Invalid Date`, blank date fields | `date-fns parseISO` |
| Input zoom | Page zooms on input focus | `font-size: 16px` on inputs |
| 100vh | Bottom content hidden behind browser chrome | `100dvh` + `-webkit-fill-available` |
| Scroll lock | Background scrolls through modal | `position: fixed` + capture `scrollY` |
| z-index | Modals appear behind other elements | `transform: translateZ(0)` |
| Modal + keyboard | Modal shifts when keyboard opens | No `transform` on overlay |
| PWA push | Push notifications silently fail | iOS 16.4+ + home screen required |
| WebSocket drop | Real-time features break on tab switch | Server heartbeat + reconnect |
| fetch unload | Analytics lost on navigation | `navigator.sendBeacon()` |
