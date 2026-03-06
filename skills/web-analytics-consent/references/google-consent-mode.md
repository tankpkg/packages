# Google Consent Mode v2

Sources: Google Consent Mode documentation (developers.google.com/tag-platform/security/guides/consent), Google Tag Manager Help, Microsoft Clarity documentation (learn.microsoft.com/en-us/clarity), vanilla-cookieconsent GitHub (orestbida/cookieconsent)

---

## What Changed on March 7, 2024

Google made Consent Mode v2 mandatory for all advertisers using Google Ads and GA4 in the European Economic Area. Sites that did not upgrade lost access to remarketing audiences, conversion modeling, and audience transfer features for EU traffic.

The upgrade introduced two new consent signals on top of the original five:

- `ad_user_data` — controls whether user data may be sent to Google for advertising purposes
- `ad_personalization` — controls whether data may be used for personalized advertising (remarketing)

The full set of seven signals is now:

| Signal | Purpose | Typical default |
|---|---|---|
| `analytics_storage` | GA4 measurement cookies | denied |
| `ad_storage` | Google Ads cookies | denied |
| `ad_user_data` | Sending user data to Google Ads | denied |
| `ad_personalization` | Personalized / remarketing ads | denied |
| `functionality_storage` | Functional cookies (preferences) | denied |
| `personalization_storage` | Personalization cookies | denied |
| `security_storage` | Security and fraud-prevention cookies | granted |

Set `security_storage` to `granted` by default because these cookies are strictly necessary and do not require consent under most frameworks.

---

## What Breaks Without v2 for EU Users

Failing to implement Consent Mode v2 before the March 2024 deadline causes the following for EEA traffic:

**Remarketing and audience lists** — Google Ads cannot build or use remarketing audiences from users who have not consented. Existing audience lists stop growing for EU users.

**Audience transfer** — GA4 audiences cannot be transferred to Google Ads for targeting.

**Conversion modeling** — Google's machine-learning gap-fill for unobserved conversions is disabled. You lose the statistical recovery of conversions from users who declined cookies.

**Smart Bidding degradation** — Automated bidding strategies (Target CPA, Target ROAS) rely on modeled conversions. Without v2, Smart Bidding receives less signal and performance degrades.

---

## Basic Mode vs Advanced Mode

Choose the mode based on how much data recovery matters and how much implementation complexity you can accept.

### Basic Mode

Tags fire only after the user grants consent. No data is collected before the consent decision. Implementation is simpler: set defaults to `denied`, update to `granted` on accept, and tags handle the rest.

- No cookieless pings sent before consent
- No conversion modeling for users who decline
- Simpler to audit and explain to privacy teams
- Appropriate when legal counsel requires zero data before consent

### Advanced Mode

Tags fire immediately in a cookieless state. Google collects behavioral signals without setting cookies, then uses modeling to reconstruct conversion data for users who declined. This recovers approximately 20-40% of conversions that would otherwise be invisible.

- Cookieless pings fire on page load regardless of consent state
- Google models conversions from aggregated, cookieless signals
- Requires more careful implementation to avoid accidental data leakage
- Appropriate when conversion volume is critical for bidding performance

To enable Advanced Mode, load GTM or the GA4 snippet before the user sees the consent banner. The consent defaults you set tell Google tags to operate in cookieless mode until consent is updated.

---

## Setting Defaults Before Any Tag Fires

The consent defaults must be set before GTM or any GA4/Ads script loads. Place this block in the `<head>` above all other scripts.

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }

  // Set defaults BEFORE GTM or GA4 loads
  gtag('consent', 'default', {
    analytics_storage:      'denied',
    ad_storage:             'denied',
    ad_user_data:           'denied',
    ad_personalization:     'denied',
    functionality_storage:  'denied',
    personalization_storage:'denied',
    security_storage:       'granted',
    wait_for_update:        500
  });
</script>

