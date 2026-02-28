# Authentication Security

Sources: OWASP Authentication Cheat Sheet, OWASP CSRF Prevention Cheat Sheet, OWASP Top 10 (2021), RFC 6819 (OAuth2 Threat Model), NIST SP 800-63B, descope.com JWT storage guide, Curity JWT best practices

Covers: Token storage, XSS and CSRF defense, credential stuffing prevention, rate limiting, secure headers, auth endpoint hardening, and common auth vulnerability patterns.

## Token Storage Decision

Where tokens live determines their attack surface. There is no universally correct choice — trade-offs are real.

### Browser Storage Options

| Storage | JavaScript Access | XSS Stealable | CSRF Vulnerable | Notes |
|---------|------------------|---------------|-----------------|-------|
| `localStorage` | Yes | Yes | No | Common but dangerous |
| `sessionStorage` | Yes | Yes | No | Cleared on tab close; still XSS vulnerable |
| Memory (JS variable) | Yes | Yes (via global) | No | Lost on page refresh |
| HttpOnly cookie | No | No | Yes (mitigated by SameSite) | Best for tokens |
| Non-HttpOnly cookie | Yes | Yes | Yes | Worst of both worlds |

### Decision Matrix

| Situation | Recommendation |
|-----------|---------------|
| Access token in browser app | HttpOnly, Secure, SameSite=Lax cookie |
| Refresh token in browser app | HttpOnly, Secure, SameSite=Strict cookie |
| Token in mobile app (iOS) | Keychain (iOS Secure Enclave backed) |
| Token in mobile app (Android) | Keystore (hardware-backed where available) |
| Token in server-side app | Environment variable or secret manager; memory at runtime |
| Token in CLI tool | OS credential store (keychain, secretservice, Credential Manager) |

**localStorage is not an acceptable token store for production applications.** Any XSS vulnerability — including through third-party scripts — can extract all tokens from localStorage.

### HttpOnly Cookie Pattern

```
Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/api; Max-Age=900
Set-Cookie: refresh_token=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/auth/token; Max-Age=2592000
```

Scope the refresh token cookie to the token endpoint path (`/auth/token`). This prevents the refresh token from being sent with every API request.

### Token Handler Pattern (BFF)

For SPAs that need API access without exposing tokens to JavaScript:

```
Browser (SPA) ←── HttpOnly cookies ──→ Backend-for-Frontend (BFF)
                                            │
                                       Bearer token in memory
                                            │
                                        API servers
```

The BFF receives cookies from the browser, extracts tokens server-side, and forwards them as Bearer headers to the actual API. The browser JavaScript never touches a token.

## XSS (Cross-Site Scripting) Defense

XSS allows attackers to inject JavaScript into your pages. If tokens are in localStorage, XSS = token theft. Defense is layered.

### Content Security Policy (CSP)

CSP instructs browsers which scripts are permitted. Reduces XSS blast radius.

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{RANDOM_PER_REQUEST}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none'
```

| CSP Directive | Effect |
|---------------|--------|
| `default-src 'self'` | Block all resources not from same origin by default |
| `script-src 'nonce-...'` | Only scripts with this per-request nonce execute |
| `frame-ancestors 'none'` | Prevent clickjacking (equivalent to X-Frame-Options: DENY) |
| `upgrade-insecure-requests` | Upgrade HTTP sub-resources to HTTPS |

Avoid `unsafe-inline` and `unsafe-eval` in `script-src` — they defeat most XSS protection.

### Input Sanitization

- Sanitize all user-supplied data before rendering in HTML (encode HTML entities)
- Use framework-provided templating (React JSX, Angular's binding) — they escape by default
- Treat any value inserted into a page as untrusted unless you explicitly trusted it
- Sanitize rich text with a purpose-built library (DOMPurify) rather than regex

### Subresource Integrity (SRI)

If loading scripts from CDNs, add `integrity` attributes to verify the exact file content:

```html
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-<hash>"
        crossorigin="anonymous"></script>
