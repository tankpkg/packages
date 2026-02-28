# JWT Internals

Sources: RFC 7519 (JWT), RFC 7515 (JWS), RFC 7517 (JWK), RFC 8725 (JWT BCP), Curity Identity Server documentation, OWASP Authentication Cheat Sheet, CVE-2026-22817, CVE-2026-23993

Covers: JWT structure, signing algorithms and selection, validation procedure, attack vectors, access/refresh token patterns, token revocation, and expiry strategies.

## JWT Structure

A JWT is three Base64url-encoded segments joined by periods:

```
<header>.<payload>.<signature>
```

### Header

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-id-2024-01"
}
```

| Field | Purpose |
|-------|---------|
| `alg` | Signing algorithm — MUST be pinned server-side, never trusted from token |
| `typ` | Token type — always `JWT` for JWTs |
| `kid` | Key ID for key rotation — optional but recommended |
| `jku` | JWK Set URL — dangerous unless strictly allowlisted |

### Standard Claims (Payload)

| Claim | Name | Required | Description |
|-------|------|----------|-------------|
| `iss` | Issuer | Yes | Who issued the token |
| `sub` | Subject | Yes | Who the token represents |
| `aud` | Audience | Yes | Who the token is for |
| `exp` | Expiration | Yes | Unix timestamp, reject after this |
| `iat` | Issued At | Recommended | When token was created |
| `nbf` | Not Before | Optional | Reject before this timestamp |
| `jti` | JWT ID | For revocation | Unique ID for this token instance |

Register only non-sensitive data in payload — it is base64-encoded, not encrypted. Anyone with the token can decode the payload.

## Signing Algorithms

### Algorithm Comparison

| Algorithm | Type | Key Length | Speed | When to Use |
|-----------|------|------------|-------|-------------|
| HS256 | Symmetric HMAC-SHA256 | 256-bit secret | Fast | Single-service: same process signs and verifies |
| HS384 | Symmetric HMAC-SHA384 | 384-bit secret | Fast | Same as HS256, higher security margin |
| RS256 | Asymmetric RSA-SHA256 | 2048-4096 bit RSA | Slower | Multiple services: private key signs, public key verifies |
| ES256 | Asymmetric ECDSA-P256 | 256-bit EC | Fast | Like RS256 but smaller keys; requires careful implementation |
| EdDSA | Asymmetric Ed25519 | 256-bit EC | Fastest | New systems; best choice for asymmetric when library supports it |
| RS512 | Asymmetric RSA-SHA512 | 2048-4096 bit RSA | Slower | Regulatory requirement for SHA-512 |
| `none` | No signature | — | — | **Never use. Never accept.** |

### Selection Decision Tree

```
Do multiple services verify this token?
├── Yes → Use RS256, ES256, or EdDSA (asymmetric)
│   ├── Modern stack, library supports EdDSA → EdDSA (Ed25519)
│   ├── Need widest library compatibility → RS256
│   └── Small key size priority → ES256
└── No (single monolith or single service) → Use HS256
    └── Secret: cryptographically random, 256+ bits, rotated periodically
```

### HS256 Key Requirements

- Minimum 256 bits of entropy (32 random bytes)
- Generated with `crypto.randomBytes(32)` or OS random source
- Never derived from passwords or predictable values
- Treat as a database credential — rotate if compromised

### RS256 / EdDSA Key Management

- Sign only with private key (never distribute it)
- Verify with public key (safe to distribute, expose via JWKS endpoint)
- Rotate keys using `kid` field — serve old and new public keys simultaneously during rotation
- JWKS endpoint: `GET /.well-known/jwks.json`

## Validation Procedure

Validate in this exact order. Skip any step and the token is untrusted.

1. **Parse structure** — Confirm exactly 3 base64url segments separated by periods
2. **Decode header** — Parse JSON, extract `alg` and `kid`
3. **Pin the algorithm** — Reject if `alg` does not match your expected algorithm. Never use the header's `alg` to decide how to verify
4. **Decode payload** — Parse JSON claims
5. **Verify signature** — Using the pinned algorithm and correct key
6. **Check `exp`** — Reject if current time ≥ exp (allow ≤30s clock skew)
7. **Check `nbf`** — Reject if current time < nbf (if present)
8. **Check `iss`** — Reject if issuer does not match expected value
9. **Check `aud`** — Reject if audience does not include your service identifier
10. **Check revocation** — Query revocation list or Redis if token revocation is implemented

### Clock Skew Handling

Allow a tolerance window (≤30 seconds) for exp and nbf to handle distributed system clock drift. Document the tolerance value — larger values increase attack window.

## Attack Vectors

### None Algorithm Attack (Critical)

Attacker changes `"alg":"RS256"` to `"alg":"none"` and removes the signature. Vulnerable libraries skip verification for `none` algorithm.

**Prevention**: Pin the algorithm in code. Do not use the `alg` field from the token header to choose the verification method.

```
// WRONG: trusting the token's own alg field
verifyWith(token.header.alg, token, key)

