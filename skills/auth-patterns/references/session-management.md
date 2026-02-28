# Session Management

Sources: OWASP Session Management Cheat Sheet, RFC 6265 (HTTP Cookies), NIST SP 800-63B Digital Identity Guidelines, WorkOS session management engineering blog, bughra.dev cookie security reference

Covers: Server-side session architecture, cookie security attributes, session ID generation, session fixation prevention, concurrent session controls, expiry strategies, and distributed session patterns.

## Session Architecture Fundamentals

A session links HTTP requests (stateless by design) to a specific authenticated user. Two fundamental models exist:

| Model | Mechanism | State Location | Example |
|-------|-----------|---------------|---------|
| Server-side session | Opaque session ID in cookie → server looks up state | Server (DB/Redis) | Traditional web apps |
| Client-side token | Self-contained signed token (JWT) | Client (cookie or storage) | Stateless APIs |
| Hybrid | Short-lived JWT + server-side session metadata | Both | Modern web apps with revocation |

Choose server-side sessions for traditional web apps, admin dashboards, and when immediate revocation is required. Choose client-side tokens for distributed APIs and microservices.

## Session Storage Backends

### In-Memory (Single Process)

| Property | Value |
|----------|-------|
| Latency | Microseconds |
| Persistence | None — sessions lost on restart |
| Scalability | Single process only |
| Use case | Development, single-instance toy apps |

Never use in-memory session storage for production clustered deployments.

### Redis

| Property | Value |
|----------|-------|
| Latency | Sub-millisecond |
| Persistence | Optional (AOF/RDB) |
| Scalability | Cluster mode supports horizontal scaling |
| Use case | Production web apps — the standard choice |

Configure Redis with a session TTL using `EXPIRE`. On session logout, explicitly `DEL` the key. Use Redis Cluster or Redis Sentinel for high availability.

### Relational Database

| Property | Value |
|----------|-------|
| Latency | 1-10ms |
| Persistence | Full (ACID guarantees) |
| Scalability | Vertical + read replicas |
| Use case | When audit trails are required or Redis is not available |

Index the session ID column. Run a periodic cleanup job to delete expired sessions — database does not auto-expire rows like Redis.

### Backend Selection

| Requirement | Recommended Backend |
|-------------|---------------------|
| High throughput (>1K RPS) | Redis |
| Full audit trail required | Relational DB |
| Multi-region deployment | Redis with replication |
| Session metadata queries | Relational DB |
| Simplest possible stack | Redis |

## Cookie Security Attributes

Every session cookie must include these attributes. Missing any of them is a security defect.

### Attribute Reference

| Attribute | Value | Protection | When to Set |
|-----------|-------|------------|-------------|
| `Secure` | Flag (no value) | Prevents transmission over HTTP | Always — even in dev (use localhost exception) |
| `HttpOnly` | Flag (no value) | Prevents JavaScript access (XSS protection) | Always |
| `SameSite` | `Lax`, `Strict`, or `None` | CSRF protection | Always |
| `Path` | `/` | Scopes cookie to path prefix | `/` for site-wide session |
| `Domain` | omit or specific | Scopes cookie to domain | Omit for exact domain match |
| `Max-Age` | Seconds | Cookie lifetime | Only for persistent cookies |
| `Expires` | Date | Cookie lifetime (older syntax) | Prefer `Max-Age` |

### SameSite Values Compared

| Value | Cross-site GET | Cross-site POST | Top-level navigation | CSRF Protection |
|-------|---------------|----------------|---------------------|-----------------|
| `Strict` | No | No | No | Maximum |
| `Lax` | Yes | No | Yes | Standard |
| `None` | Yes | Yes | Yes | None (requires Secure) |

**Default recommendation**: `SameSite=Lax` for most web apps. Provides CSRF protection while allowing cross-site navigation (clicking links from other sites works).

Use `SameSite=Strict` when a user following a link from another site always seeing a logged-out state is acceptable (banking, admin panels).

Use `SameSite=None; Secure` only when the cookie must be sent in cross-site contexts (embedded widgets, OAuth callbacks from other domains).

### Minimal Secure Cookie

```
Set-Cookie: sessionid=<value>; Secure; HttpOnly; SameSite=Lax; Path=/
```

### Persistent vs Session Cookies

| Type | Expires | Use Case |
|------|---------|----------|
| Session cookie | Browser close | Temporary authentication (no "remember me") |
| Persistent cookie | Specific date/time | "Remember me" functionality |

For persistent sessions, set `Max-Age` to the desired duration (e.g., `Max-Age=2592000` for 30 days). Always pair with server-side refresh token rotation.

## Session ID Generation

Session IDs must be unpredictable. An attacker who guesses or brute-forces a valid session ID hijacks the account.

### Requirements

| Property | Requirement | Reason |
|----------|-------------|--------|
| Entropy | ≥128 bits (16 bytes) | Prevents brute force within practical timescales |
| Randomness | CSPRNG (cryptographically secure) | `Math.random()` is not sufficient |
| Length (if hex) | 32 characters (128 bits) | Standard encoding |
| Length (if base64url) | 22 characters (≥128 bits) | Compact encoding |
| Uniqueness | Database-enforced UNIQUE constraint | Prevents collision |

### CSPRNG Sources by Language

| Language | CSPRNG |
|----------|--------|
| Node.js | `crypto.randomBytes(16)` |
| Python | `secrets.token_bytes(16)` |
| Java | `java.security.SecureRandom` |
| Go | `crypto/rand.Read()` |
| PHP | `random_bytes(16)` |
| Ruby | `SecureRandom.hex(16)` |

