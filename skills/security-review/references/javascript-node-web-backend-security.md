# Node.js Web Backend Security

Sources: OWASP Node.js Security Cheat Sheet, Node.js Security Best Practices

## Scope
This guide targets Node.js web backends, commonly Express and similar frameworks.
It focuses on server-side security controls and secure defaults.
Apply these practices to new code and when reviewing existing code paths.
Avoid recommending HSTS unless explicitly required by policy.
Avoid over-asserting TLS requirements for local development contexts.

## Threat model essentials
Assume request data is attacker-controlled.
Assume authentication tokens can be stolen if stored or logged incorrectly.
Assume dependency supply chain can be compromised.
Focus on injection prevention and authorization correctness.
Prefer explicit allowlists over implicit defaults.

## Input validation
Validate request bodies, params, and query strings.
Use schema validation at the boundary.
Reject unknown fields to reduce attack surface.
Normalize types and enforce limits.
Never trust req.body or req.query without validation.

## Zod validation example

```javascript
import { z } from "zod";

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(["user", "admin"]).default("user"),
});

app.post("/users", (req, res, next) => {
  const parsed = createUserSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid input" });
  }
  req.body = parsed.data;
  next();
}, createUserHandler);
```

## SQL and NoSQL injection prevention
Always use parameterized queries or a query builder.
Avoid string concatenation for SQL.
For NoSQL, avoid passing untrusted objects directly into queries.
Use strict allowlists for query operators.
Log suspicious query patterns for investigation.

## ORM usage guidance
Prefer ORM methods that parameterize by default.
Do not use raw SQL unless absolutely required.
If using raw SQL, bind parameters explicitly.
Review any `$where` or regex usage for MongoDB.
Avoid dynamic collection names and dynamic table names.

## Authentication basics
Use a proven auth library when possible.
Hash passwords with bcrypt or argon2.
Use per-user salts and a strong cost factor.
Store only password hashes, never plaintext.
Lock out or throttle repeated failed logins.

## JWT best practices
Use short-lived access tokens and rotate refresh tokens.
Pin the algorithm and validate expected issuer and audience.
Avoid `none` algorithm and reject unexpected alg values.
Store JWTs in HttpOnly cookies when possible.
Handle token revocation via a denylist or rotation.

## JWT validation example

```javascript
import jwt from "jsonwebtoken";

const JWT_ISSUER = "https://auth.example.com";
const JWT_AUDIENCE = "api";

function authenticate(req, res, next) {
  const token = req.cookies.session || req.headers.authorization?.replace("Bearer ", "");
  if (!token) return res.status(401).json({ error: "Unauthorized" });

  try {
    const payload = jwt.verify(token, process.env.JWT_PUBLIC_KEY, {
      algorithms: ["RS256"],
      issuer: JWT_ISSUER,
      audience: JWT_AUDIENCE,
    });
    req.user = payload;
    return next();
  } catch (err) {
    return res.status(401).json({ error: "Unauthorized" });
  }
}
```

## Authorization (RBAC) with middleware
Centralize access control in middleware.
Use explicit role checks per route.
Avoid embedding authorization checks in controllers only.
Enforce least privilege.
Example RBAC middleware:

```javascript
const requireRole = (roles) => (req, res, next) => {
  if (!req.user || !roles.includes(req.user.role)) {
    return res.status(403).json({ error: "Forbidden" });
  }
  return next();
};

app.delete("/admin/users/:id", authenticate, requireRole(["admin"]), deleteUser);
```

## Rate limiting
Use rate limiting for login and sensitive endpoints.
Prefer sliding window or token bucket.
Apply per-IP and per-user where possible.
Back it with Redis for distributed deployments.
Example with express-rate-limit:

```javascript
import rateLimit from "express-rate-limit";

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
});

app.post("/login", loginLimiter, loginHandler);
```

## Security headers
Use helmet to set secure headers.
Disable headers that leak server details.
Avoid enabling HSTS unless explicitly required by policy.
Set Content-Security-Policy from the server.
Example helmet configuration:

```javascript
import helmet from "helmet";

app.use(helmet({
  contentSecurityPolicy: {
    useDefaults: true,
    directives: {
      "script-src": ["'self'"],
      "object-src": ["'none'"],
      "base-uri": ["'self'"],
      "frame-ancestors": ["'none'"],
    },
  },
  referrerPolicy: { policy: "no-referrer" },
  crossOriginResourcePolicy: { policy: "same-site" },
}));
```

## CORS configuration
Define explicit allowlists for origins.
Do not use wildcard origins with credentials.
Return minimal headers for preflight responses.
Avoid reflecting arbitrary Origin headers.
Log unexpected origins for review.

## File upload security
Limit file size and count.
Validate MIME type and file signatures.
Store uploads outside the web root.
Scan files for malware if applicable.
Use random file names to avoid path traversal.

## Example file upload validation

```javascript
import multer from "multer";

const upload = multer({
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ["image/png", "image/jpeg"];
    if (!allowed.includes(file.mimetype)) return cb(new Error("Invalid file type"));
    return cb(null, true);
  },
});

app.post("/avatars", authenticate, upload.single("avatar"), avatarHandler);
```

## Secrets management
Use environment variables or a secrets manager.
Never commit .env files.
Rotate secrets on a schedule and after exposure.
Avoid logging secrets and tokens.
Limit secret access by service role.

## Dependency security
Use npm audit in CI to detect known issues.
Pin versions with package-lock.json.
Review transitive dependencies for critical paths.
Use Snyk or similar tooling for monitoring.
Avoid installing packages with unknown provenance.

## Logging security
Never log passwords, tokens, or full auth headers.
Redact sensitive fields in structured logs.
Use request IDs for tracing without data exposure.
Avoid logging full request bodies in production.
Ensure logs are access controlled.

## Error handling
Do not expose stack traces to clients.
Use a centralized error handler.
Return generic error messages to users.
Log detailed errors server-side.
Avoid leaking internal paths or SQL details.

## Session management
Use HttpOnly cookies for session IDs.
Rotate session IDs after login and privilege changes.
Expire sessions after inactivity.
Bind sessions to device or IP only if it does not harm users.
Invalidate sessions on password reset.

## CSRF protection
Use SameSite cookies for session cookies.
Use CSRF tokens for unsafe methods.
Verify Origin and Referer for sensitive actions.
Avoid custom CSRF logic when libraries exist.
Document any endpoints intentionally exempted.

## SSRF and outbound requests
Validate and allowlist outbound hosts.
Resolve DNS and revalidate on each request.
Block internal IP ranges and metadata services.
Avoid proxying arbitrary URLs.
Add timeouts and size limits for outbound requests.

## Access control pitfalls
Do not use client-provided roles or permissions.
Validate resource ownership on every request.
Avoid implicit admin checks based on email or username.
Audit route-level permissions regularly.
Log access denials to identify abuse.

## Secure defaults in Express
Disable X-Powered-By.
Set trust proxy correctly when behind a load balancer.
Limit JSON body size to prevent resource exhaustion.
Use strict routing to avoid ambiguity.
Handle async errors with a wrapper.

## Example secure Express baseline

```javascript
app.disable("x-powered-by");
app.set("trust proxy", 1);
app.use(express.json({ limit: "200kb" }));
```

## Checklist
Use this checklist for quick review.
Prioritize controls that prevent injection and auth bypass.

| Security Check | Implementation | Priority |
| --- | --- | --- |
| Input validation | Schema validation for body, params, query | High |
| Injection prevention | Parameterized queries and ORM methods | High |
| Auth correctness | JWT or session validation with strict checks | High |
| Authorization | Central RBAC middleware on protected routes | High |
| Rate limiting | Per-IP and per-user limits on auth routes | High |
| Secure headers | Helmet configured with CSP and safe defaults | High |
| Secrets management | Secrets in env or vault, never in repo | High |
| Error handling | No stack traces returned to clients | Medium |
| Logging hygiene | Redact tokens and secrets from logs | Medium |
| File upload safety | Validate type, size, and storage location | Medium |
| Dependency audit | npm audit and lockfile integrity | Medium |
| CORS allowlist | Explicit origin allowlist | Medium |
| Session rotation | Rotate session IDs on privilege change | Low |
| SSRF defense | Allowlist outbound hosts | Low |
