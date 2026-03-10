# Intercom JavaScript API Reference

Sources: Intercom Developer Documentation (developers.intercom.com), @intercom/messenger-js-sdk v0.0.18

Covers: complete method reference, boot configuration, messenger customization, callback events.

## Installation

### Script Tag (Legacy)

Add the snippet to your HTML `<head>` or before `</body>`. Replace `YOUR_APP_ID` with your workspace app ID.

```javascript
<script>
  window.intercomSettings = { app_id: "YOUR_APP_ID" };
</script>
<script>
  (function(){var w=window;var ic=w.Intercom;if(typeof ic==="function"){
    ic('reattach_activator');ic('update',w.intercomSettings);
  } else {
    var d=document;var i=function(){i.c(arguments);};
    i.q=[];i.c=function(args){i.q.push(args);};w.Intercom=i;
    var l=function(){var s=d.createElement('script');s.type='text/javascript';
    s.async=true;s.src='https://widget.intercom.io/widget/YOUR_APP_ID';
    var x=d.getElementsByTagName('script')[0];x.parentNode.insertBefore(s,x);};
    if(document.readyState==='complete'){l();}
    else if(w.attachEvent){w.attachEvent('onload',l);}
    else{w.addEventListener('load',l,false);}
  }})();
</script>
```

### NPM Package

```bash
npm install @intercom/messenger-js-sdk
```

```javascript
import Intercom from '@intercom/messenger-js-sdk';
Intercom({ app_id: 'YOUR_APP_ID' });
```

### Legacy vs SDK Comparison

| Aspect | `window.Intercom(method, ...)` | `@intercom/messenger-js-sdk` |
|--------|-------------------------------|------------------------------|
| Installation | Script snippet in HTML | `npm install` |
| TypeScript | No built-in types | Full TypeScript definitions |
| Tree shaking | Not applicable | Named imports supported |
| Method calls | `window.Intercom('boot', {...})` | `Intercom({...})` / `boot({...})` |
| Named imports | Not available | `import { boot, show, hide } from '@intercom/messenger-js-sdk'` |
| Bundle impact | External script, no bundle cost | Adds ~10KB to bundle |

Both approaches call the same Intercom messenger. The SDK is preferred for modern JavaScript projects.

## Boot Configuration

Call `boot()` once per session after the user's identity is known. Pass all known attributes at boot time.

```javascript
import { boot } from '@intercom/messenger-js-sdk';

boot({
  app_id: 'YOUR_APP_ID',
  email: 'user@example.com',
  user_id: 'user_123',
  name: 'Jane Smith',
  created_at: 1704067200,
  user_hash: 'HMAC_SHA256_HASH',
  api_base: 'https://api-iam.intercom.io',
  hide_default_launcher: false,
  alignment: 'right',
  horizontal_padding: 20,
  vertical_padding: 20,
});
```

### Boot Settings Reference

| Property | Type | Description |
|----------|------|-------------|
| `app_id` | string | **Required.** Your Intercom workspace app ID. |
| `email` | string | User's email address. |
| `user_id` | string | Your internal user ID. Stable identifier across sessions. |
| `name` | string | User's display name shown in the Intercom inbox. |
| `created_at` | number | Unix timestamp (seconds) of account creation. Used for segmentation. |
| `user_hash` | string | HMAC-SHA256 of `user_id` (or `email` if no `user_id`). Enables identity verification. |
| `intercom_user_jwt` | string | JWT-based identity token. Alternative to `user_hash`. |
| `api_base` | string | Regional API endpoint. Defaults to US. See regional table below. |
| `custom_launcher_selector` | string | CSS selector for a custom launcher element (e.g. `'#my-button'`). |
| `hide_default_launcher` | boolean | Hides the default chat bubble. Use with `custom_launcher_selector`. |
| `alignment` | string | `'left'` or `'right'`. Default: `'right'`. |
| `horizontal_padding` | number | Pixels from screen edge. Default: `20`. |
| `vertical_padding` | number | Pixels from screen bottom. Default: `20`. |
| `z_index` | number | CSS z-index of the messenger widget. Default: `2147483001`. |
| `action_color` | string | Hex color for action buttons and links. |
| `background_color` | string | Hex color for the messenger header and launcher. |
| `theme_mode` | string | `'light'`, `'dark'`, or `'system'`. |
| `session_duration` | number | Milliseconds of inactivity before session expires. |