<!-- GTM snippet goes here, AFTER the consent defaults block -->
<script>
  (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
  new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  })(window,document,'script','dataLayer','GTM-XXXXXXX');
</script>
```

The `wait_for_update` parameter (500 milliseconds) tells Google tags to pause before firing while waiting for a consent update. This prevents tags from firing in the denied state when the user has already consented in a previous session and the CMP is about to restore that consent automatically. Use 500ms as the default; increase to 1000ms only if your CMP takes longer to initialize.

---

## Updating Consent After User Decision

Call `gtag('consent', 'update', {...})` inside your CMP callbacks. Pass only the signals that changed — omitted signals retain their current state.

### Accept all

```javascript
gtag('consent', 'update', {
  analytics_storage:       'granted',
  ad_storage:              'granted',
  ad_user_data:            'granted',
  ad_personalization:      'granted',
  functionality_storage:   'granted',
  personalization_storage: 'granted'
});
```

### Reject all (analytics only, no ads)

```javascript
gtag('consent', 'update', {
  analytics_storage:       'denied',
  ad_storage:              'denied',
  ad_user_data:            'denied',
  ad_personalization:      'denied',
  functionality_storage:   'denied',
  personalization_storage: 'denied'
});
```

### Granular update (analytics accepted, ads declined)

```javascript
gtag('consent', 'update', {
  analytics_storage:       'granted',
  ad_storage:              'denied',
  ad_user_data:            'denied',
  ad_personalization:      'denied'
});
```

---

## Integration with vanilla-cookieconsent

vanilla-cookieconsent exposes `onConsent` (fires on first decision or page load when a saved decision exists) and `onChange` (fires when the user changes a previous decision). Map category names to consent signals in both callbacks.

```javascript
import 'https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.0.1/dist/cookieconsent.umd.js';

function updateGtagConsent(cookie) {
  const categories = cookie.categories || [];

  gtag('consent', 'update', {
    analytics_storage:       categories.includes('analytics') ? 'granted' : 'denied',
    ad_storage:              categories.includes('marketing') ? 'granted' : 'denied',
    ad_user_data:            categories.includes('marketing') ? 'granted' : 'denied',
    ad_personalization:      categories.includes('marketing') ? 'granted' : 'denied',
    functionality_storage:   categories.includes('functional') ? 'granted' : 'denied',
    personalization_storage: categories.includes('functional') ? 'granted' : 'denied'
  });
}

