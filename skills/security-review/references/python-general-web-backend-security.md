# Python Web Backend Security

Sources: OWASP Python Security, Django Security Documentation, Flask Security Documentation

## Scope
This guide covers Python web backends with Django, Flask, and FastAPI in mind.
It focuses on input validation, injection prevention, auth, and safe defaults.
Apply these practices to new code and to security reviews.
Avoid recommending HSTS unless explicitly required by policy.
Avoid over-asserting TLS requirements for local development contexts.

## Threat model essentials
Assume every request can be malicious.
Assume authentication tokens can be stolen if stored or logged incorrectly.
Assume dependency supply chain risk.
Prioritize preventing injection and access control flaws.
Treat serialization as a high-risk boundary.

## Input validation
Validate request bodies and parameters at the boundary.
Reject unknown fields to reduce attack surface.
Normalize data types and enforce limits.
Never trust user input for queries or file paths.
Prefer schema validation with clear error handling.

## Pydantic v2 example (FastAPI style)

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUser(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="user", pattern="^(user|admin)$")
```

## Marshmallow example

```python
from marshmallow import Schema, fields, validate

class CreateUserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(load_default="user", validate=validate.OneOf(["user", "admin"]))
```

## SQL injection prevention
Use parameterized queries and ORM methods.
Avoid string concatenation for SQL.
Use SQLAlchemy bound parameters for raw SQL.
Avoid dynamic table names from user input.
Log suspicious query patterns for review.

## SQLAlchemy example

```python
from sqlalchemy import text

stmt = text("SELECT * FROM users WHERE email = :email")
rows = db.session.execute(stmt, {"email": email}).fetchall()
```

## Authentication basics
Hash passwords with bcrypt or argon2.
Store only password hashes, never plaintext.
Use per-user salts and an appropriate cost factor.
Throttle or lock out repeated failed logins.
Rotate session identifiers after login.

## bcrypt example

```python
import bcrypt

password = user_password.encode("utf-8")
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

if bcrypt.checkpw(password, hashed):
    login_user(user)
```

## Session management
Use HttpOnly cookies for session IDs.
Set SameSite=Lax or Strict for session cookies.
Set Secure only when TLS is actually used.
Expire sessions after inactivity.
Invalidate sessions on password reset.

## CORS configuration (Flask)

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://app.example.com"]}}, supports_credentials=True)
```

## CORS configuration (FastAPI)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## CSRF protection (Flask)

```python
from flask import Flask
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me"
csrf = CSRFProtect(app)
```

## CSRF protection (Django)
Use Django's built-in CSRF middleware.
Ensure templates include `{% csrf_token %}` in forms.
Prefer CSRF protection on all unsafe methods.
Add trusted origins via `CSRF_TRUSTED_ORIGINS`.
Do not disable CSRF protection globally.

## File upload security
Limit file size and count.
Validate MIME type and file signatures.
Store uploads outside web root.
Scan uploaded files when applicable.
Use random file names to avoid collisions.

## Dependency security
Use pip-audit or safety in CI.
Pin versions in requirements.txt or lock files.
Review transitive dependencies for critical paths.
Enable Dependabot where possible.
Avoid installing packages with unknown provenance.

## Secrets management
Use environment variables or a secrets manager.
Never commit .env files.
Rotate secrets after exposure.
Restrict access to secrets per service.
Avoid logging secrets in debug output.

## Logging hygiene
Never log passwords or tokens.
Redact sensitive fields from structured logs.
Use request IDs for correlation.
Avoid logging full request bodies in production.
Ensure logs are access controlled.

## Structured logging example

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("app")
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Error handling
Do not expose stack traces to clients.
Return generic error messages to users.
Log detailed errors server-side only.
Avoid leaking SQL or filesystem paths.
Use centralized exception handling.

## Serialization risks
Do not use pickle with untrusted data.
Avoid yaml.load without safe loaders.
Prefer JSON for untrusted input.
Validate data after deserialization.
Treat serialized input as untrusted.

## Django security settings
Set `ALLOWED_HOSTS` explicitly.
Use `SECURE_SSL_REDIRECT` only when TLS is used.
Set `SESSION_COOKIE_HTTPONLY` and `SESSION_COOKIE_SAMESITE`.
Set `CSRF_TRUSTED_ORIGINS` for known domains.
Set `SECURE_CONTENT_TYPE_NOSNIFF` and `SECURE_REFERRER_POLICY`.

## Flask security settings
Set `SESSION_COOKIE_HTTPONLY = True`.
Set `SESSION_COOKIE_SAMESITE = "Lax"` or "Strict".
Set `SESSION_COOKIE_SECURE = True` only with TLS.
Disable debug mode in production.
Use `ProxyFix` when behind a proxy.

## FastAPI auth with OAuth2 scopes

```python
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", scopes={"admin": "Admin access"})

def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if security_scopes.scopes and not has_scopes(payload, security_scopes.scopes):
        raise PermissionError("Forbidden")
    return payload

@app.get("/admin", dependencies=[Security(get_current_user, scopes=["admin"])])
def admin_route():
    return {"status": "ok"}
```

## Access control pitfalls
Do not trust client-provided roles.
Validate resource ownership on every request.
Avoid implicit admin checks based on email or username.
Centralize permission checks in one layer.
Log access denials for review.

## SSRF and outbound requests
Allowlist outbound hosts when proxying URLs.
Block internal IP ranges and metadata services.
Enforce timeouts and size limits.
Do not follow redirects to unknown hosts.
Log unusual outbound requests.

## Security headers
Set security headers at the server or proxy.
Use Content-Security-Policy for frontend pages.
Avoid enabling HSTS unless explicitly required by policy.
Set Referrer-Policy and X-Content-Type-Options.
Disable server signature headers.

## Checklist
Use this checklist for quick review.
Prioritize preventing injection and auth bypass.

| Security Check | Implementation | Priority |
| --- | --- | --- |
| Input validation | Schema validation for body, params, query | High |
| Injection prevention | Parameterized queries and ORM methods | High |
| Auth correctness | bcrypt or argon2 password hashing | High |
| Authorization | Centralized permission checks | High |
| CSRF protection | Flask-WTF or Django CSRF middleware | High |
| CORS allowlist | Explicit origin allowlist, no wildcards with creds | High |
| Secrets management | Secrets in env or vault, never in repo | High |
| Error handling | No stack traces returned to clients | Medium |
| Logging hygiene | Redact tokens and secrets | Medium |
| Dependency audit | pip-audit or safety in CI | Medium |
| File upload safety | Validate type, size, and storage location | Medium |
| Serialization safety | Avoid pickle and unsafe yaml | Medium |
| Django hardening | ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS set | Medium |
| Session rotation | Rotate session IDs on login | Low |