Custom user or company attributes are passed flat in the boot object — not nested under a `custom_attributes` key:

```javascript
boot({ app_id: 'YOUR_APP_ID', user_id: 'user_123', plan: 'pro', company_size: 50 });
```

### Regional API Base URLs

| Region | `api_base` value |
|--------|-----------------|
| United States (default) | `https://api-iam.intercom.io` |
| European Union | `https://api-iam.eu.intercom.io` |
| Australia | `https://api-iam.au.intercom.io` |

Set `api_base` to match the region where your Intercom workspace is hosted. Mismatched regions cause boot failures.

## Lifecycle Methods

### boot(settings)

Initializes the messenger and identifies the user. Call once per page load or session start.

```javascript
boot({ app_id: 'YOUR_APP_ID', user_id: 'user_123' });
```

### update(attributes?)

Refreshes the messenger with new user data and checks for new messages. Call on every route change in SPAs. Throttled to **20 calls per 30 minutes** — batch attribute changes rather than calling repeatedly.

```javascript
update();                                          // Ping for new messages
update({ email: 'new@example.com' });              // Update attributes
```

### shutdown()

Clears the current user session and removes the messenger. Call on logout. Without `shutdown()`, Intercom stores the session in a cookie for up to 1 week — a logged-out user returning within that window may see the previous user's conversations.

```javascript
shutdown();
```

## Visibility Methods

| Method | Description |
|--------|-------------|
| `show()` | Opens the messenger to its default view (home or last open space). |
| `hide()` | Closes the messenger if open. |
| `hideNotifications(hide)` | Shows or hides the notification badge. Pass `true` to hide, `false` to show. |

```javascript
import { show, hide, hideNotifications } from '@intercom/messenger-js-sdk';

show();
hide();
hideNotifications(true);
```

## Navigation Methods

### showSpace(space)

Opens the messenger to a named space. Each space must be enabled in Messenger > Spaces. Calling with a disabled space opens the home screen instead.

```javascript
showSpace('home');      // Home screen
showSpace('messages'); // Conversations list
showSpace('help');     // Help center / articles
showSpace('news');     // News feed
showSpace('tasks');    // Tasks / checklists
showSpace('tickets');  // Tickets view
```

### showMessages()

Opens the conversations list. Equivalent to `showSpace('messages')`.

```javascript
showMessages();
```

### showNewMessage(prepopulatedContent?)

Opens the new message composer. Optionally pre-fills the message body.

```javascript
showNewMessage();
showNewMessage('I need help with my billing.');
```

### showArticle(articleId)

Opens a specific help center article by numeric ID. Find IDs in the Articles section URL: `app.intercom.com/a/apps/YOUR_APP_ID/articles/12345678`.

```javascript
showArticle(12345678);
```

### showNews(newsItemId)

Opens a specific news item by numeric ID. Find IDs in the Intercom News section.

```javascript
showNews(87654321);
```

### showTicket(ticketId)

Opens a specific ticket by numeric ID.

```javascript
showTicket(11223344);
```

### showConversation(conversationId)

Opens a specific conversation by numeric ID.

```javascript
showConversation(99887766);
```

## Engagement Methods

### startTour(tourId)

Triggers a product tour by numeric ID. Only standalone, live tours work — tours in a Series cannot be triggered via this method. The user must match the tour's audience rules.

```javascript
startTour(123456);
```

### startSurvey(surveyId)

Triggers an in-product survey by numeric ID. Surveys have an inherent delay of approximately **5-7 seconds** before appearing — do not assume failure if the survey does not appear immediately.

```javascript
startSurvey(654321);
```

### startChecklist(checklistId)

Opens a specific checklist by numeric ID. The checklist must be published — calling with a draft ID silently fails.

```javascript
startChecklist(112233);
```

### trackEvent(eventName, metadata?)

Records a custom event for the current user. Metadata values must be strings, numbers, or booleans — not nested objects or arrays.

```javascript
trackEvent('signed_up');
trackEvent('purchased_plan', { plan_name: 'Pro', amount: 99, currency: 'USD' });
```

## Callback Events

Register callbacks after `boot()` to respond to messenger state changes.

### onHide(callback)

Fires when the messenger is closed.

```javascript
onHide(() => { console.log('Messenger closed'); });
```

