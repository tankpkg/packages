# Calling Workarounds and Performance

Sources: Intercom Developer Documentation, Intercom Phone/Switch API docs, Web Performance best practices

Covers: phone and video calling limitations, Switch API, Fin Voice, trackEvent workarounds, lazy loading, facade pattern, Core Web Vitals impact, testing and mocking.

## Critical: There Is No startCall() Method

The single most common misconception about Intercom's frontend SDK is that a method exists to initiate phone or video calls from JavaScript. It does not. There is no `Intercom('startCall', ...)`, no `startVideoCall()`, no `openPhoneChannel()`. Phone and video are entirely separate systems from the Messenger widget and have no programmatic JavaScript surface for call initiation.

| Feature | Programmatic from JS? | API Available? |
|---|---|---|
| Inbound phone (IVR) | No | REST (read-only) |
| Outbound phone | No — agent-initiated only | REST (read-only) |
| Phone-to-Messenger deflection | No — server-side REST only | POST /phone_call_redirects |
| Video (Google Meet) | No — agent-initiated only | None |
| Fin Voice (AI phone) | No | POST /fin_voice/register (Unstable) |

When a user asks "how do I open a call from Intercom," the answer is: you cannot open a call directly. Route the user toward a call through one of the workaround patterns described in this file.

The table above covers every calling-related feature in Intercom's product as of 2024. If a new calling feature is released, verify whether it has a JavaScript API before assuming it does — Intercom's calling infrastructure is intentionally separate from the Messenger SDK.

## The trackEvent Workaround

The officially confirmed pattern for connecting a frontend action to phone support is to fire a custom event and let an Intercom Workflow handle the routing. Intercom staff have confirmed this as the intended approach for callback requests.

Fire the event from your frontend:

```javascript
Intercom('trackEvent', 'request-phone-callback', {
  phone: '+11234567890',
  preferred_time: 'afternoon',
  page: 'pricing'
});
```

Then in the Intercom dashboard, create a Workflow with an event-based trigger:

1. Trigger: User performs event — `request-phone-callback`
2. Action: Assign conversation to phone support team
3. Action: Send automated reply confirming callback request
4. Optional: Tag the conversation with `callback-requested`

The metadata you pass — phone number, preferred time, originating page — appears in the conversation context for the agent. This gives agents everything they need to make the outbound call without requiring any additional data collection.

For the full trackEvent method signature and event naming conventions, see `references/js-api-reference.md`. For building the Workflow automation side, see `references/events-and-workflows.md`.

Event names should use kebab-case and be descriptive enough that an agent reading the conversation context understands what the user requested. Avoid generic names like `phone-request` — prefer `request-phone-callback` or `schedule-callback-request`.

## Switch API: Phone-to-Messenger Deflection

The Switch API lets you deflect callers from your phone queue to the Intercom Messenger. When a caller is waiting on hold, your IVR or telephony backend calls this endpoint, which sends the caller an SMS with a link to continue the conversation in Messenger.

This is a server-side REST call — your backend makes it, not the browser. The Switch API is designed for telephony systems, not browser JavaScript. Do not attempt to call it from the frontend — it requires your server-side access token and is not a CORS-enabled endpoint.

Endpoint: `POST https://api.intercom.io/phone_call_redirects`

```bash
curl -X POST https://api.intercom.io/phone_call_redirects \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "phone": "+11234567890" }'
```

Successful response:

```json
{
  "type": "phone_call_redirect",
  "phone": "+11234567890",
  "url": "https://app.intercom.com/a/apps/YOUR_APP_ID/conversations/..."
}
```

The caller receives an SMS: "Continue your support conversation here: [link]". Clicking the link opens the Messenger in their mobile browser with the conversation pre-loaded.

Use this to reduce phone queue volume during peak periods. The typical integration point is your IVR system: after a caller has waited N seconds, trigger the deflection automatically. Your frontend has no role in this flow — it is purely a backend-to-Intercom API call.

The Switch API requires the caller's phone number in E.164 format (e.g., `+11234567890`). If your telephony system provides numbers in a different format, normalize them before calling the endpoint.

## Calling REST API: Read-Only Access

Intercom exposes a read-only REST API for call records. Use this to display call history inside your application — for example, showing a customer's past support calls in an account dashboard.

