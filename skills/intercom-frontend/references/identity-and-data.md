# Identity Verification and Data Modeling

Sources: Intercom Developer Documentation, Intercom Security Best Practices

Covers: JWT and HMAC identity verification, user attributes, company data, custom attributes, visitor identification.

For boot configuration, see `references/js-api-reference.md`.

---

## Why Identity Verification Matters

Without identity verification, any user can boot the Intercom Messenger with an arbitrary email or user_id and impersonate another user. An attacker who knows a target's email can open a conversation as that person, access their conversation history, and receive support responses intended for them.

Identity verification closes this attack vector by requiring a cryptographic proof — generated server-side with a secret key — that the frontend cannot forge. Intercom validates this proof before associating the session with the claimed identity.

Enable identity verification for all production deployments where users are logged in. Unverified deployments are acceptable only for anonymous visitor flows or internal tools with no sensitive data.

---

## JWT Verification (Recommended)

JWT is the current recommended approach. The server generates a signed token using the `INTERCOM_MESSENGER_SECRET_KEY` (found in Settings → Security). The client passes this token as `intercom_user_jwt` in the `boot()` call.

### Server-Side: Node.js

```javascript
const jwt = require('jsonwebtoken');

function generateIntercomJWT(userId) {
  const payload = {
    sub: userId,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (60 * 60), // 1 hour expiry
  };

  return jwt.sign(payload, process.env.INTERCOM_MESSENGER_SECRET_KEY, {
    algorithm: 'HS256',
  });
}

// In your API endpoint:
app.get('/api/intercom-token', requireAuth, (req, res) => {
  const token = generateIntercomJWT(req.user.id);
  res.json({ token });
});
```

The `sub` claim must match the `user_id` passed to `boot()`. The `exp` claim controls token expiry — use short-lived tokens (1 hour or less) and refresh them before expiry.

### Client-Side: Boot with JWT

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: currentUser.id,
  email: currentUser.email,
  name: currentUser.name,
  intercom_user_jwt: tokenFromServer, // fetched from your API
});
```

Fetch the JWT from your server after the user authenticates. Do not hardcode or cache the secret key in frontend code.

---

## HMAC Verification (Legacy)

HMAC-SHA256 is the older verification method. It remains supported but JWT is preferred for new implementations. HMAC generates a static hash of the user identifier — it does not expire, which is a security limitation compared to JWT.

Pass the hash as `user_hash` in the `boot()` call.

### Server-Side: Node.js

```javascript
const crypto = require('crypto');

function generateIntercomHMAC(identifier) {
  return crypto
    .createHmac('sha256', process.env.INTERCOM_SECRET_KEY)
    .update(identifier)
    .digest('hex');
}

// For user_id-based verification:
const hash = generateIntercomHMAC(user.id.toString());

// For email-based verification (when no user_id):
const hash = generateIntercomHMAC(user.email);
```

Use `user_id` as the identifier when available. Fall back to `email` only for lead flows where no user_id exists yet.

### Server-Side: Python

```python
import hmac
import hashlib

def generate_intercom_hmac(identifier: str) -> str:
    secret = os.environ['INTERCOM_SECRET_KEY'].encode('utf-8')
    message = identifier.encode('utf-8')
    return hmac.new(secret, message, hashlib.sha256).hexdigest()
```

### Client-Side: Boot with HMAC

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: currentUser.id,
  email: currentUser.email,
  user_hash: hashFromServer, // fetched from your API
});
```

---

## JWT vs HMAC Comparison

| Aspect | JWT | HMAC |
|---|---|---|
| Mechanism | Signed token with claims | Static keyed hash |
| Recommended | Yes (current standard) | Legacy |
| Expiration | Built-in via `exp` claim | None — hash never expires |
| Complexity | Higher — requires JWT library | Lower — single HMAC call |
| Security | Stronger — tokens expire | Weaker — compromised hash is permanent |
| Boot parameter | `intercom_user_jwt` | `user_hash` |
| Identifier | `sub` claim = `user_id` | Hash of `user_id` or `email` |

