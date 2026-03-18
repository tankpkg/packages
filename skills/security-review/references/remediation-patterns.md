# Remediation Patterns

Sources: OWASP Prevention Cheat Sheet Series, MITRE CWE mitigations, NIST SP 800-53 security controls, CWE/SANS Top 25 remediation guidance

Covers: Fix patterns for injection, XSS, CSRF, SSRF, authentication, authorization, cryptography, deserialization, file handling, HTTP headers, error handling, and logging — one section per vulnerability class, with code examples showing the corrected implementation.

## Input Validation

Validate all input at every trust boundary. Treat all external data — HTTP parameters, headers, cookies, file uploads, API payloads — as untrusted until validated.

- **Allowlist over denylist.** Define exactly what is permitted; reject everything else. Denylists are incomplete by definition.
- **Validate type, length, range, and format.** A field accepting a user ID should accept only positive integers within a known range.
- **Server-side validation is mandatory.** Client-side validation is a UX convenience, not a security control.
- **Fail closed.** On validation failure, reject the input. Never attempt to sanitize and continue with malformed data.

| Input Type | Validation Rule |
|------------|----------------|
| Integer ID | Positive integer, within expected range (e.g., 1–2^31) |
| Email address | RFC 5321 format via library; max 254 characters |
| Username | Allowlist: `[a-zA-Z0-9_-]`, 3–32 characters |
| File upload | Magic bytes check, MIME type allowlist, max size |
| URL | Parse with URL library, validate scheme (https only), validate host against allowlist |
| Free text | Max length, strip null bytes; encode on output, not on input |

```python
import re
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

def validate_email(value: str) -> str:
    if not isinstance(value, str) or len(value) > 254:
        raise ValueError("Invalid email")
    if not EMAIL_PATTERN.match(value):
        raise ValueError("Invalid email format")
    return value.lower().strip()
```

## Parameterized Queries (SQL Injection Prevention)

Never construct SQL by concatenating or interpolating user-supplied values. Use parameterized queries or prepared statements in every language and framework.

```javascript
// Node.js (pg)
const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
```