### onShow(callback)

Fires when the messenger is opened.

```javascript
onShow(() => { console.log('Messenger opened'); });
```

### onUnreadCountChange(callback)

Fires when the unread count changes. Also fires **immediately upon registration** with the current count — account for this initial call in your handler.

```javascript
onUnreadCountChange((count) => {
  document.getElementById('badge').textContent = count > 0 ? count : '';
});
```

### onUserEmailSupplied(callback)

Fires when a visitor (non-identified user) submits their email address in the messenger.

```javascript
onUserEmailSupplied(() => { console.log('Visitor provided email'); });
```

## Identity

### getVisitorId()

Returns the anonymous visitor ID assigned before a user is identified. Returns `undefined` if the user is already identified. Use to associate pre-login activity with a user after authentication — pass the visitor ID to your backend and use the Intercom REST API to merge the visitor with the identified user.

```javascript
const visitorId = getVisitorId();
```

## Messenger Customization

Appearance settings can be passed at `boot()` or updated via `update()`.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `alignment` | string | `'right'` | `'left'` or `'right'` — side of screen. |
| `horizontal_padding` | number | `20` | Pixels from screen edge. Desktop only. |
| `vertical_padding` | number | `20` | Pixels from screen bottom. Desktop only. |
| `z_index` | number | `2147483001` | CSS z-index. Raise if other elements overlap the messenger. |
| `action_color` | string | Workspace default | Hex color for buttons and links. |
| `background_color` | string | Workspace default | Hex color for header and launcher. |
| `theme_mode` | string | `'system'` | `'light'`, `'dark'`, or `'system'`. |
| `hide_default_launcher` | boolean | `false` | Hides the default bubble. Requires a custom launcher. |
| `custom_launcher_selector` | string | — | CSS selector for your custom open button. |
| `session_duration` | number | — | Inactivity timeout in milliseconds. |

### Custom Launcher Pattern

Intercom attaches a click listener to the element matching `custom_launcher_selector`. The element must exist in the DOM when `boot()` is called.

```javascript
boot({ app_id: 'YOUR_APP_ID', hide_default_launcher: true, custom_launcher_selector: '#support-button' });
```

```html
<button id="support-button">Contact Support</button>
```

## SPA Considerations

Call `update()` on every route change — the messenger does not detect navigation automatically. This logs the page view, checks for URL-triggered messages, and keeps the session active.

```javascript
// React Router / History API pattern
router.on('routeChange', () => { update(); });

// After programmatic navigation
history.pushState({}, '', '/new-path');
update();
```

Call `shutdown()` on logout, then `boot()` again when a new user logs in. Do not call `boot()` twice without an intervening `shutdown()` — the second call is ignored.

```javascript
async function logout() {
  await api.logout();
  shutdown();
  router.push('/login');
}

async function login(credentials) {
  const user = await api.login(credentials);
  boot({ app_id: 'YOUR_APP_ID', user_id: user.id, email: user.email, user_hash: user.intercomHash });
}
```

## Common Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| `update()` calls silently dropped | Exceeds 20 calls per 30 minutes | Debounce route change handlers; batch attribute updates |
| Previous user's conversations visible after logout | `shutdown()` not called | Always call `shutdown()` on logout |
| Custom attributes not appearing in Intercom | Attributes nested under `custom_attributes` key | Pass attributes flat in the boot/update object |
| `startTour()` does nothing | Tour is part of a Series, or is in draft | Use only standalone, live tours |
| Survey appears 5-7 seconds late | Intentional delay built into Intercom | Do not retry; wait for the survey to appear |
| `startChecklist()` does nothing | Checklist is in draft state | Publish the checklist before triggering |
| `showSpace()` opens home instead of target | Space not enabled in workspace settings | Enable the space in Messenger > Spaces |
| Messenger overlaps page content | Default z-index too high or too low | Adjust `z_index` in boot settings |
| Padding settings ignored on mobile | Mobile layout overrides padding | Intercom controls mobile positioning; padding applies desktop only |
| `onUnreadCountChange` fires immediately | Fires on registration with current count | Handle the initial call; do not treat it as a new message |
| `boot()` called twice | Second call ignored silently | Call `shutdown()` between sessions |
| `getVisitorId()` returns undefined | User is already identified | Only call before `boot()` with user identity |
