---
name: "intercom-frontend"
description: |
  Intercom frontend integration expert. Covers the JavaScript Messenger SDK
  (@intercom/messenger-js-sdk), framework-specific patterns (React, Next.js,
  Angular, Vue/Nuxt), programmatic messenger control, custom launchers,
  phone/video calling workarounds (no startCall method exists), product tours,
  surveys, checklists, identity verification (JWT/HMAC), trackEvent automation,
  and performance optimization (lazy loading, facade pattern).
  Synthesizes Intercom Developer Documentation, @intercom/messenger-js-sdk
  API reference, react-use-intercom patterns, and community best practices.

  Trigger phrases: "intercom", "intercom messenger", "intercom widget",
  "intercom SDK", "@intercom/messenger-js-sdk", "react-use-intercom",
  "intercom boot", "intercom shutdown", "intercom update", "intercom show",
  "intercom custom launcher", "intercom product tour", "startTour",
  "startSurvey", "startChecklist", "intercom identity verification",
  "intercom trackEvent", "intercom phone call", "intercom video call",
  "intercom Angular", "intercom Next.js", "intercom Vue",
  "intercom performance", "intercom lazy load", "showNewMessage",
  "showSpace", "intercom JWT", "intercom HMAC"
---

# Intercom Frontend Integration

## Core Philosophy

1. **The Messenger is a guest in your app** -- boot it intentionally, shut it
   down on logout, and call update() on every route change. Stale sessions
   cause data leaks and ghost conversations.
2. **There is no startCall()** -- phone and video calls cannot be initiated
   from the JS API. Use trackEvent to trigger Workflows that route to phone
   support. This is the most common misconception.
3. **Identity verification is non-negotiable** -- without JWT or HMAC,
   anyone can impersonate users by booting with their email. Generate
   tokens server-side only.
4. **Performance is opt-in** -- the widget is ~300KB+ with heartbeat timers.
   Lazy load with facade pattern or initializeDelay to protect Core Web Vitals.
5. **Custom attributes go inline** -- pass them at the top level of boot/update,
   never nested under a custom_attributes key.

## Quick-Start: Common Problems

### "How do I add Intercom to my React/Next.js app?"

1. Install react-use-intercom for React, or @intercom/messenger-js-sdk for others.
2. Wrap app in IntercomProvider with appId and autoBoot.
3. For Next.js App Router: wrap provider in a 'use client' component.
4. Add route change tracking with update() in useEffect.
   -> See `references/framework-integration.md`

### "How do I open a phone/video call from Intercom?"

1. Accept that no startCall() method exists -- this is a hard API limitation.
2. Use trackEvent('request-phone-callback', { phone, preferred_time }).
3. Configure a Workflow in Intercom dashboard with event-based trigger.
4. For phone-to-Messenger deflection, use Switch API (server-side).
   -> See `references/calling-and-performance.md`

### "How do I build a custom chat button?"

1. Set hide_default_launcher: true in boot configuration.
2. Use custom_launcher_selector for automatic binding, or call show() programmatically.
3. Add unread badge via onUnreadCountChange callback.
   -> See `references/messenger-ui.md`

### "How do I trigger a product tour or survey?"

1. Get the ID from the Intercom dashboard URL.
2. Call startTour(id), startSurvey(id), or startChecklist(id).
3. Tours in a Series cannot be triggered -- duplicate outside the Series.
4. Surveys have a ~5-7 second delay after calling startSurvey().
   -> See `references/engagement-features.md`

### "How do I set up identity verification?"

1. Generate JWT server-side using HS256 + INTERCOM_MESSENGER_SECRET_KEY.
2. Pass as intercom_user_jwt in boot configuration.
3. Legacy HMAC still works but JWT is recommended.
   -> See `references/identity-and-data.md`

### "Intercom is slowing down my app"

1. Add initializeDelay to defer loading.
2. Implement facade pattern: show a static button, load real widget on click.
3. Use route-based loading to skip public pages.
4. For Next.js: use next/script with strategy="lazyOnload".
   -> See `references/calling-and-performance.md`

## Decision Trees

### Package Selection

| Framework | Package | Notes |
|-----------|---------|-------|
| React | react-use-intercom | Provider + useIntercom() hook, 408K weekly DLs |
| React (minimal) | @intercom/messenger-js-sdk | Official SDK, direct API calls |
| Next.js | react-use-intercom | Add 'use client' wrapper for App Router |
| Angular | @intercom/messenger-js-sdk | Use NgZone.runOutsideAngular() for all calls |
| Vue / Nuxt | @intercom/messenger-js-sdk | Plugin + composable pattern |
| Vanilla JS | @intercom/messenger-js-sdk or script tag | Script tag for simplest setup |

### Method Selection

| Goal | Method | Notes |
|------|--------|-------|
| Open messenger | show() | Opens Home or unread messages |
| Open specific space | showSpace('help') | home, messages, help, news, tasks, tickets |
| Open composer | showNewMessage('text') | Pre-populated requires Inbox Essential+ |
| Open article | showArticle(id) | Invalid ID silently opens Home |
| Start onboarding | startTour(id) | Must be published + "Use everywhere" |
| Collect feedback | startSurvey(id) | 5-7 second delay is normal |
| Track progress | startChecklist(id) | Must be published |
| Log user action | trackEvent(name, meta) | Powers Workflows and segmentation |
| Request callback | trackEvent + Workflow | No direct call API exists |

### When to Call update()

| Event | Action | Why |
|-------|--------|-----|
| Route change | update() with no args | Log page impression, check messages |
| User data changes | update({ email, name }) | Sync attributes to Intercom |
| Plan upgrade | update({ plan: 'pro' }) | Update segmentation |
| Logout | shutdown() | Clear session, prevent data leaks |

## Common Gotchas

| Gotcha | Impact | Fix |
|--------|--------|-----|
| update() throttled to 20/30min | Calls silently dropped | Batch updates, call on meaningful events |
| shutdown() not called on logout | Conversations persist 1 week via cookie | Always call shutdown() in logout flow |
| Custom attrs nested under custom_attributes | Attributes silently ignored | Pass inline at top level |
| Angular without NgZone.runOutsideAngular() | Continuous change detection from heartbeats | Wrap all Intercom calls |
| Next.js App Router without 'use client' | Server component error | Create client wrapper component |
| Padding settings on mobile | No effect, messenger is full-screen | Use custom launcher for mobile |
| Tours in a Series | startTour() fails silently | Duplicate tour outside the Series |
| hide_default_launcher: false | Forces launcher visible even if dashboard hides it | Omit property to respect dashboard setting |

## Reference Files

| File | Contents |
|------|----------|
| `references/js-api-reference.md` | Complete method reference, boot settings, customization options, SPA lifecycle |
| `references/framework-integration.md` | React, Next.js, Angular, Vue/Nuxt setup, package comparison, route tracking |
| `references/identity-and-data.md` | JWT/HMAC verification, user/company attributes, custom attributes, visitor flow |
| `references/events-and-workflows.md` | trackEvent API, metadata types, workflow triggers, webhooks, segmentation, A/B testing |
| `references/messenger-ui.md` | Custom launcher, positioning, theming, z-index, responsive behavior, notification control |
| `references/engagement-features.md` | Product tours, surveys, checklists, news, tickets, articles, onboarding patterns |
| `references/calling-and-performance.md` | Phone/video workarounds, Switch API, lazy loading, facade pattern, testing, TypeScript |
