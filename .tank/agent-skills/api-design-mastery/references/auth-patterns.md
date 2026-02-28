# API Authentication and Authorization

Sources: RFC 6749 (OAuth 2.0), RFC 7519 (JWT), RFC 7523 (JWT for OAuth), RFC 9068 (JWT Profile for Access Tokens), RFC 7617 (HTTP Basic Auth), OWASP API Security Top 10, OAuth 2.0 Security Best Current Practice (draft-ietf-oauth-security-topics)

Covers: API key design and storage, JWT access + refresh token pattern, OAuth 2.0 flows (Authorization Code + PKCE, Client Credentials), RBAC, rate limiting algorithms and headers.

## Choosing an Auth Mechanism

| Mechanism | Client Type | Use Case |
|----------|------------|---------|
| API Key | Server-side code, machine clients | Service-to-service; simple public API access |
| JWT (short-lived access token) | Any | Stateless user auth; microservice identity |
| JWT + Refresh Token | Web / mobile apps | User sessions with automatic renewal |
| OAuth 2.0 Auth Code + PKCE | Web apps, mobile apps | User-delegated access to third-party resources |
| OAuth 2.0 Client Credentials | Backend services | Machine-to-machine with an authorization server |

## API Keys

### Generation

Generate API keys using a cryptographically secure random source:

```typescript
import crypto from 'node:crypto';

// 32 bytes = 256 bits of entropy, hex-encoded = 64 character string
const rawKey = crypto.randomBytes(32).toString('hex');
```

Prefix keys to communicate scope and environment at a glance:

```
sk_live_a3f8b2c1...    # secret key, production
sk_test_7d4e9f2a...    # secret key, test/sandbox
pk_live_b1c2d3e4...    # public/publishable key, production
```

### Storage

Never store the raw API key. Store a hash of it:

```typescript
import crypto from 'node:crypto';

function hashApiKey(rawKey: string): string {
  return crypto.createHash('sha256').update(rawKey).digest('hex');
}

// Database stores: hash, prefix, scope, created_at, last_used_at, expires_at
// Return the raw key ONCE to the user at creation time
```

Store with this metadata:
- `key_hash` — SHA-256 of raw key (for lookup)
- `key_prefix` — first 8 characters (so users can identify keys in a list)
- `scope` — what the key can do (`read:orders`, `write:orders`, `admin`)
- `created_at`, `last_used_at`, `expires_at`
- `description` — user-supplied label ("Production webhook key")

### Transport

Always send API keys in the `Authorization` header using the `Bearer` scheme:

```http
GET /orders
Authorization: Bearer sk_live_a3f8b2c1...
```

Some APIs use a custom header:

```http
X-API-Key: sk_live_a3f8b2c1...
```

Never accept API keys as query parameters — they appear in server access logs, browser history, and CDN logs:

```
GET /orders?api_key=sk_live_a3f8b2c1...   ❌ DO NOT DO THIS
```

### Rotation

Support multiple active keys per account so clients can rotate without downtime:

1. Client creates new key
2. Client updates their application to use the new key
3. Client verifies the new key works
4. Client revokes the old key

Keys should have an optional `expires_at`. Force rotation by setting a maximum lifetime for high-security contexts.

## JWT (JSON Web Tokens)

### Structure

A JWT is three Base64URL-encoded JSON objects joined by dots:

```
header.payload.signature
```

**Header** identifies the algorithm:
```json
{ "alg": "RS256", "typ": "JWT" }
```

**Payload** contains claims:
```json
{
  "sub": "user_42",
  "iss": "https://auth.example.com",
  "aud": "https://api.example.com",
  "exp": 1706745600,
  "iat": 1706744700,
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "role": "editor"
}
```

### Standard Claims

| Claim | Purpose | Requirement |
|-------|---------|------------|
| `sub` | Subject — the user or entity the token represents | Required |
| `iss` | Issuer — the authorization server URL | Required |
| `aud` | Audience — the resource server this token is for | Required |
| `exp` | Expiration — Unix timestamp; token invalid after this | Required |
| `iat` | Issued at — Unix timestamp | Required |
| `jti` | JWT ID — unique identifier for this token (enables revocation) | Recommended |
| `nbf` | Not before — token invalid before this timestamp | Optional |

