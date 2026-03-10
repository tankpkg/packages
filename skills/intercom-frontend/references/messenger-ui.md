# Messenger UI Customization

Sources: Intercom Developer Documentation, Intercom Messenger Customization Guide

Covers: custom launcher patterns, hiding default launcher, positioning, theming, z-index management, responsive behavior, notification control.

For complete boot settings, see `references/js-api-reference.md`. For framework-specific provider patterns, see `references/framework-integration.md`.

## Custom Launcher Patterns

Three approaches exist for replacing or augmenting the default launcher bubble. Choose based on how much control you need over click behavior and badge display.

### A. CSS Selector Approach

Pass a CSS selector string to `custom_launcher_selector` during boot. Intercom attaches its own click handler to the matched element automatically. Combine with `hide_default_launcher: true` to suppress the default bubble.

```javascript
Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  custom_launcher_selector: '#open-chat',
  hide_default_launcher: true,
});
```

```html
<button id="open-chat">Chat with us</button>
```

Intercom re-queries the selector after each `update()` call, so elements rendered after boot are picked up as long as they match the selector at the time of the next update. Use a stable, unique selector — class selectors work but are more fragile if class names change.

### B. Programmatic Approach

Hide the default launcher and call `Intercom('show')` directly from your button's event handler. This gives full control: you can conditionally open the messenger, log analytics events, or delay the open until some condition is met.

```javascript
Intercom('boot', { app_id: 'YOUR_APP_ID', hide_default_launcher: true });

document.getElementById('open-chat').addEventListener('click', () => {
  Intercom('show');
});
```

Use this approach when you need to run logic before opening (e.g., check authentication state, fire an analytics event, or open to a specific space rather than the default home).

### C. Hybrid Approach with Unread Badge

Use `custom_launcher_selector` for automatic click handling and `onUnreadCountChange` to drive a badge counter on the same element.

```javascript
Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  custom_launcher_selector: '#chat-launcher',
  hide_default_launcher: true,
});

Intercom('onUnreadCountChange', (count) => {
  const badge = document.getElementById('chat-badge');
  badge.textContent = count > 99 ? '99+' : String(count);
  badge.style.display = count > 0 ? 'flex' : 'none';
});
```

```html
<button id="chat-launcher" style="position: relative;">
  Chat
  <span id="chat-badge" style="
    display: none; position: absolute; top: -6px; right: -6px;
    background: #e74c3c; color: white; border-radius: 50%;
    width: 18px; height: 18px; font-size: 11px;
    align-items: center; justify-content: center;
  "></span>
</button>
```

`onUnreadCountChange` fires immediately on registration with the current unread count, then fires again on every subsequent change. Initialize badge state in the callback rather than assuming zero at boot.

## Hiding the Default Launcher

Set `hide_default_launcher: true` in the boot call to suppress the default bubble. Toggle after boot with `update()`:

```javascript
Intercom('update', { hide_default_launcher: true });  // hide
Intercom('update', { hide_default_launcher: false }); // show
```

Setting `hide_default_launcher: false` explicitly forces the launcher visible, overriding any visibility settings configured in the Intercom dashboard. If you want the dashboard to control launcher visibility, omit the property entirely rather than setting it to `false`. Only set it explicitly when your code owns the visibility decision.

## Positioning

| Property | Type | Default | Description |
|---|---|---|---|
| `alignment` | `'left'` or `'right'` | `'right'` | Which side of the viewport the launcher anchors to |
| `horizontal_padding` | number (px) | 20 | Distance from the aligned edge; minimum 20 |
| `vertical_padding` | number (px) | 20 | Distance from the bottom of the viewport; minimum 20 |

```javascript
Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  alignment: 'left',
  horizontal_padding: 32,
  vertical_padding: 80,
});
```

Update positioning dynamically — for example, to move the launcher above a cookie banner that appears after boot:

```javascript
function showCookieBanner() {
  renderCookieBanner();
  Intercom('update', { vertical_padding: 120 });
}

function dismissCookieBanner() {
  removeCookieBanner();
  Intercom('update', { vertical_padding: 20 });
}
```

`horizontal_padding` and `vertical_padding` have no effect on mobile viewports. On mobile, the messenger opens full-screen and the launcher renders at a fixed position. Do not rely on padding values for mobile layout — use a custom launcher instead (see Responsive Behavior section).

## Z-Index Management

Set `z_index` in boot or via `update()` to control stacking order:

```javascript
Intercom('boot', { app_id: 'YOUR_APP_ID', z_index: 9999 });
```