All calls go through your backend. Never expose your Intercom access token to the browser.

| Endpoint | Description |
|---|---|
| GET /calls | List all calls, paginated |
| GET /calls/{id} | Retrieve a specific call's details |
| GET /calls/{id}/recording | Retrieve the call recording URL |
| GET /calls/{id}/transcript | Retrieve the call transcript |

Frontend pattern: your backend exposes a proxy endpoint (e.g., `GET /api/support/calls`) that fetches from Intercom and returns sanitized data to the browser.

```javascript
app.get('/api/support/calls', async (req, res) => {
  const response = await fetch('https://api.intercom.io/calls', {
    headers: {
      'Authorization': `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}`,
      'Accept': 'application/json'
    }
  });
  res.json(await response.json());
});
```

Call records include duration, outcome, assigned agent, and timestamps. They do not include the ability to initiate new calls.

The proxy pattern is important for security: if you expose your Intercom access token in the browser, any user can read all your call records, contact data, and conversation history. Always proxy through your backend.

## Fin Voice: AI Phone Agent

Fin Voice is Intercom's AI phone agent — it handles inbound calls using the same Fin AI that powers chat. The integration connects your existing telephony provider to Fin Voice.

Registration endpoint: `POST /fin_voice/register`. This endpoint links an external call provider (Twilio, Vonage, etc.) to Fin Voice. The API is marked **Unstable** in Intercom's documentation, meaning the interface may change without notice.

Fin Voice is not a frontend integration. Your frontend has no interaction with Fin Voice at runtime — calls go directly through your phone provider to Fin, bypassing the Messenger entirely. Do not build frontend features that depend on the `/fin_voice/register` endpoint. Use it only for initial setup, and treat it as subject to breaking changes.

## Video Calling Options

Intercom does not provide a native video calling feature with a JavaScript API. The available options are:

- **Google Meet (built-in):** Agents can initiate a Google Meet call from the Intercom inbox. The meeting link is sent to the user in the conversation. There is no way to trigger this from the frontend — the agent must initiate it manually.
- **24sessions:** Video booking integration. Adds a video call scheduling option to the Messenger. Configured in the Intercom App Store, not through the SDK.
- **Aircall Now:** Enables voice calls through the Messenger widget. Requires Aircall integration setup.
- **DIY — send a meeting link:** The most reliable approach. Use `showNewMessage()` to pre-populate a message, or configure a bot flow to send a Calendly or Google Meet link automatically. The user clicks the link and joins the call outside of Intercom.

```javascript
Intercom('showNewMessage', 'I would like to schedule a video call.');
```

## Routing Patterns: Connecting Chat Users to Phone or Video

Four patterns cover the majority of use cases for routing Messenger users to phone or video support.

1. **Deflect via Switch API** — Move phone callers to chat, not the reverse. Flow: Caller waits on hold → IVR triggers POST /phone_call_redirects → Caller receives SMS → Opens Messenger link → Conversation continues in chat. Frontend role: none.

2. **Collect phone number, trigger callback** — Chat user wants to speak by phone. Flow: Bot flow collects phone number → fires `trackEvent('request-phone-callback', { phone: '...' })` → Workflow assigns to phone team → Agent calls back. Frontend role: collect the phone number, fire the event.

   ```javascript
   Intercom('trackEvent', 'request-phone-callback', {
     phone: userPhoneNumber,
     preferred_time: selectedTime,
     issue_type: conversationContext
   });
   ```

3. **Send a video call link** — User needs face-to-face support. Flow: Bot asks "Would you prefer a video call?" → User selects yes → Bot sends Calendly or Google Meet link. Configure entirely in the Intercom Workflow builder. No custom JavaScript required.

4. **Pre-populated message shortcut** — "Talk to us by phone" button in your UI. Lowest-effort implementation, works without any Workflow configuration.

   ```javascript
   document.getElementById('phone-support-btn').addEventListener('click', () => {
     Intercom('showNewMessage', 'I need to speak with someone by phone. My number is: ');
   });
   ```

## Performance Impact of the Intercom Widget

The Intercom Messenger widget is a substantial JavaScript payload. The bundle is approximately 300KB or more when gzipped, depending on which features are enabled. This is comparable to loading a full React application. After initialization, Intercom runs `setInterval` heartbeats to check for new messages. These timers execute on the main thread and contribute to long task counts, which affects Interaction to Next Paint scores on pages where users interact frequently.