// CORRECT: hardcoded or configuration-based
verifyWith("RS256", token, key)
```

### Algorithm Confusion Attack (RS256 → HS256)

Attacker takes your RS256 public key (which is public and safe to share) and signs a forged token using it as an HMAC-SHA256 secret with `"alg":"HS256"`. A naive library that trusts the `alg` header will attempt HMAC verification using the public key as the secret, which succeeds.

**Real CVEs**: CVE-2026-22817 (Hono framework, CVSS 8.2), CVE-2026-23993 (HarbourJwt Go library).

**Prevention**: Same as none attack — pin the algorithm. Never let the token header drive algorithm selection.

### `kid` Header Injection

If a server builds its key lookup query using the `kid` header value without sanitization, an attacker can inject SQL or path traversal:

```
"kid": "../../dev/null"  // makes key an empty string
"kid": "' UNION SELECT 'attacker_secret'"  // SQL injection
```

**Prevention**: Validate `kid` against an allowlist of known key IDs. Never use raw `kid` value in queries.

### `jku` / `x5u` Header Injection

If the server fetches the verification key from the URL in the `jku` header, an attacker hosts their own JWKS and signs a token with their private key pointing `jku` at their server.

**Prevention**: If using `jku`, maintain a strict allowlist of trusted JWKS URLs. Prefer embedding public keys directly in configuration.

### JWT Brute Force (Weak HS256 Secret)

Short or guessable HMAC secrets can be brute-forced offline once the attacker has a valid token. Tools like `hashcat` can test billions of combinations per second.

**Prevention**: Use cryptographically random secrets ≥256 bits.

### Replay Attacks

A stolen token can be reused until it expires.

**Prevention options**:
- Short expiry (access tokens: 5-15 minutes)
- Bind token to client IP or user agent (impractical for mobile)
- Use `jti` claim + server-side revocation blacklist (negates stateless benefit)
- Refresh token rotation with one-time-use semantics

## Access Token vs Refresh Token Pattern

JWTs are suitable for access tokens but problematic as refresh tokens without additional controls.

| Dimension | Access Token | Refresh Token |
|-----------|-------------|---------------|
| Lifespan | 5-15 minutes | 30 days to 90 days |
| Storage (browser) | HttpOnly cookie | HttpOnly cookie |
| Storage (mobile) | OS secure storage | OS secure storage |
| Sent to | Every API request | Only token endpoint |
| Revocable | Difficult (stateless) | Yes (server-side) |
| JWT format | Common | Opaque preferred |

### Access Token Lifespan Trade-offs

| Lifespan | Security | UX |
|----------|----------|----|
| < 5 min | High (short compromise window) | Frequent refreshes |
| 5-15 min | Balanced | Acceptable |
| 30-60 min | Medium | Smooth |
| > 1 hour | Low (long exposure if leaked) | Very smooth |
| Non-expiring | Critical risk | No UX benefit justifies this |

### Refresh Token Rotation

Rotate refresh tokens on each use. Issue a new refresh token with every access token refresh. Invalidate the old refresh token. If an old refresh token is presented (replay attempt), invalidate the entire token family.

```
POST /auth/token
  → validate refresh_token
  → invalidate refresh_token
  → issue new access_token + new refresh_token
  → if refresh_token already used → invalidate ALL tokens for user (family revocation)
```

## Token Revocation Strategies

| Approach | Mechanism | Latency | Complexity |
|----------|-----------|---------|------------|
| Short expiry | Tokens expire naturally | None | None |
| Blacklist (Redis) | Store `jti` of revoked tokens | Milliseconds | Redis dependency |
| Version claim | Include version in token; server tracks current version | Milliseconds | DB lookup per request |
| Token introspection | POST /introspect — resource server checks with auth server | Network RTT | External dependency |
| Opaque tokens | Stateful tokens, server looks up session on every request | DB lookup | Full server-side state |

For most use cases: short-lived access tokens + opaque refresh tokens with server-side revocation is the right balance.

## JWT Pitfalls

| Pitfall | Risk | Fix |
|---------|------|-----|
| Storing sensitive data in payload | Data exposed to anyone with the token | Only store non-sensitive IDs; fetch sensitive data server-side |
| No `exp` claim | Token valid forever if leaked | Always set expiry |
| Symmetric secret too short | Brute-forceable | 256+ bits of random entropy |
| Trusting `alg` header | Algorithm confusion attack | Pin algorithm in code |
| Storing in localStorage | XSS can steal token | Use HttpOnly cookie |
| Including user roles in payload | Stale permissions after role change | Short expiry or introspection |
| Self-signed for auth without validation | Any token accepted | Validate issuer, audience, signature |
| JWT as session replacement everywhere | Adds complexity without benefit | Use sessions for traditional web apps |

## When NOT to Use JWT

JWT fits stateless API authorization. It is the wrong tool for:

| Scenario | Better Alternative |
|----------|-------------------|
| Traditional web app with server-rendered pages | Server-side sessions + cookies |
| Revocation required on every logout | Opaque tokens with server-side sessions |
| Highly sensitive operations (banking, healthcare) | Opaque tokens with per-request validation |
| Simple single-server app | Server-side sessions (simpler, auditable) |

Prefer JWTs when: multiple independent services need to verify the token without calling a central authority, and short expiry makes revocation acceptable.