CookieConsent.run({
  // ... category and UI configuration in vanilla-cookieconsent.md ...

  onConsent({ cookie }) {
    updateGtagConsent(cookie);
  },

  onChange({ cookie }) {
    updateGtagConsent(cookie);
  }
});
```

The `onConsent` callback fires on every page load when a saved preference exists, which restores consent state before `wait_for_update` expires. This is the mechanism that makes returning visitors bypass the banner while still updating gtag correctly.

---

## GA4 Configuration with Consent Mode

When using gtag.js directly (without GTM), add the GA4 config call after the consent defaults block. GA4 automatically respects the consent state set by `gtag('consent', 'default', {...})`.

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }

  // Consent defaults first
  gtag('consent', 'default', {
    analytics_storage:      'denied',
    ad_storage:             'denied',
    ad_user_data:           'denied',
    ad_personalization:     'denied',
    functionality_storage:  'denied',
    personalization_storage:'denied',
    security_storage:       'granted',
    wait_for_update:        500
  });

  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

GA4 will not set `_ga` or `_gid` cookies until `analytics_storage` is updated to `granted`. In Advanced Mode, GA4 sends cookieless pings immediately; in Basic Mode, it sends nothing until consent is granted.

---

## GTM Custom HTML Tag Approach

When using GTM, load vanilla-cookieconsent via a Custom HTML tag that fires on All Pages with a trigger priority higher than your GA4 and Ads tags. Use the UMD build from jsDelivr so GTM can execute it without module bundling.

### Custom HTML tag: CookieConsent Init

Set this tag to fire on **All Pages**, with **Tag Sequencing** configured to fire before your GA4 Configuration tag.

```html
<script>
(function() {
  // Load vanilla-cookieconsent UMD build
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.0.1/dist/cookieconsent.umd.js';
  script.onload = function() {

    function updateGtagConsent(cookie) {
      var categories = cookie.categories || [];
      gtag('consent', 'update', {
        analytics_storage:       categories.indexOf('analytics') > -1 ? 'granted' : 'denied',
        ad_storage:              categories.indexOf('marketing') > -1 ? 'granted' : 'denied',
        ad_user_data:            categories.indexOf('marketing') > -1 ? 'granted' : 'denied',
        ad_personalization:      categories.indexOf('marketing') > -1 ? 'granted' : 'denied',
        functionality_storage:   categories.indexOf('functional') > -1 ? 'granted' : 'denied',
        personalization_storage: categories.indexOf('functional') > -1 ? 'granted' : 'denied'
      });
    }

    CookieConsent.run({
      onConsent: function(evt) { updateGtagConsent(evt.cookie); },
      onChange:  function(evt) { updateGtagConsent(evt.cookie); }
      // Add category and UI config here
    });
  };
  document.head.appendChild(script);
})();
</script>
```

### GTM tag consent settings

In each GA4 Configuration tag and Google Ads Conversion Tracking tag, open **Advanced Settings > Consent Settings** and set:

- GA4 Configuration: require `analytics_storage`
- Google Ads Conversion: require `ad_storage` and `ad_user_data`
- Remarketing tags: require `ad_storage`, `ad_user_data`, and `ad_personalization`

GTM will not fire these tags until the required signals are granted, regardless of when the tag trigger fires.

### Consent Mode in GTM container settings

Enable Consent Overview in the GTM container settings (Admin > Container Settings > Enable consent overview). This provides a dashboard showing which tags require which consent signals and whether they are configured correctly.

---

## Certified vs Non-Certified CMPs

Google maintains a list of Certified CMP Partners for Consent Mode v2. Certified CMPs (such as CookieYes, Cookiebot, OneTrust) integrate Consent Mode automatically and appear in the Google Ads CMP certification list.

vanilla-cookieconsent is not a Google-certified CMP. It works correctly with manual configuration as shown in this document, but you must implement the `gtag('consent', 'update', {...})` calls yourself. The absence of certification does not affect technical functionality — it only affects whether Google Ads surfaces a certification badge in the account.

---

## Microsoft Clarity Consent API

Microsoft Clarity introduced a mandatory consent API for users in the EEA, UK, and Switzerland. From October 31, 2025, Clarity requires explicit consent before setting cookies or collecting identifiable data for users in these regions.

### API call

```javascript
window.clarity('consent', true);   // user has consented
window.clarity('consent', false);  // user has declined or not yet decided
```

Call `window.clarity('consent', false)` before Clarity initializes, or immediately after, to put Clarity into cookieless mode. Call `window.clarity('consent', true)` after the user grants consent.

### Behavior when consent is denied

When consent is denied or not yet given, Clarity operates in cookieless mode:

- No cookies are set (`_clck`, `_clsk` are not written)
- Session recordings are disabled
- Heatmaps are not collected
- Aggregate page-level metrics may still be collected without identifying individual users

### Behavior when consent is granted

When consent is granted, Clarity operates normally:

- Cookies are set for session continuity
- Session recordings are captured
- Heatmaps are generated
- Full analytics features are available

---

## Clarity Consent Mode v2 Integration Pattern

Integrate Clarity consent into the same CMP callbacks used for gtag. Call `window.clarity('consent', ...)` alongside the gtag update.

### With vanilla-cookieconsent

```javascript
function updateAllConsent(cookie) {
  var categories = cookie.categories || [];
  var analyticsGranted = categories.includes('analytics');
  var marketingGranted = categories.includes('marketing');

  // Update Google Consent Mode
  gtag('consent', 'update', {
    analytics_storage:       analyticsGranted ? 'granted' : 'denied',
    ad_storage:              marketingGranted ? 'granted' : 'denied',
    ad_user_data:            marketingGranted ? 'granted' : 'denied',
    ad_personalization:      marketingGranted ? 'granted' : 'denied',
    functionality_storage:   categories.includes('functional') ? 'granted' : 'denied',
    personalization_storage: categories.includes('functional') ? 'granted' : 'denied'
  });

  // Update Microsoft Clarity
  if (typeof window.clarity === 'function') {
    window.clarity('consent', analyticsGranted);
  }
}