| Metric | Impact | Cause |
|---|---|---|
| LCP (Largest Contentful Paint) | Delays if loaded synchronously | Script blocks render |
| FID / INP (Interaction to Next Paint) | Increased input latency | Heartbeat timers on main thread |
| CLS (Cumulative Layout Shift) | Shift if launcher loads late | Bubble appears after initial layout |

Loading Intercom synchronously in the `<head>` is the worst-case scenario for all three metrics. The launcher bubble appearing after the page has rendered causes a measurable CLS score increase. Measure your CLS before and after adding Intercom using Chrome DevTools or Lighthouse to quantify the impact on your specific pages.

## Lazy Loading Strategies

Defer Intercom loading to reduce its impact on initial page performance. Choose a strategy based on how critical immediate Messenger availability is for your users. For most SaaS applications, the facade pattern or route-based loading provides the best balance between performance and availability.

| Strategy | Implementation | Savings | Tradeoff |
|---|---|---|---|
| initializeDelay | IntercomProvider prop | Delays load by N milliseconds | Messenger unavailable during delay |
| Facade pattern | Show fake button, load on click | Full savings until first click | First-click delay of ~1-2 seconds |
| Scroll trigger | Load on scroll past fold | Savings for above-fold content | Complexity, may miss fast scrollers |
| Route-based | Load only on dashboard/support routes | Full savings on public pages | Requires route-aware setup |
| Dynamic import | import() on user interaction | Full savings until interaction | Async loading gap |

**Facade pattern:** Shows a static button that looks identical to the Intercom launcher. When the user clicks it, the real Intercom loads and opens immediately. The `{ once: true }` option on the event listener ensures the handler fires only once — after Intercom loads, it replaces the facade with the real launcher.

```javascript
const facadeButton = document.createElement('button');
facadeButton.id = 'intercom-facade';
facadeButton.setAttribute('aria-label', 'Open support chat');
facadeButton.style.cssText = `
  position: fixed; bottom: 20px; right: 20px;
  width: 60px; height: 60px; border-radius: 50%;
  background: #6366f1; border: none; cursor: pointer; z-index: 9999;
`;
document.body.appendChild(facadeButton);

facadeButton.addEventListener('click', () => {
  facadeButton.remove();
  window.intercomSettings = {
    app_id: 'YOUR_APP_ID',
    user_id: currentUser.id,
    email: currentUser.email
  };
  const script = document.createElement('script');
  script.src = 'https://widget.intercom.io/widget/YOUR_APP_ID';
  script.onload = () => {
    Intercom('boot', window.intercomSettings);
    Intercom('show');
  };
  document.head.appendChild(script);
}, { once: true });
```

**React facade with @intercom/messenger-js-sdk:**

```jsx
import { useState } from 'react';

export function IntercomLauncher({ appId, user }) {
  const [loaded, setLoaded] = useState(false);

  const handleClick = async () => {
    if (loaded) return;
    const { Intercom } = await import('@intercom/messenger-js-sdk');
    Intercom('boot', { app_id: appId, ...user });
    Intercom('show');
    setLoaded(true);
  };

  return (
    <button onClick={handleClick} className="intercom-facade-launcher" aria-label="Open support chat">
      {/* Chat icon SVG */}
    </button>
  );
}
```

## Next.js Script Loading Strategy

Use `next/script` with `strategy="lazyOnload"` to defer Intercom until after the page is fully interactive. The `lazyOnload` strategy loads the script during browser idle time after all other resources have loaded. This is the recommended approach for analytics and chat widgets that are not critical to initial render.

```jsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html><body>
      {children}
      <Script
        id="intercom-init"
        strategy="lazyOnload"
        dangerouslySetInnerHTML={{ __html: `
          window.intercomSettings = { app_id: '${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}' };
          (function(){var w=window;var ic=w.Intercom;if(typeof ic==="function"){ic('reattach_activator');ic('update',w.intercomSettings);}else{var d=document;var i=function(){i.c(arguments);};i.q=[];i.c=function(args){i.q.push(args);};w.Intercom=i;var l=function(){var s=d.createElement('script');s.type='text/javascript';s.async=true;s.src='https://widget.intercom.io/widget/${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}';var x=d.getElementsByTagName('script')[0];x.parentNode.insertBefore(s,x);};if(document.readyState==='complete'){l();}else if(w.attachEvent){w.attachEvent('onload',l);}else{w.addEventListener('load',l,false);}}})();
        `}}
      />
    </body></html>
  );
}
```

