# Framework Integration Patterns

Sources: @intercom/messenger-js-sdk docs, react-use-intercom docs, community packages, framework documentation

Covers: React, Next.js (App Router and Pages Router), Angular, Vue 3, Nuxt 3 — installation, provider patterns, SPA routing, conditional loading.

For complete method signatures, see `references/js-api-reference.md`.

## Package Selection

| Package | Version | Weekly DLs | Framework | Recommendation |
|---|---|---|---|---|
| `@intercom/messenger-js-sdk` | 0.0.18 | ~853K | Any | Official SDK — use for Angular, Vue, vanilla JS |
| `react-use-intercom` | 5.5.0 | ~408K | React | Best React wrapper — Provider + hook pattern |
| `@supy-io/ngx-intercom` | 14.2.12 | ~7.5K | Angular | Newer Angular wrapper, actively maintained |
| `ng-intercom` | 8.0.2 | low | Angular | Legacy, unmaintained — avoid |

Use `react-use-intercom` for all React and Next.js projects. Use `@intercom/messenger-js-sdk` directly for Angular and Vue — the official SDK is well-maintained and the community wrappers add little value for those frameworks.

## React with react-use-intercom

```bash
npm install react-use-intercom
```

### IntercomProvider Props

Wrap your application root with `IntercomProvider`. All props except `appId` are optional.

| Prop | Type | Default | Description |
|---|---|---|---|
| `appId` | `string` | required | Your Intercom workspace app ID |
| `autoBoot` | `boolean` | `false` | Boot Intercom immediately on mount |
| `autoBootProps` | `IntercomProps` | — | User/visitor data passed on auto-boot |
| `shouldInitialize` | `boolean` | `true` | Conditionally prevent initialization |
| `initializeDelay` | `number` | — | Milliseconds to delay initialization |
| `apiBase` | `string` | — | Override API base URL (EU data residency) |
| `onHide` | `() => void` | — | Callback when messenger hides |
| `onShow` | `() => void` | — | Callback when messenger shows |
| `onUnreadCountChange` | `(count: number) => void` | — | Callback when unread count changes |

### useIntercom Hook

`useIntercom()` returns an object with the following methods and values:

| Method / Value | Description |
|---|---|
| `boot(props?)` | Initialize Intercom with optional user data |
| `shutdown()` | Shut down Intercom and clear session |
| `hardShutdown()` | Shut down and remove all Intercom cookies |
| `update(props?)` | Update user data and check for new messages |
| `hide()` / `show()` | Hide or show the messenger |
| `showMessages()` | Open messenger to message list |
| `showNewMessage(content?)` | Open new message composer |
| `showArticle(articleId)` | Open a specific Help Center article |
| `showSpace(spaceName)` | Open a specific Space (home, messages, help, news, tasks, tickets) |
| `showTicket(ticketId)` | Open a specific ticket |
| `showConversation(conversationId)` | Open a specific conversation |
| `startSurvey(surveyId)` | Trigger a specific survey |
| `startChecklist(checklistId)` | Trigger a specific checklist |
| `trackEvent(name, metadata?)` | Track a custom event |
| `getVisitorId()` | Return the current visitor ID |
| `startTour(tourId)` | Trigger a product tour |
| `isOpen` | `boolean` — current open state of the messenger |
| `unreadCount` | `number` — current unread message count |

### Boot Example

```tsx
// main.tsx — wrap app root; use autoBoot for visitors, or call boot() after auth
import { IntercomProvider, useIntercom } from 'react-use-intercom';

export default function Root() {
  return (
    <IntercomProvider appId="your_app_id" autoBoot onUnreadCountChange={(n) => console.log('Unread:', n)}>
      <App />
    </IntercomProvider>
  );
}

// After user authenticates, boot with identity verification data
function useBootIntercom(user: User | null) {
  const { boot, shutdown } = useIntercom();
  useEffect(() => {
    if (user) {
      boot({ userId: user.id, email: user.email, name: user.name, createdAt: user.createdAt });
    } else {
      shutdown(); // clears session on logout
    }
  }, [user]);
}

// Access messenger state anywhere in the tree
function SupportButton() {
  const { show, unreadCount } = useIntercom();
  return <button onClick={show}>Support {unreadCount > 0 && `(${unreadCount})`}</button>;
}
```
## Next.js App Router

### Critical Constraint: Client Boundary

The Intercom messenger runs in the browser. In the App Router, all Intercom code must live in a Client Component. Mark the provider file with `'use client'` at the top — the `react-use-intercom` library does not include this directive itself.

### IntercomClientProvider

