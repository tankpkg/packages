---
name: "@tank/auth-patterns"
description: |
  Authentication and authorization patterns for any language or framework.
  Covers JWT internals (structure, algorithms, attacks, validation), OAuth2 grant
  types (Authorization Code, PKCE, Client Credentials, Device Code), session
  management (cookies, expiry, fixation, distributed), RBAC/ABAC/ReBAC (role
  modeling, authorization policies, Zanzibar), OpenID Connect and social login
  (ID tokens, account linking, provider patterns), MFA (TOTP, WebAuthn/passkeys,
  backup codes, step-up auth), and authentication security (XSS/CSRF, token
  storage, credential stuffing, rate limiting).

  Synthesizes RFC 6749, RFC 7519, RFC 6238, W3C WebAuthn Level 2, NIST SP
  800-63B, and OWASP Authentication/CSRF cheat sheets.

  Trigger phrases: "JWT", "OAuth2", "OAuth 2.0", "session management",
  "RBAC", "ABAC", "role-based access", "authorization model", "OpenID Connect",
  "OIDC", "social login", "MFA", "multi-factor authentication", "TOTP",
  "WebAuthn", "passkeys", "refresh token", "access token", "PKCE",
  "auth flow", "implement authentication", "implement auth", "sign in with",
  "cookie security", "HttpOnly", "SameSite", "token storage", "XSS auth",
  "CSRF protection", "credential stuffing", "account linking", "backup codes",
  "permission system", "login security", "password hashing"
---

# Auth Patterns

## Core Philosophy

1. **Authentication is not authorization** — Solve them separately. Authentication proves identity; authorization enforces what that identity may do.
2. **Default deny** — All resources are denied unless explicitly permitted. Never default allow.
3. **Shortest lifetime possible** — Access tokens: 5-15 minutes. Sessions: idle + absolute timeout. Backup codes: one use. Shorter lifetime = smaller breach window.
4. **Validate every input, every time** — JWT signature, expiry, issuer, audience, nonce. Skipping one check is the vulnerability.
5. **Store nothing sensitive client-side** — Tokens in HttpOnly cookies, secrets in secret managers, TOTP seeds encrypted at rest.

## Quick-Start: Common Problems

### "Which auth approach should I use?"

| App Type | Recommended |
|----------|------------|
| Server-rendered web app | Server-side sessions + HttpOnly cookie |
| SPA / mobile calling your own API | Auth Code + PKCE → short-lived JWT in HttpOnly cookie |
| Microservices (your API → your API) | Client Credentials → short-lived JWT |
| Third-party delegated access | Auth Code + PKCE with consent screen |
| "Sign in with Google/GitHub" | OIDC → Auth Code + PKCE |
→ See `references/oauth2-flows.md` and `references/jwt-internals.md`

### "My JWT implementation feels wrong"

1. Are you pinning the algorithm in code (not trusting the token header)? → Verify
2. Are you validating `iss`, `aud`, `exp`, and signature? → All four required
3. Where is the token stored? localStorage = wrong → move to HttpOnly cookie
4. Access token lifespan > 15 minutes? → Shorten it
→ See `references/jwt-internals.md`

### "I need to add MFA"

1. Pick primary method: TOTP (practical baseline) or WebAuthn/passkeys (phishing-resistant)
2. Always generate backup codes at enrollment
3. Implement step-up auth for sensitive operations (password change, payments)
→ See `references/mfa-implementation.md`

### "How do I model permissions?"

1. Start with RBAC — users → roles → permissions
2. Hitting role explosion? Move resource-specific access to ABAC
3. Sharing / collaboration model? Consider ReBAC (Zanzibar)
→ See `references/rbac-abac.md`

### "Social login edge cases are biting me"

- Use `sub` (not email) as the stable user identifier per provider
- Always check `email_verified: true` before trusting email
- Validate `nonce`, `iss`, `aud`, and signature on ID tokens
→ See `references/oidc-social-login.md`

## Decision Trees

### Token vs Session

| Signal | Use |
|--------|-----|
| Traditional server-rendered app | Server-side sessions |
| Immediate revocation required | Server-side sessions (or opaque tokens + introspection) |
| Multiple independent services verify token | JWT (asymmetric: RS256 or EdDSA) |
| Single service | JWT (symmetric: HS256) or sessions |
| "Stateless" is a hard requirement | JWT with short expiry + refresh rotation |

### JWT Signing Algorithm

| Situation | Algorithm |
|-----------|-----------|
| Multiple services verify | RS256 or EdDSA (Ed25519) |
| Single service, simple | HS256 with 256-bit random secret |
| New system, modern stack | EdDSA (fastest, most secure) |
| Widest library compatibility needed | RS256 |
| Never | `none`, MD5, SHA-1 |

### Authorization Model

| Signal | Model |
|--------|-------|
| Permissions map to job functions | RBAC |
| Access depends on resource/context attributes | ABAC |
| Sharing and ownership relationships drive access | ReBAC |
| Multi-tenant SaaS | RBAC + tenant-scoped namespacing |
| Role count > user count | Refactor to ABAC or hierarchy |

### MFA Method

| Context | Method |
|---------|--------|
| Privileged accounts, enterprise | Hardware key (FIDO2 roaming) |
| Consumer apps, best UX | Passkeys (synced FIDO2) |
| Practical baseline anywhere | TOTP authenticator app |
| Absolute last resort only | SMS OTP |

## Reference Files

| File | Contents |
|------|----------|
| `references/jwt-internals.md` | JWT structure, signing algorithms (RS256/HS256/EdDSA), validation steps, attack vectors (none alg, alg confusion, kid injection), access/refresh token patterns, revocation strategies |
| `references/oauth2-flows.md` | All grant types (Auth Code, PKCE, Client Credentials, Device Code), token endpoint, scope design, refresh token rotation, deprecated implicit grant |
| `references/session-management.md` | Server-side session storage (Redis vs DB), cookie security attributes (HttpOnly, Secure, SameSite), session ID generation, session fixation, concurrent sessions, expiry strategies |
| `references/rbac-abac.md` | RBAC levels (0-3), role explosion prevention, ABAC vs RBAC selection, ReBAC/Zanzibar model, multi-tenant authorization, permission modeling, enforcement patterns |
| `references/oidc-social-login.md` | OIDC on OAuth2, ID token vs access token, nonce, standard scopes, provider patterns, user mapping, account linking, edge cases, JIT provisioning |
| `references/mfa-implementation.md` | TOTP algorithm and storage, WebAuthn/passkeys registration and authentication flows, SMS weaknesses, backup codes, step-up authentication, recovery flows |
| `references/auth-security.md` | Token storage (HttpOnly cookies vs localStorage), XSS defense (CSP, SRI), CSRF prevention (SameSite, synchronizer tokens), rate limiting, credential stuffing, secure headers, password hashing |