For the `@intercom/messenger-js-sdk` package in Next.js, use dynamic import with `ssr: false` to prevent Intercom from running during server-side rendering, where it would throw errors and add unnecessary weight to the server response:

```jsx
'use client';
import dynamic from 'next/dynamic';

const IntercomWidget = dynamic(() => import('./IntercomWidget'), { ssr: false });

export function IntercomProvider({ children }) {
  return <>{children}<IntercomWidget /></>;
}
```

## Testing and Mocking

Never let Intercom load in a test environment. The widget makes network requests, runs timers, and modifies the DOM in ways that interfere with test assertions and slow down test suites. A single unguarded Intercom initialization in a test file can add several seconds to your test run and cause flaky failures due to network timeouts.

**Vitest — mock @intercom/messenger-js-sdk:**

```javascript
vi.mock('@intercom/messenger-js-sdk', () => ({
  default: vi.fn(),
  Intercom: vi.fn()
}));
```

**Vitest — mock react-use-intercom:**

```javascript
vi.mock('react-use-intercom', () => ({
  useIntercom: () => ({
    boot: vi.fn(), shutdown: vi.fn(), show: vi.fn(), hide: vi.fn(),
    showNewMessage: vi.fn(), trackEvent: vi.fn(), update: vi.fn(),
    startTour: vi.fn(), startChecklist: vi.fn()
  }),
  IntercomProvider: ({ children }) => children
}));
```

Place this mock in your test setup file so it applies globally. Individual tests can then assert on specific calls:

```javascript
test('fires callback request event on form submit', async () => {
  const { trackEvent } = useIntercom();
  // render component, submit form
  expect(trackEvent).toHaveBeenCalledWith('request-phone-callback', {
    phone: '+11234567890',
    preferred_time: 'afternoon'
  });
});
```

**Jest — manual mock:**

```javascript
// __mocks__/@intercom/messenger-js-sdk.js
module.exports = { default: jest.fn(), Intercom: jest.fn() };
```

Jest automatically picks up files in `__mocks__/` directories adjacent to `node_modules`.

**Angular — mock IntercomService in TestBed:**

```typescript
const mockIntercomService = {
  boot: jasmine.createSpy('boot'),
  shutdown: jasmine.createSpy('shutdown'),
  show: jasmine.createSpy('show'),
  hide: jasmine.createSpy('hide'),
  trackEvent: jasmine.createSpy('trackEvent'),
  showNewMessage: jasmine.createSpy('showNewMessage')
};

TestBed.configureTestingModule({
  providers: [{ provide: IntercomService, useValue: mockIntercomService }]
});
```

For Vitest in Angular projects, replace `jasmine.createSpy` with `vi.fn()`.

Mock at the module boundary, not at the `window.Intercom` level. Mocking `window.Intercom` directly is fragile because it depends on the global being set before the module initializes. Module-level mocks are resolved at import time and are reliable across all test runners.

## TypeScript Types

The `@intercom/messenger-js-sdk` package includes built-in TypeScript type definitions. No additional `@types/` package is needed when using the SDK. Types are inferred from the SDK's exported functions and cover all standard method calls including `boot`, `update`, `show`, `hide`, `trackEvent`, and `startTour`.

For projects using the legacy `window.Intercom` snippet pattern without the SDK package, install the community type definitions:

```bash
npm install --save-dev @types/intercom-web
```

This adds the `Intercom` global type to `window` and provides type checking for all method calls.

When writing custom event metadata types, extend the SDK types rather than using `any`:

```typescript
interface CallbackRequestMetadata {
  phone: string;
  preferred_time: 'morning' | 'afternoon' | 'evening';
  page: string;
  issue_type?: string;
}

function requestCallback(metadata: CallbackRequestMetadata): void {
  Intercom('trackEvent', 'request-phone-callback', metadata);
}
```

This pattern catches type errors at compile time and documents the expected shape of event metadata for other developers.