Never use:
- `Math.random()` (predictable)
- `rand()` in C (predictable without seeding)
- Timestamps as session IDs
- Sequential integers

### Session ID Rotation

Regenerate the session ID on privilege change events. Failure to do so is the session fixation vulnerability.

| Event | Required Action |
|-------|----------------|
| User logs in | Generate new session ID, copy session data |
| User elevates privilege (sudo/admin) | Generate new session ID |
| User's role changes | Generate new session ID |
| Logout | Invalidate session, delete from server |

## Session Fixation Attack

An attacker tricks a victim into using a session ID the attacker already knows. When the victim authenticates, the attacker's known session ID becomes valid.

**Attack flow**:
1. Attacker creates a session ID (sometimes by visiting the site)
2. Attacker tricks victim into using it (via URL parameter or cookie injection)
3. Victim logs in with that session ID
4. Attacker uses the same session ID to access victim's authenticated session

**Prevention**: Regenerate session ID on login (see above). This invalidates any pre-authentication session ID an attacker may have planted.

**Additional protection**: Reject session IDs that were not issued by your server. Bind session ID to a browser fingerprint (user-agent + IP) as a secondary check — but note IP binding breaks mobile users on cellular.

## Session Invalidation

### Logout

A correct logout implementation:

1. Read session ID from cookie
2. Delete session from server-side store (Redis DEL, DB DELETE)
3. Overwrite cookie with expired value:
   ```
   Set-Cookie: sessionid=; Secure; HttpOnly; SameSite=Lax; Max-Age=0; Path=/
   ```
4. Do not merely clear the cookie client-side — the server must invalidate the session

**Common mistake**: Only clearing the cookie on the client. The session remains valid on the server. An attacker who captured the cookie before logout can still use it.

### Administrative Session Termination

Implement admin-initiated session termination for:
- Account compromise response
- User account suspension
- Password change triggering all-session invalidation

Store session metadata (user ID, created at, last accessed, device/IP) to enable per-user or per-device session listing and revocation.

## Concurrent Session Management

| Policy | Behavior | Use Case |
|--------|----------|----------|
| Unlimited | Multiple simultaneous sessions allowed | Consumer apps, developer tools |
| Last-wins | New login invalidates oldest session | Email clients, most web apps |
| First-wins | New login rejected if session exists | High-security: banking, admin |
| Per-device | One active session per device type | Mobile apps with device tracking |
| N maximum | Allow up to N simultaneous sessions | Enterprise with device limits |

Implement concurrent session limits by tracking sessions per user in the session store. On new login, check count; apply policy before creating new session.

## Session Expiry

### Two-Timeout Model (NIST SP 800-63B Recommended)

| Timeout Type | Description | Behavior |
|-------------|-------------|----------|
| Idle timeout | Inactivity window | Session expires if no activity within window |
| Absolute timeout | Maximum session lifetime | Session expires regardless of activity |

Require re-authentication when either timeout is reached.

### Recommended Timeout Values by Application Risk

| Application Type | Idle Timeout | Absolute Timeout |
|-----------------|-------------|-----------------|
| High-risk (banking, healthcare, admin) | 5-10 minutes | 30-60 minutes |
| Standard (SaaS, e-commerce) | 30 minutes | 8 hours |
| Internal tools (low sensitivity) | 1 hour | 24 hours |
| "Remember me" / persistent | Days (on explicit consent) | 30-90 days |

### Sliding vs Absolute Expiry

| Approach | Behavior |
|----------|----------|
| Sliding only | Resets on every request — active users never expire |
| Absolute only | Expires at fixed time — disruptive for active users |
| Hybrid (recommended) | Both: sliding resets on activity, absolute caps total lifetime |

Implement hybrid: reset idle timer on each request, but track `session_created_at` and enforce absolute expiry regardless.

### Server-Side Expiry Implementation

```
On session lookup:
  session = store.get(session_id)
  if session is None: reject (expired or invalid)
  if now - session.last_active > idle_timeout: invalidate; reject
  if now - session.created_at > absolute_timeout: invalidate; reject
  session.last_active = now  # update sliding window
  store.set(session_id, session, ex=idle_timeout)
```

## Distributed Session Management

In clustered environments, sessions must be accessible to all instances.

### Options

| Approach | Mechanism | Pros | Cons |
|----------|-----------|------|------|
| Shared session store | All instances connect to Redis/DB | Consistent, revocable | External dependency |
| Sticky sessions | Load balancer pins user to same instance | Simple | Breaks on instance failure |
| Cookie-based session (JWE) | Encrypted session state in cookie | Stateless | Revocation difficult; cookie size limits |
| Database session | Central DB for all instances | Familiar, auditable | Higher latency |

**Default recommendation**: Redis shared session store. Sticky sessions are an anti-pattern that makes deployments fragile.

### Redis Session Key Pattern

```
Key:   session:{session_id}
Value: JSON object { user_id, roles, created_at, last_active, ... }
TTL:   idle_timeout (refreshed on access)
```

Use a secondary index `user_sessions:{user_id}` → set of session IDs to enable per-user session listing and all-session invalidation on logout or password change.

## Session Security Checklist

| Check | Status |
|-------|--------|
| Session IDs are 128-bit CSPRNG values | — |
| `Secure` attribute set on session cookie | — |
| `HttpOnly` attribute set on session cookie | — |
| `SameSite=Lax` (or Strict) set | — |
| Session ID regenerated on login | — |
| Session ID regenerated on privilege escalation | — |
| Server-side invalidation on logout | — |
| Idle AND absolute timeouts enforced server-side | — |
| Session metadata stored for admin termination | — |
| Concurrent session policy enforced | — |
| Session store protected (auth, network ACL) | — |