```tsx
// components/IntercomClientProvider.tsx
'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { IntercomProvider, useIntercom } from 'react-use-intercom';

const INTERCOM_APP_ID = process.env.NEXT_PUBLIC_INTERCOM_APP_ID!;

function IntercomRouteTracker() {
  const pathname = usePathname();
  const { update } = useIntercom();
  // Call update() on every route change to track page impressions
  // and trigger message rules based on the current URL
  useEffect(() => { update(); }, [pathname]);
  return null;
}

export function IntercomClientProvider({
  children,
  userId,
  userEmail,
  userName,
}: {
  children: React.ReactNode;
  userId?: string;
  userEmail?: string;
  userName?: string;
}) {
  return (
    <IntercomProvider
      appId={INTERCOM_APP_ID}
      autoBoot
      autoBootProps={{ userId, email: userEmail, name: userName }}
      shouldInitialize={!!INTERCOM_APP_ID}
    >
      <IntercomRouteTracker />
      {children}
    </IntercomProvider>
  );
}
```

### Place in Root Layout

```tsx
// app/layout.tsx
import { IntercomClientProvider } from '@/components/IntercomClientProvider';

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(); // fetch session server-side, pass as props
  return (
    <html lang="en">
      <body>
        <IntercomClientProvider
          userId={session?.user?.id}
          userEmail={session?.user?.email}
          userName={session?.user?.name}
        >
          {children}
        </IntercomClientProvider>
      </body>
    </html>
  );
}
```

`router.events` does not exist in App Router — use `usePathname()` inside a Client Component instead.

## Next.js Pages Router

```tsx
// pages/_app.tsx
import type { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { IntercomProvider, useIntercom } from 'react-use-intercom';

const INTERCOM_APP_ID = process.env.NEXT_PUBLIC_INTERCOM_APP_ID!;

function RouteChangeHandler() {
  const router = useRouter();
  const { update } = useIntercom();
  useEffect(() => {
    const handleRouteChange = () => { update(); };
    router.events.on('routeChangeComplete', handleRouteChange);
    return () => { router.events.off('routeChangeComplete', handleRouteChange); };
  }, [router.events, update]);
  return null;
}

export default function App({ Component, pageProps }: AppProps) {
  const { user } = pageProps;
  return (
    <IntercomProvider
      appId={INTERCOM_APP_ID}
      autoBoot
      autoBootProps={{ userId: user?.id, email: user?.email, name: user?.name }}
    >
      <RouteChangeHandler />
      <Component {...pageProps} />
    </IntercomProvider>
  );
}
```

## Angular

### Critical Constraint: NgZone

Intercom's internal heartbeat timer runs on a `setInterval`. Without `NgZone.runOutsideAngular()`, every tick of that interval triggers Angular's change detection cycle across your entire application. This causes severe performance degradation — wrap every Intercom call in `runOutsideAngular`.

```bash
npm install @intercom/messenger-js-sdk
```

### IntercomService

```typescript
// services/intercom.service.ts
import { Injectable, NgZone, OnDestroy } from '@angular/core';
import Intercom from '@intercom/messenger-js-sdk';

export interface IntercomUser {
  userId?: string; email?: string; name?: string; createdAt?: number;
  [key: string]: unknown;
}

@Injectable({ providedIn: 'root' })
export class IntercomService implements OnDestroy {
  private readonly appId = 'your_app_id';
  constructor(private ngZone: NgZone) {}

  boot(user?: IntercomUser): void {
    this.ngZone.runOutsideAngular(() => {
      Intercom({ app_id: this.appId, user_id: user?.userId, email: user?.email, name: user?.name, created_at: user?.createdAt });
    });
  }
  update(props?: Partial<IntercomUser>): void {
    this.ngZone.runOutsideAngular(() => { window.Intercom('update', props ?? {}); });
  }
  shutdown(): void { this.ngZone.runOutsideAngular(() => { window.Intercom('shutdown'); }); }
  show(): void { this.ngZone.runOutsideAngular(() => { window.Intercom('show'); }); }
  hide(): void { this.ngZone.runOutsideAngular(() => { window.Intercom('hide'); }); }
  trackEvent(name: string, metadata?: Record<string, unknown>): void {
    this.ngZone.runOutsideAngular(() => { window.Intercom('trackEvent', name, metadata); });
  }
  ngOnDestroy(): void { this.shutdown(); }
}
```

### AppComponent with Route Tracking

```typescript
// app.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter, Subject, takeUntil } from 'rxjs';
import { IntercomService } from './services/intercom.service';

@Component({ selector: 'app-root', template: '<router-outlet />' })
export class AppComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  constructor(private intercom: IntercomService, private router: Router) {}
  ngOnInit(): void {
    this.intercom.boot(); // pass user data if authenticated
    this.router.events.pipe(filter((e) => e instanceof NavigationEnd), takeUntil(this.destroy$))
      .subscribe(() => { this.intercom.update(); });
  }
  ngOnDestroy(): void { this.destroy$.next(); this.destroy$.complete(); }
}
```

## Vue 3

