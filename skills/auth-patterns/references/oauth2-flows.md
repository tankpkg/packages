# OAuth2 Flows

Sources: RFC 6749 (OAuth2), RFC 7636 (PKCE), RFC 8628 (Device Authorization), RFC 7009 (Token Revocation), RFC 8707 (Resource Indicators), OAuth 2.0 Security BCP (draft-ietf-oauth-security-topics), Auth0 documentation, Authgear engineering blog

Covers: All OAuth2 grant types with selection guidance, PKCE mechanics, token endpoint, scope design, M2M authentication, refresh token rotation, and deprecated flows.

## OAuth2 Core Concepts

OAuth2 is an authorization framework — it delegates access, not identity. OAuth2 answers "what can this client access?" not "who is this user?" (that is OIDC's job).

### Key Roles

| Role | Definition | Example |
|------|-----------|---------|
| Resource Owner | The user who owns the protected data | End user |
| Client | Application requesting access | Web app, mobile app, CLI |
| Authorization Server | Issues tokens after authenticating resource owner | Auth0, Keycloak, your auth service |
| Resource Server | Holds the protected resources | Your API |

### Two Channel Types

| Channel | Description | Used For |
|---------|-------------|----------|
| Front channel | Browser redirects (URL parameters) | Authorization endpoint — user interaction |
| Back channel | Direct HTTP calls (body parameters) | Token endpoint — machine communication |

Never send credentials or tokens in front-channel redirects — they appear in browser history, logs, and referrer headers.

## Grant Types

### 1. Authorization Code (Web Apps)

Best for: Server-side web apps with a backend that can keep a client secret.

```
1. Client → Auth Server: GET /authorize
   ?response_type=code
   &client_id=CLIENT_ID
   &redirect_uri=https://app.example/callback
   &scope=openid profile email
   &state=RANDOM_STATE

2. User authenticates + consents at Auth Server

3. Auth Server → Client: GET /callback?code=AUTH_CODE&state=STATE

4. Client → Auth Server: POST /token
   grant_type=authorization_code
   &code=AUTH_CODE
   &redirect_uri=https://app.example/callback
   &client_id=CLIENT_ID
   &client_secret=CLIENT_SECRET

5. Auth Server → Client: { access_token, refresh_token, expires_in }
```

**State parameter**: Generate cryptographically random value. Store in session before redirect. Verify on callback. Prevents CSRF against the OAuth flow itself.

**Redirect URI**: Must match exactly (including trailing slash) against a pre-registered allowlist. Wildcard URIs are a security risk.

### 2. Authorization Code + PKCE (SPA / Mobile)

Best for: Any client that cannot securely store a client secret (single-page apps, mobile apps, desktop apps).

PKCE (Proof Key for Code Exchange, RFC 7636) prevents authorization code interception attacks. Required for all public clients.

**PKCE mechanics**:

```
Step 1 — Client generates:
  code_verifier = base64url(random_bytes(32))   # 43-128 chars
  code_challenge = base64url(sha256(code_verifier))

Step 2 — Client sends challenge with authorization request:
  GET /authorize?...&code_challenge=CHALLENGE&code_challenge_method=S256

Step 3 — Auth server stores challenge, issues code

Step 4 — Client sends verifier with token request:
  POST /token
    grant_type=authorization_code
    &code=AUTH_CODE
    &code_verifier=VERIFIER   # not the hash — the original value
    &client_id=CLIENT_ID
    # no client_secret for public clients

Step 5 — Auth server computes sha256(verifier) and compares to stored challenge
```

If an attacker intercepts the authorization code, they cannot exchange it without the `code_verifier`, which was never sent over the network.

**code_challenge_method**: Always use `S256`. Plain (no hashing) defeats the purpose and should be rejected by conformant servers.

### 3. Client Credentials (Machine-to-Machine)

Best for: Service-to-service communication where no user is involved. Backend microservice calling another microservice.

```
POST /token
  grant_type=client_credentials
  &client_id=SERVICE_A_ID
  &client_secret=SERVICE_A_SECRET
  &scope=service:read service:write

Response: { access_token, expires_in, token_type }
```

No refresh token is issued — tokens are short-lived and re-requested as needed.

**Secret management**: Rotate client secrets without downtime using overlapping validity windows. Store secrets in secret management systems (Vault, AWS Secrets Manager), not environment variables in code.

### 4. Device Authorization (Browserless Devices)

Best for: Smart TVs, CLI tools, IoT devices without a browser or limited input capability.

```
1. Device → Auth Server: POST /device/authorization
   &client_id=DEVICE_CLIENT_ID
   &scope=openid

   Response: {
     device_code: "DEVICE_CODE",
     user_code: "BDWP-HQTK",
     verification_uri: "https://example.com/device",
     expires_in: 1800,
     interval: 5
   }

2. Device: Display user_code + verification_uri to user
   "Go to https://example.com/device and enter: BDWP-HQTK"

3. User → Browser → Auth Server: navigates to verification_uri, enters user_code, authenticates

4. Device polls: POST /token
   grant_type=urn:ietf:params:oauth:grant-type:device_code
   &device_code=DEVICE_CODE
   &client_id=DEVICE_CLIENT_ID

   Responses:
   - authorization_pending: user hasn't completed login yet, keep polling
   - slow_down: increase polling interval by 5 seconds
   - access_denied: user denied
   - { access_token, refresh_token }: success
```

Poll at the specified `interval`. Honor `slow_down` responses immediately.

### Grant Type Selection Matrix

| Client Type | User Involved? | Can Store Secret? | Grant Type |
|-------------|---------------|-------------------|------------|
| Server-side web app | Yes | Yes | Authorization Code |
| Single-page app (SPA) | Yes | No | Authorization Code + PKCE |
| Native / mobile app | Yes | No | Authorization Code + PKCE |
| CLI tool (user present) | Yes | No | Device Authorization |
| Microservice / background job | No | Yes | Client Credentials |
| IoT device | Yes | No | Device Authorization |
| Legacy app (password grant) | — | — | **Deprecated — migrate away** |

### Deprecated and Forbidden Grants

| Grant | Status | Problem |
|-------|--------|---------|
| Implicit | Deprecated (RFC 9700) | Tokens in URL, no PKCE equivalent, token leakage |
| Resource Owner Password | Deprecated | App handles user credentials directly, bypasses SSO |

Do not implement implicit grant in new systems. Migrate existing implicit clients to Auth Code + PKCE.

## Token Endpoint

All token issuance happens at the token endpoint via `POST` with `application/x-www-form-urlencoded`.

### Request Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | The grant type being used |
| `code` | For auth code | The authorization code |
| `redirect_uri` | For auth code | Must match exact URI from authorization request |
| `code_verifier` | For PKCE | Original verifier string |
| `client_id` | Yes | Client identifier |
| `client_secret` | Confidential clients | Client secret (never in front channel) |
| `scope` | Optional | Requested scopes (subset of authorized) |
| `refresh_token` | For refresh | Refresh token to exchange |

### Token Response

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "8xLOxBtZp8",
  "scope": "openid profile email"
}
```

### Error Responses

| Error Code | Meaning |
|------------|---------|
| `invalid_request` | Malformed request |
| `invalid_client` | Client authentication failed |
| `invalid_grant` | Code expired, used, or wrong redirect_uri |
| `unauthorized_client` | Client not allowed for this grant type |
| `invalid_scope` | Requested scope not allowed |

## Scope Design

Scopes express what access is being requested. Design scopes for authorization decisions, not data retrieval.

### Scope Naming Patterns

| Pattern | Examples | Use Case |
|---------|---------|----------|
| `resource:action` | `posts:read`, `posts:write` | Fine-grained resource-action |
| `resource` | `profile`, `email` | OIDC standard scopes |
| `service:permission` | `payments:initiate` | Service-specific capability |
| Coarse | `admin`, `readonly` | Simple internal apps |

### Scope Best Practices

- Define scopes at the level of user consent — users see them on consent screens
- Separate read and write scopes (`files:read` vs `files:write`)
- Group related permissions for UX (`profile` instead of separate `name`, `birthdate` scopes)
- Do not create scopes per-user or per-resource — scopes are resource type + action
- Document every scope with a plain-language consent description
- Default to minimum scope; let users/clients request more

### Scope Validation

- Authorization server: validate requested scopes against client's registered allowed scopes
- Resource server: validate access token's scope before serving each request
- Return `403 Forbidden` with `WWW-Authenticate: Bearer error="insufficient_scope"` if scope is missing

## Token Revocation (RFC 7009)

```
POST /revoke
  token=REFRESH_OR_ACCESS_TOKEN
  &token_type_hint=refresh_token
  &client_id=CLIENT_ID
  &client_secret=CLIENT_SECRET