Migrate from HMAC to JWT for new projects. For existing HMAC implementations, migration is low-risk: generate JWT server-side and swap the boot parameter.

---

## User Attributes Reference

Pass user attributes directly in the `boot()` or `update()` call. All attributes are optional except those required by your identity verification method.

| Attribute | Type | Notes |
|---|---|---|
| `user_id` | string | Unique identifier in your system. Required for identity verification. |
| `email` | string | User's email address. |
| `name` | string | Full display name. |
| `phone` | string | E.164 format recommended: `+15551234567`. |
| `created_at` | number | Unix timestamp in **seconds** (not milliseconds) when the user signed up. |
| `unsubscribed_from_emails` | boolean | Set `true` to suppress marketing emails. |
| `language_override` | string | BCP 47 language tag, e.g. `'en'`, `'fr'`, `'de'`. Overrides browser locale. |
| `avatar` | object | `{ type: 'avatar', image_url: 'https://...' }` |
| `user_hash` | string | HMAC verification hash (legacy). |
| `intercom_user_jwt` | string | JWT verification token (recommended). |

### Boot Example with Full User Data

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  email: 'alice@example.com',
  name: 'Alice Nguyen',
  phone: '+15551234567',
  created_at: 1704067200, // Unix seconds
  unsubscribed_from_emails: false,
  language_override: 'en',
  avatar: {
    type: 'avatar',
    image_url: 'https://example.com/avatars/alice.png',
  },
  intercom_user_jwt: tokenFromServer,
});
```

Pass `created_at` as a Unix timestamp in seconds. JavaScript's `Date.now()` returns milliseconds — divide by 1000 and use `Math.floor()`.

---

## Company Data

Associate a user with one or more companies by passing a `company` object or a `companies` array. The `id` field is required; all other fields are optional.

### Single Company

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  email: 'alice@example.com',
  company: {
    id: 'company_abc',
    name: 'Acme Corp',
    created_at: 1672531200,
    plan: 'Enterprise',
    monthly_spend: 1500,
    size: 200,
    website: 'https://acme.example.com',
    industry: 'Technology',
  },
});
```

### Multiple Companies

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  companies: [
    { id: 'company_abc', name: 'Acme Corp' },
    { id: 'company_xyz', name: 'Beta Inc', plan: 'Starter' },
  ],
});
```

### Company Attribute Reference

| Attribute | Type | Notes |
|---|---|---|
| `id` | string | Required. Your internal company identifier. |
| `name` | string | Display name in Intercom. |
| `created_at` | number | Unix timestamp in seconds when the company was created. |
| `plan` | string | Subscription plan name. |
| `monthly_spend` | number | Monthly revenue from this company in your account currency. |
| `size` | number | Number of employees. |
| `website` | string | Company website URL. |
| `industry` | string | Industry classification. |

Custom attributes on companies follow the same inline pattern as user custom attributes (see below).

---

## Custom Attributes

Custom attributes extend the standard schema with your own data. They go **inline at the top level** of the boot or update object — not nested under a `custom_attributes` key.

### Correct Pattern

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  email: 'alice@example.com',
  // Custom attributes inline at top level:
  subscription_tier: 'pro',
  trial_ends_at: 1709251200,
  seats_used: 5,
  is_admin: true,
});
```

### Incorrect Pattern

```javascript
// WRONG — Intercom does not read nested custom_attributes
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  custom_attributes: {       // This key is ignored
    subscription_tier: 'pro',
  },
});
```

### Supported Types

| Type | Example | Notes |
|---|---|---|
| string | `'pro'` | Max 255 characters. |
| number | `42` | Integer or float. |
| boolean | `true` | |
| date | `1709251200` | Unix timestamp in seconds. |
| monetary | `{ amount: 4999, currency: 'usd' }` | Amount in smallest currency unit (cents). |

