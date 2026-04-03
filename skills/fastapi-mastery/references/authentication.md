# Authentication

Sources: FastAPI official documentation (fastapi.tiangolo.com/tutorial/security), python-jose documentation, passlib documentation, OAuth2 specification (RFC 6749), production FastAPI security patterns

Covers: OAuth2PasswordBearer flow, JWT access and refresh token implementation, API key authentication, OAuth2 scopes for permissions, role-based access control dependencies, and security best practices.

## OAuth2 + JWT Pattern

The standard FastAPI authentication flow: OAuth2PasswordBearer extracts the token, a dependency decodes and validates it.

### Complete JWT Auth Setup

```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```

### Current User Dependency

```python
# app/core/security.py (continued)
from app.core.database import AsyncSessionDep
from app.users.models import User

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSessionDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]
```

### Login Endpoint

```python
# app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSessionDep,
):
    user = await get_user_by_email(session, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return {
        "access_token": create_access_token({"sub": user.id}),
        "refresh_token": create_refresh_token({"sub": user.id}),
        "token_type": "bearer",
    }

@router.post("/refresh")
async def refresh_token(
    refresh: str,
    session: AsyncSessionDep,
):
    try:
        payload = jwt.decode(
            refresh, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "access_token": create_access_token({"sub": user.id}),
        "token_type": "bearer",
    }
```

## API Key Authentication

For server-to-server or simple internal tools:

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(
    api_key: Annotated[str, Depends(api_key_header)],
    session: AsyncSessionDep,
) -> APIClient:
    client = await get_api_client_by_key(session, api_key)
    if not client or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return client

APIClientDep = Annotated[APIClient, Depends(verify_api_key)]
```

### API Key Best Practices

| Practice | Reason |
|----------|--------|
| Hash keys in database | Protect against database breach |
| Prefix keys with identifier (`sk_live_...`) | Distinguish key types |
| Support key rotation (multiple active keys) | Zero-downtime rotation |
| Log key usage (not the key itself) | Audit trail |
| Rate limit per key | Prevent abuse |

## OAuth2 Scopes

Scopes enable fine-grained permissions on JWT tokens:

```python
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi import Security

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "users:read": "Read user information",
        "users:write": "Create and modify users",
        "admin": "Full administrative access",
    },
)

async def get_current_user_with_scopes(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSessionDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not enough permissions",
        headers={
            "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
        },
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        token_scopes = payload.get("scopes", [])
    except JWTError:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise credentials_exception

    user = await session.get(User, payload.get("sub"))
    if not user:
        raise credentials_exception
    return user

# Use with specific scopes per endpoint
@router.get("/users/", dependencies=[Security(get_current_user_with_scopes, scopes=["users:read"])])
async def list_users():
    ...

@router.delete("/users/{id}", dependencies=[Security(get_current_user_with_scopes, scopes=["admin"])])
async def delete_user(id: int):
    ...
```

## Role-Based Access Dependencies

Create reusable role-checking dependencies:

```python
def require_role(*roles: str):
    async def role_checker(user: CurrentUserDep):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized",
            )
        return user
    return role_checker

AdminDep = Annotated[User, Depends(require_role("admin"))]
EditorDep = Annotated[User, Depends(require_role("admin", "editor"))]

@router.post("/articles/", dependencies=[Depends(require_role("admin", "editor"))])
async def create_article(data: ArticleCreate, user: CurrentUserDep):
    ...
```

## Token Storage Recommendations

| Client Type | Access Token | Refresh Token |
|-------------|-------------|---------------|
| SPA (browser) | HttpOnly cookie | HttpOnly cookie |
| Mobile app | OS secure storage (Keychain/Keystore) | OS secure storage |
| Server-to-server | Memory (short-lived) | Environment variable |

Never store tokens in localStorage or sessionStorage -- XSS vulnerabilities expose them.

## Security Checklist

| Check | Implementation |
|-------|---------------|
| Hash passwords with bcrypt | `passlib.context.CryptContext(schemes=["bcrypt"])` |
| Pin JWT algorithm in decode | `algorithms=[settings.jwt_algorithm]` -- never trust token header |
| Short access token lifespan | 15-30 minutes maximum |
| Validate token type | Check `type` claim to prevent refresh token used as access token |
| Check user is active | Query user on every request, verify `is_active` |
| HTTPS in production | Configure behind TLS termination proxy |
| Rate limit login endpoint | Prevent brute force attacks |
| Never log tokens or passwords | Log user ID, not credentials |
| Rotate secrets without downtime | Support multiple valid secrets during rotation |
| Return 401 for auth, 403 for authz | Distinguish "who are you?" from "you can't do that" |

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Storing JWT secret in code | Secret exposed in repository | Use environment variable |
| No token type validation | Refresh token used as access token | Include and check `type` claim |
| Long-lived access tokens (> 1 hour) | Extended exposure if leaked | 15-30 minute maximum |
| Not checking `is_active` on every request | Disabled users retain access | Query user in dependency |
| Returning user object with hashed_password | Password hash exposed | Use response model to exclude |
| Trusting `alg` from JWT header | Algorithm confusion attack | Pin algorithm in `jwt.decode()` |
| Same secret for all environments | Production token works in staging | Per-environment secrets |