```

Revoke both access token and refresh token on logout. If only refresh token is revoked, old access tokens remain valid until expiry.

## Refresh Token Rotation

Issue a new refresh token on each use. Invalidate the previous one.

**Token family revocation** (detect stolen refresh tokens):

```
State machine:
  VALID: { refresh_token_A, family_id }
  
  Normal use:
    Use refresh_token_A → issue access_token + refresh_token_B
    Invalidate refresh_token_A
    State: VALID: { refresh_token_B, family_id }
  
  Replay attack detected:
    Use refresh_token_A (already invalidated) →
    Invalidate ALL tokens in family_id →
    User must re-authenticate
    (Signal: possible token theft)
```

## Client Registration Requirements

### Confidential Clients (have a secret)

- Register `client_secret` (treat like a password — hash stored, rotate periodically)
- Register exact `redirect_uris` (no wildcards)
- Register allowed `grant_types` and `response_types`
- Authenticate at token endpoint (HTTP Basic or POST body, not GET parameters)

### Public Clients (no secret)

- No `client_secret` — application is not able to keep secrets
- Register exact `redirect_uris` (critical — prevents authorization code theft)
- Must use PKCE for all authorization code requests
- Consider `dpop` (Demonstration of Proof-of-Possession) for additional binding

## Security Requirements Summary

| Requirement | Reason |
|-------------|--------|
| HTTPS on all endpoints | Prevents token interception |
| Exact redirect_uri matching | Prevents open redirect attacks |
| State parameter | CSRF protection for OAuth flow |
| PKCE for public clients | Prevents authorization code interception |
| Short-lived access tokens | Limits damage from token leakage |
| Opaque refresh tokens | Enables server-side revocation |
| Rotate refresh tokens | Detects token theft |
| Validate scope on resource server | Prevents scope escalation |
| Never log tokens | Prevents exposure in log aggregation |
| Reject implicit grant | Fragment-based tokens leak to referrers |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Wildcard redirect_uris | Attacker redirects code to their server | Exact URI matching only |
| No state parameter | CSRF vulnerability in OAuth flow | Always generate + verify state |
| Storing client_secret in mobile app | Easily extracted from binary | Use Authorization Code + PKCE (no secret) |
| Implicit grant for SPAs | Tokens in URL fragments leak | Migrate to Auth Code + PKCE |
| Long-lived access tokens | Extended exposure window if leaked | 5-15 minutes max |
| No refresh token rotation | Compromised refresh token reused indefinitely | Rotate on every use |
| Trusting scope from token without validation | Resource server skips authorization | Always check scope on resource server |
| Not validating redirect_uri on token exchange | Malicious code exchange | Verify redirect_uri matches authorization request |