### Algorithm Selection

| Algorithm | Key Type | Recommended |
|----------|---------|------------|
| RS256 | RSA asymmetric (public/private) | Yes — resource servers can verify with public key only |
| ES256 | Elliptic curve asymmetric | Yes — smaller keys than RSA, same security |
| HS256 | HMAC symmetric (shared secret) | Only when issuer and all verifiers are the same service |

Use RS256 or ES256 for any system where the token is verified by a different service than the one that issued it. HS256 requires sharing the secret with every verifier, which increases the attack surface.

### Access + Refresh Token Pattern

```
┌─────────────┐         ┌──────────────────┐
│  Client     │ ─POST /login──────────────► │  Auth Server  │
│             │ ◄─ access_token (15min) ─── │               │
│             │ ◄─ refresh_token (7 days) ── │               │
│             │                              └──────────────────┘
│             │ ─GET /orders──────────────► ┌──────────────────┐
│             │    Authorization: Bearer     │  Resource Server │
│             │    {access_token}            │                  │
│             │ ◄─ 200 OK ──────────────── │                  │
│             │                              └──────────────────┘
│             │ ─POST /token (refresh)──────► ┌──────────────────┐
│             │    grant_type=refresh_token   │  Auth Server     │
│             │ ◄─ new access_token ─────── │                  │
└─────────────┘                              └──────────────────┘
```

Storage rules:
- Access token: in memory only (JavaScript variable, not localStorage or sessionStorage)
- Refresh token: in an `httpOnly; Secure; SameSite=Strict` cookie — inaccessible to JavaScript

Expiry guidelines:
- Access token: 15 minutes to 1 hour
- Refresh token: 7 to 30 days (revoke on logout; rotate on use)

### Token Verification

```typescript
import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

const client = jwksClient({ jwksUri: 'https://auth.example.com/.well-known/jwks.json' });

async function verifyAccessToken(token: string): Promise<JwtPayload> {
  const decoded = jwt.decode(token, { complete: true });
  const key = await client.getSigningKey(decoded?.header.kid);
  
  return jwt.verify(token, key.getPublicKey(), {
    algorithms: ['RS256'],
    issuer: 'https://auth.example.com',
    audience: 'https://api.example.com',
  }) as JwtPayload;
}
```

## OAuth 2.0 Flows

### Authorization Code + PKCE

Use this flow when a user authorizes a client application to access resources on their behalf. PKCE (Proof Key for Code Exchange, RFC 7636) is mandatory for all public clients (SPAs, mobile apps).

```
1. Client generates:
   code_verifier = random 43-128 character string (URL-safe characters)
   code_challenge = base64url(sha256(code_verifier))

2. Redirect user to authorization server:
   GET https://auth.example.com/authorize
     ?response_type=code
     &client_id=my-app
     &redirect_uri=https://app.example.com/callback
     &scope=openid profile email
     &state=random_csrf_token
     &code_challenge=abc123...
     &code_challenge_method=S256

3. User authenticates and consents.
   Server redirects to: https://app.example.com/callback?code=AUTH_CODE&state=...

4. Client exchanges code for tokens:
   POST https://auth.example.com/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code
   &code=AUTH_CODE
   &redirect_uri=https://app.example.com/callback
   &client_id=my-app
   &code_verifier=original_verifier

5. Server returns:
   { "access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 3600 }
```

The `state` parameter must be validated on the callback to prevent CSRF attacks.

### Client Credentials

Use for server-to-server communication where no user is involved:

```http
POST /token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=client_credentials&scope=read:orders write:shipments
```

Response:

```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read:orders write:shipments"
}
```

Store `client_secret` in a secrets manager or environment variable. Never commit it to source control.

### Deprecated Flows — Do Not Use

| Flow | Problem | Replace With |
|------|---------|-------------|
| Implicit | Access token exposed in URL fragment; XSS risk | Authorization Code + PKCE |
| Resource Owner Password Credentials | Client receives user credentials directly | Authorization Code + PKCE |

## Scopes and RBAC

### OAuth Scopes

Scopes are coarse-grained permissions granted to a client application by the user. Format: `action:resource`:

```
read:profile
write:profile
read:orders
write:orders
admin:billing
```

Request minimal scopes. Ask only for what the current feature needs. Users and enterprises reject applications that request excessive permissions.

### Role-Based Access Control

Apply RBAC for user-level authorization within your own API (distinct from OAuth scopes, which govern client authorization):

```typescript
type Role = 'VIEWER' | 'EDITOR' | 'ADMIN';

const rolePermissions: Record<Role, string[]> = {
  VIEWER: ['read:own'],
  EDITOR: ['read:own', 'write:own', 'read:shared'],
  ADMIN:  ['read:all', 'write:all', 'manage:users'],
};

function hasPermission(user: { role: Role }, permission: string): boolean {
  return rolePermissions[user.role]?.includes(permission) ?? false;
}
```

Check both role AND resource ownership:

```typescript
const order = await db.orders.findById(orderId);
if (!order) throw new NotFoundError();

// Check the user can see THIS specific order, not just "some orders"
if (order.userId !== ctx.user.id && !hasPermission(ctx.user, 'read:all')) {
  throw new ForbiddenError('You do not have access to this order');
}
```

## Rate Limiting

### Rate Limit Headers

Include rate limit state on every response — not just 429:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 842
X-RateLimit-Reset: 1706745600
```

On limit exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706745600
```

### Rate Limit Strategies

| Strategy | Mechanism | Allows Bursts | Use When |
|---------|---------|-------------|---------|
| Fixed Window | Count requests per fixed time window | Yes — at boundary | Simplest; acceptable for most APIs |
| Sliding Window | Count requests in rolling window ending now | Somewhat | Smoother than fixed; moderate complexity |
| Token Bucket | Bucket refills at constant rate; each request consumes one token | Yes — up to bucket size | Allows short bursts; controls sustained rate |
| Leaky Bucket | Requests queued; processed at fixed rate | No — adds latency | Smooth output rate; adds queue overhead |

Token bucket is the standard choice. It permits legitimate burst traffic (a user submitting a form twice quickly) while enforcing sustained limits.

### Rate Limit Tiers

Different clients get different limits based on identity:

| Tier | Limit | Identified By |
|------|-------|--------------|
| Unauthenticated | 60 req/hour per IP | No credentials |
| Authenticated free | 1,000 req/hour | API key / JWT role |
| Paid | 10,000 req/hour | API key tier |
| Enterprise | Custom | Contract |
| Internal services | No limit | Internal IP / service token |

Apply aggressive limits on authentication endpoints (`/login`, `/token`) to prevent brute force attacks — independently of the general rate limit.

## Security Headers

Include on all API responses:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Cache-Control: no-store    # On sensitive endpoints (auth, account data)
```

### CORS

```typescript
app.use(cors({
  origin: ['https://app.example.com', 'https://admin.example.com'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Authorization', 'Content-Type', 'Idempotency-Key'],
  credentials: true,   // Required if using httpOnly cookies for refresh tokens
  maxAge: 86400,       // Cache preflight for 24 hours
}));
```

Never set `origin: '*'` with `credentials: true` — browsers block this combination.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| API key in query parameter | Logged in server access logs; cached by proxies | `Authorization` header only |
| Storing raw API key in database | Single breach exposes all keys | Store SHA-256 hash; return raw key once |
| JWT with no expiry | Stolen token is valid forever | Always set `exp`; access tokens ≤ 1 hour |
| Refresh token in localStorage | JavaScript can read it — XSS vulnerability | `httpOnly; Secure; SameSite=Strict` cookie |
| HS256 for multi-service JWT | All services share the same secret | RS256 with JWKS endpoint |
| Using Implicit flow | Access token in URL fragment; XSS risk | Authorization Code + PKCE |
| 401 for an authenticated user who lacks access | Misleads client into credential retry | 401 = not authenticated; 403 = not authorized |
| No rate limit on `/login` or `/token` | Enables brute force credential attacks | Tight limits on auth endpoints, independent of general limits |
| Checking role but not resource ownership | User A can access User B's data | Check both: role AND `resource.ownerId === user.id` |
| Committing `client_secret` to source control | Secret exposed in repository history | Secrets manager or environment variable only |