```python
# Python (psycopg2)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

```go
// Go (database/sql)
row := db.QueryRowContext(ctx, "SELECT * FROM users WHERE id = $1", userID)
```

```java
// Java (PreparedStatement)
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);
ResultSet rs = ps.executeQuery();
```

ORMs do not eliminate injection risk when raw query methods (`raw()`, `query()`, `execute()`) are used. Apply the same discipline to those call sites.

## Output Encoding (XSS Prevention)

Encoding context determines the correct encoding function. Applying the wrong encoder for the context does not prevent XSS.

| Output Context | Correct Encoding |
|----------------|-----------------|
| HTML body | HTML entity encoding (`&`, `<`, `>`, `"`, `'`) |
| HTML attribute | HTML attribute encoding (quote all attributes) |
| JavaScript string | JavaScript string escaping (`\`, `"`, `'`, newlines) |
| URL parameter | Percent-encoding (`encodeURIComponent`) |
| CSS value | CSS hex encoding |

```jsx
// React: JSX auto-escapes text content — safe by default
function UserProfile({ name }) { return <div>{name}</div>; }

// When raw HTML is required: sanitize first with DOMPurify
import DOMPurify from 'dompurify';
function RichContent({ untrustedHtml }) {
  const clean = DOMPurify.sanitize(untrustedHtml, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href'],
  });
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

Deploy CSP as defense in depth. A strict policy limits the blast radius of any XSS that slips through:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'
```

## Command Injection Prevention

Never pass user-controlled data to a shell via string interpolation. The shell interprets metacharacters (`;`, `|`, `&`, `$`, `(`, `)`) as control characters.

```python
# Correct: list form, shell=False (default)
result = subprocess.run(["ls", "-la", validated_path], shell=False, capture_output=True, timeout=10)
```

```javascript
// Correct: execFile does not invoke a shell
const { execFile } = require('child_process');
execFile('convert', [inputPath, '-resize', '800x600', outputPath], callback);
```

If a shell is unavoidable, maintain an explicit allowlist of permitted values and validate against it before substitution. Never construct the command string from raw user input.

## SSRF Prevention

Server-Side Request Forgery allows attackers to make the server issue HTTP requests to internal infrastructure or cloud metadata endpoints.

1. **Allowlist permitted destinations.** Enforce an explicit list of permitted hosts.
2. **Block private and link-local IP ranges** before connecting.
3. **Resolve the hostname, validate the resolved IP, then connect.** Prevents DNS rebinding.
4. **Route outbound HTTP through a dedicated egress proxy** that enforces the allowlist at the network layer.

| Blocked Range | Description |
|---------------|-------------|
| `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | RFC 1918 private |
| `127.0.0.0/8` | Loopback |
| `169.254.169.254/32` | AWS/GCP/Azure metadata endpoint |
| `::1/128`, `fc00::/7` | IPv6 loopback and unique local |

```python
import ipaddress, socket, urllib.parse, httpx

ALLOWED_HOSTS = {'api.example.com', 'cdn.example.com'}

def safe_fetch(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("URL not permitted")
    addr = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        raise ValueError("Resolved IP is in a blocked range")
    return httpx.get(url, follow_redirects=False, timeout=10).content
```

## CSRF Prevention

Cross-Site Request Forgery tricks an authenticated user's browser into submitting a state-changing request to a site where they are logged in.

1. **`SameSite=Lax` or `SameSite=Strict` on session cookies.** `Strict` blocks the cookie on all cross-site requests; `Lax` allows top-level navigations.
2. **Synchronizer token pattern.** Server generates a per-session token, stores it server-side, and requires it in a request header or body field.
3. **Double-submit cookie.** Token stored in both a cookie and a request header; server verifies they match.

```
Set-Cookie: session=<token>; HttpOnly; Secure; SameSite=Lax; Path=/
```

```javascript
// Express: csurf middleware
app.use(csrf({ cookie: true }));
app.get('/transfer', (req, res) => res.render('transfer', { csrfToken: req.csrfToken() }));
// csurf validates req.body._csrf automatically on POST
```

```html
<form method="POST" action="/transfer">
  <input type="hidden" name="_csrf" value="<%= csrfToken %>">
</form>
```

## Authentication Hardening

### Password Storage

Never store passwords in plaintext or with reversible encryption. Never use MD5, SHA-1, or unsalted SHA-256 — they are too fast and trivially brute-forced.

| Algorithm | Recommended Parameters | Notes |
|-----------|----------------------|-------|
| Argon2id | `m=65536, t=3, p=4` | Preferred for new systems |
| bcrypt | cost factor 12 or higher | Widely supported |
| scrypt | `N=32768, r=8, p=1` | Acceptable alternative |

```python
from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

def hash_password(plaintext: str) -> str:
    return ph.hash(plaintext)

def verify_password(stored_hash: str, plaintext: str) -> bool:
    try:
        return ph.verify(stored_hash, plaintext)
    except Exception:
        return False
```

### Rate Limiting, Lockout, and Sessions

- Limit login attempts to 5 per minute per IP and per account; apply exponential backoff after failures.
- Use temporary lockout (15 minutes), not permanent — permanent lockout enables denial-of-service.
- Return the same error message for invalid username and invalid password to prevent user enumeration.
- Regenerate the session ID immediately after successful login.
- Set an absolute session timeout (8 hours) and an idle timeout (30 minutes).
- Invalidate the session server-side on logout — do not merely clear the client-side cookie.

## Authorization Enforcement

Authorization must be enforced at the API or service layer. UI-level hiding of controls is not a security control.

### Object-Level Authorization (IDOR Prevention)

Always scope queries to the authenticated user. Fetching a resource by ID alone allows any authenticated user to access any record.

```javascript
// Incorrect: fetches any order by ID
app.get('/orders/:id', async (req, res) => {
  const order = await db.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
  res.json(order.rows[0]);
});

// Correct: scopes to the authenticated user
app.get('/orders/:id', authenticate, async (req, res) => {
  const order = await db.query(
    'SELECT * FROM orders WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );
  if (!order.rows[0]) return res.status(404).json({ error: 'Not found' });
  res.json(order.rows[0]);
});
```

### Role-Based Middleware and Indirect References

```javascript
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role))
      return res.status(403).json({ error: 'Forbidden' });
    next();
  };
}
app.delete('/admin/users/:id', authenticate, requireRole('admin'), deleteUser);
```

Use UUIDs as public-facing resource identifiers. Sequential integer IDs make enumeration trivial.

```sql
CREATE TABLE documents (
  id        SERIAL PRIMARY KEY,
  public_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  user_id   INTEGER NOT NULL REFERENCES users(id)
);
```

## Cryptographic Best Practices

| Operation | Use | Never Use |
|-----------|-----|-----------|
| Password hashing | Argon2id, bcrypt (cost 12+) | MD5, SHA-1, SHA-256 (too fast) |
| Symmetric encryption | AES-256-GCM | AES-ECB, DES, 3DES |
| Asymmetric encryption | RSA-OAEP (2048+), Ed25519 | RSA-PKCS1v1.5, DSA |
| Hashing (non-password) | SHA-256, SHA-3, BLAKE3 | MD5, SHA-1 |
| Random values | `crypto.randomBytes`, `secrets.token_urlsafe` | `Math.random`, `random.random` |
| TLS | 1.2 minimum, 1.3 preferred | SSL, TLS 1.0, TLS 1.1 |
| Key derivation | HKDF, PBKDF2 (600,000+ iterations) | Direct use of password as key |

```javascript
// Node.js: cryptographically secure random token
const token = require('crypto').randomBytes(32).toString('hex');