Define custom attributes in Settings → Data → Custom Attributes before using them. Attributes sent before definition are silently dropped.

### Custom Attributes on Companies

```javascript
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: '12345',
  company: {
    id: 'company_abc',
    name: 'Acme Corp',
    // Custom company attributes inline:
    contract_value: { amount: 120000, currency: 'usd' },
    renewal_date: 1735689600,
    account_manager: 'Bob Smith',
  },
});
```

---

## Visitor vs Lead vs User

Intercom distinguishes three identity states. Understanding the progression prevents duplicate contact records and ensures correct conversation routing.

```
Anonymous Visitor
  │  No email, no user_id
  │  Auto-generated visitor ID (getVisitorId())
  │
  ▼ (user submits email in Messenger or via update())
Lead
  │  Has email, no user_id
  │  Stored as a Lead in Intercom
  │
  ▼ (user authenticates; boot() called with user_id)
User
     Has user_id (and usually email)
     Full contact record in Intercom
```

### Retrieving the Visitor ID

```javascript
const visitorId = window.Intercom('getVisitorId');
```

Use this to associate pre-authentication activity with the eventual user record. Pass `visitorId` to your server when the user signs up so you can link the anonymous session.

### Converting a Visitor to a Lead

```javascript
// Visitor provides email (e.g., in a lead capture form)
window.Intercom('update', {
  email: 'prospect@example.com',
});
```

### Converting a Lead to a User

```javascript
// After authentication, boot with user_id
window.Intercom('boot', {
  app_id: 'YOUR_APP_ID',
  user_id: authenticatedUser.id,
  email: authenticatedUser.email,
  intercom_user_jwt: tokenFromServer,
});
```

Calling `boot()` with a `user_id` that matches an existing Lead merges the records.

---

## Data Update Patterns

Use `update()` to change user or company attributes after the initial `boot()` call. This is appropriate for attribute changes that occur during a session — plan upgrades, profile edits, feature flag changes.

```javascript
window.Intercom('update', {
  subscription_tier: 'enterprise',
  seats_used: 12,
  last_upgraded_at: Math.floor(Date.now() / 1000),
});
```

### Throttle Limits

Intercom enforces a limit of 20 `update()` calls per 30-minute window per user. Exceeding this limit causes subsequent calls to be silently dropped.

Update on meaningful state changes — plan upgrades, role changes, significant feature interactions. Do not call `update()` on every keystroke, scroll event, or minor UI interaction.

### Null and Empty Values

| Value passed | Displayed in Intercom |
|---|---|
| `''` (empty string) | "Unknown" |
| `'undefined'` (string) | "Unknown" |
| `'null'` (string) | "Unknown" |
| `null` | Clears the attribute |
| `undefined` | Attribute unchanged |

Pass `null` explicitly to clear an attribute. Avoid passing the string `"null"` or `"undefined"` — these are treated as literal unknown values, not as clearing operations.

---

## Security Checklist

Follow these practices for every production deployment that uses identity verification.

- Generate JWT or HMAC server-side only. The secret key must never appear in frontend JavaScript, environment variables accessible to the browser, or version control.
- Validate the user's identity on your server before signing the token or hash. Confirm the requesting session belongs to the claimed `user_id` before generating the proof.
- Use short-lived JWTs. Set `exp` to 1 hour or less. Implement a token refresh endpoint that the frontend calls before expiry.
- Serve all pages over HTTPS. Identity verification tokens transmitted over HTTP are vulnerable to interception.
- Rotate the Intercom secret key if it is ever exposed. Generate a new key in Settings → Security and redeploy all server-side signing code.
- Do not log JWT or HMAC values in application logs. Treat them as credentials.
- Audit `user_id` values before signing. Ensure users cannot manipulate the identifier passed to your signing endpoint to obtain a token for another user's ID.