```

A compromised CDN serving a modified script will not execute if the hash does not match.

## CSRF (Cross-Site Request Forgery) Defense

CSRF tricks a logged-in user's browser into sending a forged request to your app. If your auth uses cookies, CSRF is relevant.

### Modern Defense: SameSite Cookie

`SameSite=Lax` prevents cookies from being sent on cross-origin POST requests (the most common CSRF vector). This is the first-line defense.

```
Set-Cookie: sessionid=X; SameSite=Lax; Secure; HttpOnly
```

`SameSite=Strict` prevents cookies on any cross-origin request including GET navigation. Stronger but breaks some OAuth2 redirect flows.

### Synchronizer Token Pattern (Double Submit)

For legacy browsers without SameSite support, or APIs that accept cross-origin requests intentionally:

```
1. Server generates CSRF token (random, tied to session)
2. Server includes CSRF token in page (in form or meta tag)
3. Client sends token in custom header (X-CSRF-Token) or form field
4. Server validates: does submitted token match session's CSRF token?
```

Custom headers (`X-CSRF-Token`, `X-Requested-With`) cannot be set by cross-origin forms — only JavaScript can set them, and JavaScript respects same-origin policy for these headers.

### Cookie-to-Header Token

A simple CSRF pattern for SPAs using cookies:

```
Server sets: Set-Cookie: csrf_token=RANDOM; SameSite=Strict; Secure; (not HttpOnly — JS must read it)
Client reads cookie and sends: X-CSRF-Token: RANDOM
Server validates: does X-CSRF-Token header equal csrf_token cookie?
```

This works because a cross-origin attacker's JavaScript cannot read the cookie (same-origin policy), only the victim's JavaScript can.

## Rate Limiting on Auth Endpoints

Auth endpoints are the primary attack surface for credential stuffing, brute force, and enumeration.

### Endpoints to Rate Limit

| Endpoint | Limit | Strategy |
|----------|-------|----------|
| `POST /login` | 5-10 attempts per username per 15 minutes | Per-username + per-IP |
| `POST /register` | 10 per IP per hour | Per-IP |
| `POST /forgot-password` | 3 per IP per hour | Per-IP (prevent enumeration) |
| `POST /auth/token` (OAuth) | 20 per client per minute | Per-client-id |
| `POST /verify-otp` | 5 per session | Per-session + lockout |
| `POST /verify-backup-code` | 5 attempts | Per-user, then require support |

### Progressive Delays (Exponential Backoff)

After the first failed login, introduce increasing delays before the next attempt is processed:

```
Attempt 1: immediate
Attempt 2: 200ms delay
Attempt 3: 500ms delay
Attempt 4: 1s delay
Attempt 5: 2s delay, CAPTCHA required
Attempt 10: account temporarily locked (30 minutes)
```

Delays are applied server-side — client sees the delay but cannot skip it.

### Account Lockout vs Soft Lock

| Approach | Pros | Cons |
|----------|------|------|
| Hard lockout | Stops brute force definitively | Enables denial-of-service (attacker locks out legitimate users) |
| Soft lock + CAPTCHA | Limits automated attacks without enabling DoS | CAPTCHA solvable by humans (and some ML) |
| Notification only | No lockout — just alert user | Brute force continues silently |

Prefer soft lock + CAPTCHA for consumer apps. Hard lockout on OTP endpoints (5 attempts max).

## Credential Stuffing Prevention

Credential stuffing uses username/password pairs from data breaches to attempt logins at scale.

### Detections

| Signal | Action |
|--------|--------|
| High volume from single IP | Block IP, alert security team |
| High volume for single user | Soft lock + notify user |
| Multiple IPs for single user in short window | Flag for review |
| Login from new country/device | Step-up authentication or notification |
| IP in Tor exit node / known proxy | Require CAPTCHA or block |

### Mitigation

- Check passwords against breached credential databases (HaveIBeenPwned API) at login and password change
- Implement device fingerprinting — flag first login from new device
- Use CAPTCHA for login after failures (recaptcha, Turnstile, hCaptcha)
- Log and monitor login patterns; alert on anomalies
- Implement anomaly-based rate limiting (not just per-IP — distributed attacks use many IPs)

## Secure Auth Headers

Set these headers on every response, especially auth pages.

| Header | Value | Effect |
|--------|-------|--------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforce HTTPS; prevent SSL stripping |
| `X-Frame-Options` | `DENY` | Prevent clickjacking (fallback if CSP not set) |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Prevent auth tokens leaking in Referer header |
| `Cache-Control` | `no-store` | Prevent browser caching of auth pages/responses |
| `Content-Security-Policy` | (see above) | XSS defense |

Add `no-store` to token endpoint responses specifically — browsers and proxies must not cache tokens.

## Password Security (If Passwords Are Used)

### Hashing Requirements (NIST SP 800-63B)

| Property | Requirement |
|----------|-------------|
| Algorithm | bcrypt (cost 12+), Argon2id, or scrypt |
| Never use | MD5, SHA-1, SHA-256 (without key stretching) — all crackable |
| Salt | Automatically handled by bcrypt/Argon2 |
| Minimum length | 8 characters (require), allow up to 64+ |
| Composition rules | Not required by NIST — checking against breach lists is more effective |
| Password hints | Never store or display |

### Password Policy (NIST 2024 Guidance)

- Check new passwords against known breached lists (HaveIBeenPwned)
- Allow long passwords (64+ characters) and paste — password managers need this
- Do not require arbitrary complexity rules (uppercase + special char) — they produce predictable patterns
- Do not expire passwords on a schedule — expire only on known breach
- Allow all printable ASCII characters and unicode in passwords

## Common Auth Vulnerabilities Quick Reference

| Vulnerability | Description | Prevention |
|---------------|-------------|-----------|
| Broken authentication | Weak session IDs, missing expiry | Use CSPRNG, enforce expiry, rotate on login |
| Token in URL | Tokens in query params appear in logs and Referer | Never put tokens in URLs |
| No HTTPS | Auth credentials transmitted in cleartext | Enforce HTTPS + HSTS |
| Verbose error messages | "User not found" enables enumeration | Return same message for wrong user/password |
| Insecure password reset | Predictable reset tokens, no expiry | CSPRNG token, 1-hour expiry, one-time use |
| JWT none algorithm | Forged token accepted | Pin algorithm server-side |
| Open redirect after login | Login?next=https://evil.com | Validate redirect URLs against allowlist |
| Mass assignment | User sets their own `role` in request body | Never bind user input directly to auth models |
| Long-lived refresh tokens | Leaked refresh tokens reusable indefinitely | Rotate on use; revoke on logout |
| No MFA for admin | Admin accounts compromised via credential stuffing | Enforce MFA for all privileged accounts |
