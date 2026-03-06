# vanilla-cookieconsent v3

Sources: cookieconsent.orestbida.com, github.com/orestbida/cookieconsent, npm vanilla-cookieconsent v3.1.0

vanilla-cookieconsent is a lightweight (~7KB gzipped), dependency-free consent management library. It handles consent UI, cookie storage, script gating, and programmatic consent queries. MIT license, ~115K weekly npm downloads, WCAG-compliant dialog, 40+ languages.

---

## Installation

### npm

```bash
npm install vanilla-cookieconsent
```

```js
import CookieConsent from 'vanilla-cookieconsent';
import 'vanilla-cookieconsent/dist/cookieconsent.css';
```

### CDN

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vanilla-cookieconsent/dist/cookieconsent.css" />
<script defer src="https://cdn.jsdelivr.net/npm/vanilla-cookieconsent/dist/cookieconsent.umd.js"></script>
```

CDN exposes `window.CookieConsent`. Call `CookieConsent.run(config)` once on page load.

---

## Categories

Define categories under the `categories` key. Each maps to a named consent group referenced by scripts and callbacks.

```js
categories: {
  necessary: {
    enabled: true,   // pre-checked
    readOnly: true,  // user cannot uncheck
  },
  analytics: {
    enabled: false,  // opt-in by default
    autoClear: {
      cookies: [
        { name: /^_ga/ },   // regex matches _ga, _ga_XXXXXXXX
        { name: '_gid' },   // exact string match
        { name: /^_gat/ },
      ],
      reloadPage: false,    // set true when script cannot stop without reload
    },
  },
  marketing: {
    enabled: false,
    autoClear: {
      cookies: [
        { name: /^_fbp/ },
        { name: /^_fbc/ },
      ],
      reloadPage: false,
    },
  },
  functionality: {
    enabled: false,  // chat widgets, embedded maps, preference storage
  },
},
```

`autoClear` deletes matching cookies when a category is rejected or withdrawn. String values match exact cookie names; RegExp values test against the name. The library deletes from the current domain and all parent domains.

---

## Script Gating

### Declarative: data-cookiecategory

Set `type="text/plain"` and `data-cookiecategory` on script tags. The library re-enables them after consent by cloning the element with `type="text/javascript"`.

```html
<!-- External script blocked until analytics consent -->
<script
  type="text/plain"
  data-cookiecategory="analytics"
  src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXX"
  async
></script>

<!-- Inline script blocked until analytics consent -->
<script type="text/plain" data-cookiecategory="analytics">
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXX');
</script>

<!-- Marketing script -->
<script
  type="text/plain"
  data-cookiecategory="marketing"
  src="https://connect.facebook.net/en_US/fbevents.js"
></script>
```

### Programmatic: onConsent / onChange

Use callbacks for SPA analytics clients or when you need to call disable methods on rejection.

```js
onConsent: () => {
  // Fires on every page load when valid consent exists,
  // and immediately after first consent.
  if (CookieConsent.acceptedCategory('analytics')) initAnalytics();
  if (CookieConsent.acceptedCategory('marketing')) initAds();
},

onChange: ({ changedCategories, changedServices }) => {
  // Fires when the user updates preferences after initial consent.
  if (changedCategories.includes('analytics')) {
    CookieConsent.acceptedCategory('analytics')
      ? initAnalytics()
      : disableAnalytics();
  }
},

onFirstConsent: ({ cookie }) => {
  // Fires once, the very first time the user makes a choice.
},
```

`changedCategories`: array of category names whose state changed.
`changedServices`: object mapping category names to arrays of changed service names.

---

## Services

Services add sub-category granularity. A user can accept `analytics` but reject a specific service within it.

```js
analytics: {
  enabled: false,
  services: {
    ga: {
      label: 'Google Analytics',
      onAccept: () => { initGoogleAnalytics(); },
      onReject: () => { disableGoogleAnalytics(); },
      cookies: [{ name: /^_ga/ }, { name: '_gid' }],
    },
    hotjar: {
      label: 'Hotjar',
      onAccept: () => { initHotjar(); },
      onReject: () => { disableHotjar(); },
      cookies: [{ name: /^_hj/ }],
    },
  },
},
```

Link the preferences modal section to the category via `linkedCategory: 'analytics'`; services render as individual toggles automatically. Add `cookieTable: { headers: { name, domain, desc }, body: [{ name, domain, desc }] }` to the section for a disclosure table.

Query service acceptance: `CookieConsent.acceptedService('ga', 'analytics')` returns `true | false`.

---

## Revision System

Increment `revision` to invalidate all existing consents and force re-consent. Use when cookie usage changes materially.

```js
CookieConsent.run({
  revision: 2,
  language: {
    translations: {
      en: {
        consentModal: {
          description: 'We updated our cookie policy. {{revisionMessage}}',
          revisionMessage: 'Our cookie usage has changed since your last visit.',
        },
      },
    },
  },
});
```

When the stored revision does not match the configured revision, the library invalidates the existing consent and shows the modal again. `{{revisionMessage}}` renders as an empty string when the revision has not changed.

---

## Dark Mode

Add `cc--darkmode` to the `<html>` element to activate the dark theme.

```js
// Sync with system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
document.documentElement.classList.toggle('cc--darkmode', prefersDark);
```

Override CSS variables for both modes:

```css
:root {
  --cc-bg: #ffffff;
  --cc-primary-color: #1a73e8;
  --cc-btn-primary-bg: #1a73e8;
  --cc-btn-primary-color: #ffffff;
  --cc-btn-secondary-bg: #f1f3f4;
  --cc-btn-secondary-color: #3c4043;
}