The default z-index is approximately `2147483000` — near the maximum integer value for CSS z-index.

If your application has modals or overlays that must appear above the messenger, set `z_index` to a value below your overlay's z-index:

```javascript
// Your modal uses z-index: 10000 — set messenger below it
Intercom('update', { z_index: 9000 });
// When modal closes, restore
Intercom('update', { z_index: 2147483000 });
```

If a third-party library raises its own elements to a very high z-index and covers the messenger, set `z_index` explicitly above the offending element. Avoid using `2147483647` (the CSS maximum) unless necessary — it can cause rendering issues in some browsers.

## Theming and Colors

| Property | Values | Description |
|---|---|---|
| `action_color` | CSS hex or rgb string | Color for buttons, links, and CTAs inside the messenger |
| `background_color` | CSS hex or rgb string | Color for the team profile header area |
| `theme_mode` | `'light'`, `'dark'`, `'system'` | Light/dark mode; `'system'` follows OS preference |

Set at boot:

```javascript
Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  action_color: '#6366f1',
  background_color: '#1e1b4b',
  theme_mode: 'system',
});
```

All three properties can be changed dynamically with `update()`. Use this to synchronize the messenger with your application's own theme toggle:

```javascript
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  Intercom('update', {
    theme_mode: theme === 'dark' ? 'dark' : 'light',
    action_color: theme === 'dark' ? '#818cf8' : '#6366f1',
    background_color: theme === 'dark' ? '#1e1b4b' : '#eef2ff',
  });
}
```

`theme_mode: 'system'` reads `prefers-color-scheme` from the OS. If your app manages its own theme state independently of the OS preference, use `'light'` or `'dark'` explicitly and drive it from your app's theme state rather than relying on `'system'`.

## Responsive Behavior

On mobile viewports (typically below 768px), the Intercom messenger opens full-screen. The launcher bubble still appears, but `horizontal_padding` and `vertical_padding` are ignored.

Recommended pattern: detect the mobile viewport, hide the default launcher, and render a custom launcher positioned to fit your mobile layout.

```javascript
function setupIntercomForViewport() {
  const isMobile = window.matchMedia('(max-width: 767px)').matches;
  Intercom('update', { hide_default_launcher: isMobile });
}

setupIntercomForViewport();
window.matchMedia('(max-width: 767px)').addEventListener('change', setupIntercomForViewport);
```

On mobile, pair this with a custom launcher element that fits your mobile navigation — for example, a bottom navigation bar item:

```html
<nav class="bottom-nav">
  <button class="nav-item" id="mobile-chat-launcher">
    Support
    <span id="mobile-chat-badge" style="display: none;"></span>
  </button>
</nav>
```

```javascript
Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  custom_launcher_selector: '#mobile-chat-launcher',
  hide_default_launcher: true,
});
```

To restore the default launcher on desktop, you must explicitly set `hide_default_launcher: false` — omitting the property does not reset it.

## Notification Control

`hideNotifications` suppresses in-app notification badges and message popups without closing the messenger or affecting unread counts:

```javascript
Intercom('hideNotifications', true);  // suppress notifications
Intercom('hideNotifications', false); // restore notifications
```

Use this when the user enters a focused mode where notification popups would be disruptive:

```javascript
// Video call or screen share
function enterFocusMode() {
  Intercom('hideNotifications', true);
}

function exitFocusMode() {
  Intercom('hideNotifications', false);
}

// Presentation / fullscreen mode
document.addEventListener('fullscreenchange', () => {
  Intercom('hideNotifications', !!document.fullscreenElement);
});
```

`hideNotifications` does not affect the unread count returned by `onUnreadCountChange` — messages still accumulate, they just do not surface as popups. When notifications are re-enabled, any accumulated messages become visible.

## Showing Specific Spaces

`showSpace` opens the messenger to a specific section:

```javascript
Intercom('showSpace', 'home');      // default home screen
Intercom('showSpace', 'messages');  // conversation list
Intercom('showSpace', 'help');      // help center / articles
Intercom('showSpace', 'news');      // news feed
Intercom('showSpace', 'tasks');     // task center
Intercom('showSpace', 'tickets');   // tickets list
```

Each space must be enabled in your Intercom workspace settings. Calling `showSpace` with a disabled space falls back to the home screen.

Use `showSpace` to create contextual entry points throughout your application:

```javascript
// Footer help link
document.getElementById('help-link').addEventListener('click', (e) => {
  e.preventDefault();
  Intercom('showSpace', 'help');
});

// Navigation messages link
document.getElementById('nav-messages').addEventListener('click', (e) => {
  e.preventDefault();
  Intercom('showSpace', 'messages');
});

// Sidebar task center
document.getElementById('task-center-btn').addEventListener('click', () => {
  Intercom('showSpace', 'tasks');
});
```

## Pre-populated Messages

`showNewMessage` opens the new message composer with pre-filled text:

```javascript
Intercom('showNewMessage');                              // empty composer
Intercom('showNewMessage', 'I need help with billing'); // pre-filled
```

Requires Inbox Essential or Pro plan. Use for contextual help buttons where the user's intent is already known:

```javascript
// Bug report button on a specific feature
document.getElementById('report-bug').addEventListener('click', () => {
  const page = window.location.pathname;
  const feature = document.querySelector('[data-feature]')?.dataset.feature;
  Intercom('showNewMessage', `Bug report — Page: ${page}, Feature: ${feature}\n\n`);
});

// Billing help button
document.getElementById('billing-help').addEventListener('click', () => {
  Intercom('showNewMessage', 'I have a question about my billing.');
});
```

The pre-filled text is editable by the user before sending. Include a trailing newline or space to position the cursor after the pre-filled content.

## Conditional Visibility by Page

In single-page applications, show or hide the messenger launcher based on the current route. Update visibility on every route change rather than only at boot.

**React Router pattern**:

```javascript
const MESSENGER_HIDDEN_ROUTES = ['/onboarding', '/checkout', '/presentation'];

function useIntercomVisibility() {
  const location = useLocation();
  useEffect(() => {
    const hidden = MESSENGER_HIDDEN_ROUTES.some((route) =>
      location.pathname.startsWith(route)
    );
    Intercom('update', { hide_default_launcher: hidden });
  }, [location.pathname]);
}
```

**Vanilla SPA pattern** (history API):

```javascript
const HIDDEN_PATHS = ['/onboarding', '/checkout'];

function updateIntercomVisibility() {
  const hidden = HIDDEN_PATHS.some((path) =>
    window.location.pathname.startsWith(path)
  );
  Intercom('update', { hide_default_launcher: hidden });
}

const originalPushState = history.pushState.bind(history);
history.pushState = (...args) => { originalPushState(...args); updateIntercomVisibility(); };
window.addEventListener('popstate', updateIntercomVisibility);
updateIntercomVisibility();
```

Prefer `update()` for route-based visibility changes over conditionally rendering the `IntercomProvider` — the latter triggers a full shutdown and re-boot on each route change, resetting conversation state and firing additional API calls.

## Unread Count Badge

`onUnreadCountChange` registers a callback that fires with the current unread message count immediately on registration, then on every subsequent change:

```javascript
// Update browser tab title
Intercom('onUnreadCountChange', (count) => {
  document.title = count > 0 ? `(${count}) My App` : 'My App';
});

// Update navigation badge
Intercom('onUnreadCountChange', (count) => {
  const badge = document.getElementById('nav-support-badge');
  if (!badge) return;
  badge.textContent = count > 9 ? '9+' : String(count);
  badge.setAttribute('aria-label', `${count} unread support messages`);
  badge.style.display = count > 0 ? 'inline-flex' : 'none';
});
```

Register `onUnreadCountChange` after boot. In React, register it inside a `useEffect` that runs after the Intercom boot effect.

## Summary: Property Reference

| Property | Set via | Effect |
|---|---|---|
| `custom_launcher_selector` | boot, update | CSS selector for custom launcher element |
| `hide_default_launcher` | boot, update | Show/hide default bubble; omit for dashboard control |
| `alignment` | boot, update | `'left'` or `'right'` |
| `horizontal_padding` | boot, update | px from aligned edge (desktop only) |
| `vertical_padding` | boot, update | px from bottom (desktop only) |
| `z_index` | boot, update | Stacking order of messenger iframe |
| `action_color` | boot, update | Button and link color inside messenger |
| `background_color` | boot, update | Team profile header color |
| `theme_mode` | boot, update | `'light'`, `'dark'`, or `'system'` |

| Method | Purpose |
|---|---|
| `Intercom('show')` | Open messenger to default view |
| `Intercom('showSpace', space)` | Open messenger to specific space |
| `Intercom('showNewMessage', text)` | Open new message composer |
| `Intercom('hideNotifications', bool)` | Suppress/restore notification popups |
| `Intercom('onUnreadCountChange', fn)` | Register unread count callback |