// AES-256-GCM encryption
function encrypt(plaintext, key) {
  const iv = require('crypto').randomBytes(12); // 96-bit IV for GCM
  const cipher = require('crypto').createCipheriv('aes-256-gcm', key, iv);
  const data = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  return { iv: iv.toString('hex'), tag: cipher.getAuthTag().toString('hex'), data: data.toString('hex') };
}
```

```python
import secrets
token = secrets.token_urlsafe(32)  # URL-safe base64, 32 bytes of entropy
```

## Secure Deserialization

Native serialization formats (Python `pickle`, Java `ObjectInputStream`, PHP `unserialize`, Ruby `Marshal`) execute arbitrary code during deserialization. Never deserialize untrusted data with these mechanisms.

| Language | Safe Format | Library |
|----------|-------------|---------|
| Python | JSON | `json` (stdlib) |
| Java | JSON | Jackson with `@JsonTypeInfo` disabled |
| PHP | JSON | `json_decode` |
| Any | Protocol Buffers | `protobuf` |

If native Java deserialization is unavoidable, use `ObjectInputFilter` to allowlist permitted classes:

```java
ois.setObjectInputFilter(info -> {
    Class<?> cls = info.serialClass();
    if (cls == null) return ObjectInputFilter.Status.UNDECIDED;
    return (cls == MyDataClass.class)
        ? ObjectInputFilter.Status.ALLOWED
        : ObjectInputFilter.Status.REJECTED;
});
```

Validate the structure and types of deserialized data before acting on it, even when using safe formats:

```python
from pydantic import BaseModel, validator

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

    @validator('amount')
    def must_be_positive(cls, v):
        if v <= 0: raise ValueError('Amount must be positive')
        return v
```

## Secure File Handling

- **Validate by content, not extension.** Check magic bytes (file signature) to determine actual file type.
- **Maintain an allowlist of permitted MIME types.** Reject anything not on the list.
- **Enforce size limits** before reading the full file into memory.
- **Generate a random filename** for storage. Never use the user-supplied filename as the storage path.
- **Store uploads outside the webroot.** Files inside the webroot may be directly accessible or executed.

```python
import magic, os, secrets

ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = '/var/app/uploads'   # outside webroot