.cc--darkmode {
  --cc-bg: #1e1e1e;
  --cc-primary-color: #8ab4f8;
  --cc-btn-primary-bg: #8ab4f8;
  --cc-btn-primary-color: #202124;
  --cc-btn-secondary-bg: #3c4043;
  --cc-btn-secondary-color: #e8eaed;
}
```

---

## Internationalization (i18n)

### Inline Translations

```js
language: {
  default: 'en',
  autoDetect: 'browser',  // or 'document' to read <html lang="">
  translations: {
    en: {
      consentModal: {
        title: 'Cookie consent',
        description: 'We use cookies to improve your experience.',
        acceptAllBtn: 'Accept all',
        acceptNecessaryBtn: 'Reject all',
        showPreferencesBtn: 'Manage preferences',
        footer: '<a href="/privacy">Privacy Policy</a>',
      },
      preferencesModal: {
        title: 'Cookie preferences',
        acceptAllBtn: 'Accept all',
        acceptNecessaryBtn: 'Reject all',
        savePreferencesBtn: 'Save preferences',
        closeIconLabel: 'Close',
        sections: [/* linkedCategory sections */],
      },
    },
  },
},
```

### External JSON Translations

Point each locale key to a URL; the library fetches on demand. The JSON file mirrors the inline translation object structure.

```js
translations: {
  en: '/locales/cookieconsent/en.json',
  de: '/locales/cookieconsent/de.json',
},
```

Switch language at runtime: `CookieConsent.setLanguage('de')`.

---

## GUI Options

```js
guiOptions: {
  consentModal: {
    layout: 'box',            // 'box' | 'cloud' | 'bar'
    position: 'bottom right', // 'bottom left|center|right', 'top left|center|right', 'middle left|center|right'
    equalWeightButtons: true, // accept and reject buttons same width
    flipButtons: false,       // swap button order
  },
  preferencesModal: {
    layout: 'box',            // 'box' | 'bar'
    position: 'right',        // 'left' | 'right' (bar layout only)
    equalWeightButtons: true,
    flipButtons: false,
  },
},
```

Layout guidance: `box` is a compact floating card (default); `cloud` is a wider centered card; `bar` is a full-width banner at top or bottom.

---

## Programmatic API

All methods are on the `CookieConsent` import or `window.CookieConsent` (CDN).

### Modal Control

```js
CookieConsent.show();             // Show consent modal
CookieConsent.show(true);         // Force show even if consent exists
CookieConsent.hide();             // Hide consent modal
CookieConsent.showPreferences();  // Open preferences modal
CookieConsent.hidePreferences();  // Close preferences modal
```

### Consent Actions

```js
CookieConsent.acceptAll();                             // Accept all categories
CookieConsent.acceptCategory('analytics');             // Accept one category
CookieConsent.acceptCategory(['analytics', 'marketing']); // Accept multiple
CookieConsent.acceptCategory([]);                      // Accept none (necessary only)
CookieConsent.reset(true);                             // Clear consent cookie and reload
```

### Consent Queries

```js
CookieConsent.validConsent();                    // true | false — valid, non-expired, current revision
CookieConsent.acceptedCategory('analytics');     // true | false
CookieConsent.acceptedService('ga', 'analytics'); // true | false

const prefs = CookieConsent.getUserPreferences();
// { acceptType: 'all'|'necessary'|'custom', acceptedCategories: [], rejectedCategories: [] }

