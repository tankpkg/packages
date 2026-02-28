# OpenID Connect and Social Login

Sources: OpenID Connect Core 1.0 specification, RFC 6749 (OAuth2), OWASP Authentication Cheat Sheet, Ory engineering blog (secure account linking), OpenID Connect Discovery 1.0 specification, Google Identity Platform documentation

Covers: OIDC protocol layer over OAuth2, ID tokens, nonce, standard scopes, social provider integration patterns, user mapping, account linking, edge cases, and JIT provisioning.

## What OIDC Adds to OAuth2

OAuth2 handles authorization (what can this client access?). OpenID Connect adds authentication (who is this user?) on top of OAuth2.

| Capability | OAuth2 | OAuth2 + OIDC |
|------------|--------|---------------|
| Access token for APIs | Yes | Yes |
| Refresh token | Yes | Yes |
| User identity | No | Yes — via ID token |
| User profile data | No | Yes — via UserInfo endpoint |
| Standard logout | No | Yes — via RP-initiated logout |
| Session management | No | Yes — via front-channel logout |
| Provider discovery | No | Yes — via `.well-known/openid-configuration` |

OIDC is not a replacement for OAuth2. It runs on top of it, adding the `openid` scope and new endpoints.

## ID Token vs Access Token

| Dimension | ID Token | Access Token |
|-----------|----------|--------------|
| Audience (`aud`) | Your client (the relying party) | Your API / resource server |
| Purpose | Prove who authenticated and when | Authorize resource access |
| Format | Always JWT | JWT or opaque |
| Validate at | Your backend after auth code exchange | Resource server on every API call |
| Contains | Identity claims (sub, name, email, nonce) | Scopes, client_id, resource permissions |
| Send to API | Never | Yes — in Authorization header |

**Common mistake**: Sending the ID token to your API as a bearer token. The API cannot validate it correctly — it is not its intended audience. Use the access token for API calls; use the ID token only to establish the local session.

## ID Token Structure

An ID token is a JWT with these required claims:

| Claim | Required | Description |
|-------|----------|-------------|
| `iss` | Yes | Issuer — identity provider URL |
| `sub` | Yes | Subject — stable, unique user identifier at this provider |
| `aud` | Yes | Audience — your client_id |
| `exp` | Yes | Expiration timestamp |
| `iat` | Yes | Issued-at timestamp |
| `nonce` | If provided in auth request | Replay attack protection |
| `auth_time` | If `max_age` requested | When user last authenticated |
| `acr` | Optional | Authentication Context Class — method used (password, mfa) |
| `amr` | Optional | Authentication Methods References — `["pwd","otp"]` |

Additional claims from scopes: `name`, `given_name`, `family_name`, `email`, `email_verified`, `picture`, `locale`.

## Nonce — Replay Attack Prevention

The nonce ties an ID token to a specific authorization request. Without it, a captured ID token can be replayed.

```
Step 1 — Client generates:
  nonce = base64url(crypto.randomBytes(16))
  Store nonce in session: session.nonce = nonce

Step 2 — Include in authorization request:
  GET /authorize?...&nonce=NONCE_VALUE

Step 3 — Provider embeds nonce in ID token:
  { ..., "nonce": "NONCE_VALUE" }

Step 4 — Client validates:
  if id_token.nonce != session.nonce: reject
  Delete session.nonce (one-time use)
```

Always validate the nonce for flows that return an ID token.

## ID Token Validation Sequence

Validate the ID token completely before trusting any claims.

1. Fetch the provider's JWKS from `/.well-known/openid-configuration` → `jwks_uri`
2. Match the ID token's `kid` header to the correct public key in JWKS
3. Verify signature using that key and the pinned algorithm
4. Confirm `iss` matches the expected issuer URL exactly
5. Confirm `aud` contains your `client_id`
6. Check `exp` — reject if expired (allow ≤30s clock skew)
7. Check `iat` — reject if too far in the past (optional max age)
8. Verify `nonce` matches value from session (if nonce was sent)
9. Check `email_verified: true` before treating email as confirmed identity

Skip any step and you are open to forged identity attacks.

## Standard Scopes and Claims

| Scope | Claims Returned | Use When |
|-------|----------------|----------|
| `openid` | `sub`, `iss`, `aud`, `exp`, `iat` | Always — required for OIDC |
| `profile` | `name`, `given_name`, `family_name`, `picture`, `locale` | Display name / avatar |
| `email` | `email`, `email_verified` | Email-based lookup or communication |
| `address` | `address` (structured) | Billing, shipping |
| `phone` | `phone_number`, `phone_number_verified` | SMS fallback, MFA |

Request only scopes you will use. Requesting unnecessary scopes harms user consent UX and collects data beyond purpose.

## Provider Discovery

OIDC providers publish their configuration at a well-known URL:

```
GET {issuer}/.well-known/openid-configuration

Returns JSON with:
  - issuer
  - authorization_endpoint
  - token_endpoint
  - userinfo_endpoint
  - jwks_uri
  - supported scopes, response types, claims
  - supported signing algorithms
```

Fetch and cache this document at startup. Refresh periodically (e.g., daily). Never hardcode endpoint URLs — they can change.

## Social Provider Integration Patterns

### Provider Comparison