```bash
npm install @intercom/messenger-js-sdk
```

### Plugin and Composable

```typescript
// plugins/intercom.ts
import type { App } from 'vue';
import Intercom from '@intercom/messenger-js-sdk';

export interface IntercomInstance {
  boot: (props?: Record<string, unknown>) => void;
  update: (props?: Record<string, unknown>) => void;
  shutdown: () => void;
  show: () => void;
  hide: () => void;
  trackEvent: (name: string, metadata?: Record<string, unknown>) => void;
}

const APP_ID = import.meta.env.VITE_INTERCOM_APP_ID;

export const intercomPlugin = {
  install(app: App) {
    const intercom: IntercomInstance = {
      boot: (props = {}) => Intercom({ app_id: APP_ID, ...props }),
      update: (props = {}) => window.Intercom('update', props),
      shutdown: () => window.Intercom('shutdown'),
      show: () => window.Intercom('show'),
      hide: () => window.Intercom('hide'),
      trackEvent: (name, metadata) => window.Intercom('trackEvent', name, metadata),
    };
    app.provide('intercom', intercom);
  },
};
```

```typescript
// composables/useIntercom.ts
import { inject } from 'vue';
import type { IntercomInstance } from '@/plugins/intercom';
export function useIntercom(): IntercomInstance {
  return inject<IntercomInstance>('intercom')!;
}
```

### Register Plugin and Track Routes

```typescript
// main.ts
import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import { intercomPlugin } from './plugins/intercom';

const router = createRouter({ history: createWebHistory(), routes: [...] });
const app = createApp(App);
app.use(router);
app.use(intercomPlugin);

router.afterEach(() => { window.Intercom?.('update'); }); // track route changes

app.mount('#app');
```

## Nuxt 3

Use a `.client.ts` plugin suffix to run only in the browser, preventing SSR initialization.

```typescript
// plugins/intercom.client.ts
import Intercom from '@intercom/messenger-js-sdk';

export default defineNuxtPlugin(() => {
  const appId = useRuntimeConfig().public.intercomAppId as string;
  const intercom = {
    boot: (props: Record<string, unknown> = {}) => Intercom({ app_id: appId, ...props }),
    update: (props: Record<string, unknown> = {}) => window.Intercom('update', props),
    shutdown: () => window.Intercom('shutdown'),
    show: () => window.Intercom('show'),
    hide: () => window.Intercom('hide'),
    trackEvent: (name: string, meta?: Record<string, unknown>) => window.Intercom('trackEvent', name, meta),
  };
  intercom.boot();
  useRouter().afterEach(() => { intercom.update(); });
  return { provide: { intercom } };
});
```

Configure `runtimeConfig.public.intercomAppId` in `nuxt.config.ts`. Access via `const { $intercom } = useNuxtApp()`.

## Conditional Loading Patterns

### Auth-Only Loading

Pass `shouldInitialize={!!user}` to prevent the SDK from booting for unauthenticated visitors.

```tsx
<IntercomProvider appId={APP_ID} autoBoot={!!user} shouldInitialize={!!user}
  autoBootProps={user ? { userId: user.id, email: user.email } : undefined}>
  {children}
</IntercomProvider>
```

### Layout-Based Loading

Load Intercom only in authenticated layouts, not on marketing pages.

```tsx
// app/(dashboard)/layout.tsx — Intercom present
'use client';
import { IntercomClientProvider } from '@/components/IntercomClientProvider';
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <IntercomClientProvider>{children}</IntercomClientProvider>;
}
// app/(marketing)/layout.tsx — no Intercom
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
```

### Dynamic Import on Interaction

Defer the SDK until the user explicitly requests support — eliminates it from the initial bundle.

```tsx
export function LazySupportButton() {
  const [loaded, setLoaded] = useState(false);
  const handleClick = async () => {
    if (!loaded) {
      const { default: Intercom } = await import('@intercom/messenger-js-sdk');
      Intercom({ app_id: 'your_app_id' });
      setLoaded(true);
    }
    window.Intercom('show');
  };
  return <button onClick={handleClick}>Contact Support</button>;
}
```

## SPA Route Change Pattern

Call `update()` on every route change. Pass no arguments — Intercom reads `window.location` automatically. Without this, Intercom cannot record page impressions or trigger URL-based messages.

| Framework | Route Event | Method |
|---|---|---|
| React Router | `useLocation()` in `useEffect` | `update()` via `useIntercom` hook |
| Next.js App Router | `usePathname()` in `useEffect` | `update()` via `useIntercom` hook |
| Next.js Pages Router | `router.events.on('routeChangeComplete')` | `update()` via `useIntercom` hook |
| Angular | `Router.events` filtered to `NavigationEnd` | `IntercomService.update()` |
| Vue 3 / Nuxt 3 | `router.afterEach()` | `window.Intercom('update')` |