def store_upload(file_bytes: bytes) -> str:
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File exceeds size limit")
    mime = magic.from_buffer(file_bytes, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"File type not permitted: {mime}")
    filename = secrets.token_hex(16) + '.' + mime.split('/')[-1]
    with open(os.path.join(UPLOAD_DIR, filename), 'wb') as f:
        f.write(file_bytes)
    return filename
```

Serve uploaded files with `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`. Serving with `Content-Type: text/html` enables stored XSS via MIME sniffing.

## Secure HTTP Headers

Apply these headers to every HTTP response. Configure at the reverse proxy or application framework level.

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

| Header | Purpose | Recommended Value |
|--------|---------|-------------------|
| `Content-Security-Policy` | Restricts resource loading; mitigates XSS | Strict allowlist per context |
| `Strict-Transport-Security` | Forces HTTPS; prevents SSL stripping | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | Prevents MIME sniffing | `nosniff` |
| `X-Frame-Options` | Prevents clickjacking | `DENY` or `SAMEORIGIN` |
| `Referrer-Policy` | Controls referrer header leakage | `strict-origin-when-cross-origin` |
| `Cache-Control` | Prevents caching of sensitive responses | `no-store` on authenticated endpoints |

```javascript
// Express.js: Helmet applies all headers with one call
app.use(require('helmet')({
  contentSecurityPolicy: { directives: { defaultSrc: ["'self'"], scriptSrc: ["'self'"], objectSrc: ["'none'"] } },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
}));
```

## Error Handling

- **Never expose internal details to the client.** Stack traces, file paths, SQL errors, and library versions reveal implementation details useful to attackers.
- **Log full error details server-side.** Operators need the full context; users do not.
- **Return structured, generic error responses** with stable error codes clients can handle programmatically.
- **Avoid resource existence disclosure.** Return `403 Forbidden` rather than `404 Not Found` when a user lacks permission — `404` confirms the resource exists.

```json
{ "error": "The requested resource was not found.", "code": "RESOURCE_NOT_FOUND", "request_id": "req_01HZ9K3M7P" }
```

```javascript
// Express.js: global error handler
app.use((err, req, res, next) => {
  logger.error({ requestId: req.id, message: err.message, stack: err.stack, userId: req.user?.id });
  const status = err.status || 500;
  res.status(status).json({
    error: status === 500 ? 'An unexpected error occurred.' : err.message,
    code: err.code || 'INTERNAL_ERROR',
    request_id: req.id,
  });
});
```

## Logging and Monitoring

### What to Log

| Event Category | Events to Log |
|----------------|--------------|
| Authentication | Login success, login failure, logout, password change, MFA events |
| Authorization | Access denied, privilege escalation attempts |
| Input validation | Validation failures at security boundaries |
| Data access | Access to sensitive records (PII, financial data) |
| Administrative | User creation/deletion, role changes, configuration changes |

### What Never to Log

- Passwords (plaintext or hashed), session tokens, API keys, JWTs
- Credit card numbers, CVVs, full national ID numbers
- Any secret or credential

```json
{
  "timestamp": "2026-03-18T14:22:01.342Z",
  "level": "warn",
  "event": "auth.login_failed",
  "username_hash": "sha256:a3f1...",
  "ip": "203.0.113.42",
  "request_id": "req_01HZ9K3M7P",
  "reason": "invalid_credentials"
}
```

Hash or truncate identifiers in log entries when the full value is not needed for investigation.

### Alerting Thresholds

| Pattern | Alert Condition |
|---------|----------------|
| Brute force | 10+ failed logins for one account in 5 minutes |
| Credential stuffing | 100+ failed logins across accounts from one IP in 5 minutes |
| Privilege escalation | Any `403` on an admin endpoint from a non-admin user |
| Unusual data access | Single user accessing >1000 records in 1 minute |
| Token reuse after logout | Session token used after server-side invalidation |

Alerts should route to an on-call channel and trigger automated temporary blocks where feasible. Log all automated enforcement actions.