| Provider | Protocol | Notes |
|----------|----------|-------|
| Google | OIDC | Returns `email_verified`. Sub is stable numeric string |
| GitHub | OAuth2 only (not OIDC) | No ID token. Must call `/user` and `/user/emails` endpoints |
| Apple | OIDC | ID token contains name only on first login. Sub is stable opaque string |
| Microsoft / Azure AD | OIDC | Use `tid` (tenant ID) claim for multi-tenant apps |
| Facebook | OAuth2 (not OIDC) | Returns user data from Graph API |

For providers that do not implement OIDC (GitHub, Facebook), treat the flow as OAuth2, fetch user data from their API, and manually map to your user model.

### User Identifier Strategy

| Field | Stable? | Safe as Primary Key? | Notes |
|-------|---------|---------------------|-------|
| `sub` (OIDC subject) | Yes | Yes — use this | Unique per provider, never changes |
| `email` | No | No | Users can change email; providers can reuse emails |
| Provider-scoped user ID | Yes | Yes | Same as sub in most OIDC providers |

Store users by `{provider}:{sub}` composite key. Never use email as the primary identifier for social logins.

### Minimal User Mapping

```
social_accounts table:
  provider          TEXT     -- "google", "github", "apple"
  provider_user_id  TEXT     -- the `sub` claim
  user_id           FK       -- your internal user ID
  email             TEXT     -- last known (may become stale)
  email_verified    BOOLEAN
  created_at        TIMESTAMP
  last_login_at     TIMESTAMP

UNIQUE (provider, provider_user_id)
```

## Account Linking

Account linking connects a social identity to an existing app account, enabling multiple login methods for one user.

### Linking Strategies

| Strategy | Trigger | Risk |
|----------|---------|------|
| Automatic by email | New social login matches existing account's email | Account takeover if email not verified |
| Manual by user | User explicitly links in settings | Safe — user consent required |
| Prompt on conflict | New social login conflicts — offer to link | Good UX balance |

**Critical rule**: Never automatically link accounts based on unverified email. An attacker controls a social provider, creates an account with victim's email, and gains access to victim's app account.

Safe automatic linking only when:
- `email_verified: true` in the ID token
- Your existing account's email is also verified
- You require the user to be currently logged in to link

### Secure Linking Flow

```
1. User is logged in to your app
2. User initiates "Connect Google" from settings
3. OAuth2 + PKCE flow to Google
4. Receive ID token — verify signature, nonce, audience
5. Check email_verified is true
6. Check: does this Google sub already link to a different user?
   → If yes: reject (social account already claimed by another user)
7. Insert row into social_accounts table
8. Confirm success to user
```

### Unlinking Constraints

Prevent users from unlinking their only login method (would lock them out). Require at least one remaining authentication method before permitting unlink.

## Edge Cases to Handle

| Edge Case | Behavior |
|-----------|----------|
| `email_verified: false` | Do not treat email as verified identity. Allow login by `sub` but flag account. Do not pre-fill email in profile. |
| User changes email at provider | New email appears in future logins. Update `email` field in `social_accounts` but keep `sub` as the key. |
| Provider deactivates user account | User will be denied at the provider's authorization step. Your app session expires naturally. |
| Provider deletes user data | Your stored profile data (name, email) becomes stale. Treat as reference data only, not source of truth. |
| Same email at two providers | Two separate social accounts; link only on explicit user action |
| Apple hides email with relay address | Store the relay address (`privaterelay.appleid.com`). It is stable for that user. |
| Provider revokes consent | Future token requests will fail. Present re-authorization prompt. |

## Just-in-Time (JIT) Provisioning vs Invitation

| Model | How Users Are Created | Use Case |
|-------|-----------------------|----------|
| JIT provisioning | Automatically on first social login | Public-facing apps, consumer |
| Invitation-only | Admin invites user; social login links to invitation | Enterprise, B2B, controlled access |
| Allowlist domain | JIT for `@company.com` email domain only | Internal corporate tools |

For enterprise apps: implement invitation-only with domain allowlist as an option. JIT without restriction allows anyone with a Google account to create an account.

## RP-Initiated Logout

To log out properly from both your app and the identity provider:

```
1. Invalidate your local session
2. Redirect to:
   {end_session_endpoint}
   ?id_token_hint={ID_TOKEN}
   &post_logout_redirect_uri={YOUR_CALLBACK}
   &state={RANDOM_STATE}

3. Provider logs out user from their session
4. Provider redirects back to your post_logout_redirect_uri
```

`end_session_endpoint` is in the discovery document. Not all providers implement it — fall back to clearing your session only if unavailable.

## Single Logout (SLO)

In SSO scenarios, logging out from one app should log out all apps sharing the SSO session.

| SLO Mechanism | How It Works | Support |
|--------------|-------------|---------|
| Front-channel logout | Provider loads logout URLs from each RP in hidden iframes | Widely supported; unreliable if user's browser blocks iframes |
| Back-channel logout | Provider POSTs logout token (JWT) to each RP's logout endpoint | More reliable; requires RPs to expose HTTPS endpoint |

Back-channel SLO is preferred for reliability. Implement a `POST /backchannel-logout` endpoint that validates the logout token and invalidates the corresponding session.