const cookie = CookieConsent.getCookie();        // full parsed cc_cookie object
const id     = CookieConsent.getCookie('consentId'); // specific field
```

### Callbacks Reference

| Callback | Fires | Arguments |
|---|---|---|
| `onFirstConsent` | Once, after first-ever consent | `{ cookie }` |
| `onConsent` | Every page load with valid consent; after first consent | `{ cookie }` |
| `onChange` | When user updates preferences | `{ cookie, changedCategories, changedServices }` |
| `onModalReady` | Modal DOM ready, before shown | `{ modalName }` |
| `onModalShow` | Modal becomes visible | `{ modalName }` |
| `onModalHide` | Modal hidden | `{ modalName }` |

`modalName` is `'consentModal'` or `'preferencesModal'`.

---

## Storage Mechanism

Consent is stored in a first-party cookie named `cc_cookie` (configurable). The value is a JSON string:

```json
{
  "consentId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "consentTimestamp": "2024-01-15T10:30:00.000Z",
  "lastConsentTimestamp": "2024-01-20T14:22:00.000Z",
  "revision": 2,
  "categories": ["necessary", "analytics"],
  "services": { "analytics": ["ga"] }
}
```

Fields: `consentId` (UUID, stable), `consentTimestamp` (first consent), `lastConsentTimestamp` (last update), `revision`, `categories` (accepted names), `services` (accepted names per category).

Cookie attributes: `SameSite=Lax; Secure` on HTTPS. Default expiry: 182 days. Configure via `cookie: { name, expiresAfterDays, sameSite, useLocalStorage }`.

---

## Accessibility

The consent modal renders as `role="dialog"` with `aria-modal="true"` and `aria-labelledby` pointing to the modal title. The preferences modal follows the same pattern.

Built-in features (no configuration required):
- Focus trap: Tab and Shift+Tab cycle within the open modal.
- Focus restoration: Focus returns to the triggering element on close.
- Keyboard: Escape closes the preferences modal; Enter and Space activate buttons.
- Screen reader: Modal title announced on open via `aria-labelledby`.

Open the preferences modal from a footer link without JavaScript:

```html
<a href="#" data-cc="show-preferencesModal">Cookie settings</a>
```

---

## React and Next.js Integration

Create a client component that calls `CookieConsent.run()` inside `useEffect` with an empty dependency array. This ensures the library initializes once in the browser and never on the server.

```tsx
// components/CookieConsentProvider.tsx
'use client';

import { useEffect } from 'react';
import CookieConsent from 'vanilla-cookieconsent';
import 'vanilla-cookieconsent/dist/cookieconsent.css';

export default function CookieConsentProvider() {
  useEffect(() => {
    CookieConsent.run({
      categories: {
        necessary: { enabled: true, readOnly: true },
        analytics: { enabled: false },
        marketing: { enabled: false },
      },
      onConsent: () => {
        if (CookieConsent.acceptedCategory('analytics')) initAnalytics();
      },
      onChange: ({ changedCategories }) => {
        if (changedCategories.includes('analytics')) {
          CookieConsent.acceptedCategory('analytics')
            ? initAnalytics()
            : disableAnalytics();
        }
      },
      language: {
        default: 'en',
        translations: { en: '/locales/cookieconsent/en.json' },
      },
    });
  }, []);

  return null;
}
```

Mount `<CookieConsentProvider />` in the root layout (`app/layout.tsx`). Read consent in any client component: `CookieConsent.acceptedCategory('analytics')` is safe to call after `run()` has executed. If consent is not yet given, call `CookieConsent.showPreferences()`.

---

## Config Shape Summary

Top-level keys accepted by `CookieConsent.run()`:

| Key | Type | Purpose |
|---|---|---|
| `revision` | number | Increment to force re-consent |
| `cookie` | object | `name`, `expiresAfterDays`, `sameSite`, `useLocalStorage` |
| `guiOptions` | object | `consentModal` and `preferencesModal` layout/position |
| `categories` | object | Category definitions with `enabled`, `readOnly`, `autoClear`, `services` |
| `language` | object | `default`, `autoDetect`, `translations` (inline or URL) |
| `onFirstConsent` | function | `({ cookie })` — fires once on first-ever consent |
| `onConsent` | function | `({ cookie })` — fires on every page load with valid consent |
| `onChange` | function | `({ cookie, changedCategories, changedServices })` — fires on preference update |
| `onModalReady` | function | `({ modalName })` — fires when modal DOM is ready |
| `onModalShow` | function | `({ modalName })` — fires when modal becomes visible |
| `onModalHide` | function | `({ modalName })` — fires when modal is hidden |