CookieConsent.run({
  onConsent({ cookie }) { updateAllConsent(cookie); },
  onChange({ cookie })  { updateAllConsent(cookie); }
});
```

### Clarity initialization order

Load the Clarity snippet in the `<head>` before the consent banner initializes. Clarity is designed to receive the consent signal after initialization — calling `window.clarity('consent', false)` after the snippet loads correctly switches it to cookieless mode.

```html
<!-- Clarity snippet (loads first) -->
<script type="text/javascript">
  (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
  })(window, document, "clarity", "script", "YOUR_CLARITY_ID");
</script>

<!-- Immediately deny consent for EEA/UK/CH until user decides -->
<script>
  window.clarity = window.clarity || function() {
    (window.clarity.q = window.clarity.q || []).push(arguments);
  };
  window.clarity('consent', false);
</script>
```

The queuing pattern (`window.clarity.q`) ensures the consent call is queued even if the Clarity script has not finished loading. Clarity processes the queue on initialization.

---

## Geo-Targeting Consent Defaults

For sites with global traffic, apply `denied` defaults only to EEA, UK, and Switzerland users using the `region` parameter. Users outside these regions receive `granted` defaults and are not shown the consent banner.

```javascript
gtag('consent', 'default', {
  analytics_storage:      'denied',
  ad_storage:             'denied',
  ad_user_data:           'denied',
  ad_personalization:     'denied',
  wait_for_update:        500,
  region: ['AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI','FR','GR',
            'HR','HU','IE','IT','LT','LU','LV','MT','NL','PL','PT','RO',
            'SE','SI','SK','IS','LI','NO','GB','CH']
});

// Fallback default for all other regions
gtag('consent', 'default', {
  analytics_storage:      'granted',
  ad_storage:             'granted',
  ad_user_data:           'granted',
  ad_personalization:     'granted'
});
```

Place the region-specific default first. Google processes defaults in order and the more specific region array takes precedence for matching users.

---

## Verification and Debugging

### Google Tag Assistant

Use Tag Assistant (tagassistant.google.com) to verify consent signals are firing correctly. The Consent tab shows the current state of all seven signals and whether tags are being held or fired.

### GTM Preview mode

In GTM Preview, the Consent tab in the tag details panel shows which consent signals a tag requires and whether they were granted at the time the tag fired.

### Browser console

Inspect the dataLayer to confirm consent events are being pushed:

```javascript
// In browser console
dataLayer.filter(e => e[0] === 'consent');
// Should show 'default' event on load and 'update' event after user decision
```

### Common mistakes

- Placing the consent defaults block after the GTM snippet — tags fire before defaults are set
- Omitting `ad_user_data` and `ad_personalization` — these are the v2-specific signals; omitting them means you are still on v1
- Not calling `gtag('consent', 'update', {...})` in the `onConsent` callback — returning visitors who already consented will not have their consent restored
- Setting `wait_for_update` too low (under 300ms) on slow connections — tags fire in denied state before the CMP restores saved consent
- Forgetting to call `window.clarity('consent', true)` after the user accepts — Clarity remains in cookieless mode for the session even though the user consented
