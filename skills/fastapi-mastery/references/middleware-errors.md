# Middleware and Error Handling

Sources: FastAPI official documentation (fastapi.tiangolo.com/tutorial/middleware), Starlette middleware documentation (starlette.io), production FastAPI error handling patterns, OWASP security headers guidance

Covers: CORS configuration, custom middleware patterns, exception handlers, structured error responses, request validation error customization, logging middleware, request ID tracking, and security headers.

## CORS Middleware

Configure Cross-Origin Resource Sharing for frontend-backend communication:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

### CORS Configuration by Environment

| Environment | `allow_origins` | `allow_credentials` |
|------------|-----------------|---------------------|
| Development | `["http://localhost:3000"]` | `True` |
| Staging | `["https://staging.example.com"]` | `True` |
| Production | `["https://example.com"]` | `True` |
| Public API (no cookies) | `["*"]` | `False` |

Never use `allow_origins=["*"]` with `allow_credentials=True` -- browsers reject this combination.

## Custom Middleware

### ASGI Middleware (Recommended)

Write middleware using the ASGI interface for full control:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

app.add_middleware(TimingMiddleware)
```

### Request ID Middleware

Track requests across services for debugging:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### Logging Middleware

```python
import logging
import time

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        return response
```

### Security Headers Middleware

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
```

### Middleware Registration Order

Middleware executes in reverse registration order (last registered runs first on request, last on response):

```python
# Execution order for incoming request: 3 -> 2 -> 1 -> route handler
# Execution order for outgoing response: route handler -> 1 -> 2 -> 3
app.add_middleware(SecurityHeadersMiddleware)  # 1
app.add_middleware(LoggingMiddleware)           # 2
app.add_middleware(RequestIDMiddleware)         # 3 (runs first on request)
```

Register in this order: CORS first (outermost), then security headers, then request ID, then logging, then app-specific.

## Exception Handlers

### Built-in HTTPException

```python
from fastapi import HTTPException, status

@router.get("/items/{item_id}")
async def get_item(item_id: int, session: AsyncSessionDep):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
            headers={"X-Error": "item_missing"},
        )
    return item
```

### Structured Error Responses

Define a consistent error format across the API:

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None = None

class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    detail: list[dict]
    request_id: str | None = None
```

### Custom Exception Classes

```python
# app/core/exceptions.py
class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        error: str,
        detail: str,
    ):
        self.status_code = status_code
        self.error = error
        self.detail = detail

class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            status_code=404,
            error="not_found",
            detail=f"{resource} with id '{resource_id}' not found",
        )

class ConflictError(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, error="conflict", detail=detail)

class ForbiddenError(AppException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, error="forbidden", detail=detail)
```

### Register Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error,
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", extra={
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        })
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "detail": "An internal error occurred",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
```

### Using Custom Exceptions in Services

```python
# app/users/service.py
from app.core.exceptions import NotFoundError, ConflictError

class UserService:
    async def get_by_id(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def create(self, data: UserCreate) -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"Email '{data.email}' already registered")
        ...
```

## Validation Error Customization

### Simplify Pydantic Error Messages

```python
@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": errors},
    )
```

## Trusted Host Middleware

Prevent host header attacks in production:

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"],
)
```

## GZip Middleware

Compress responses larger than a threshold:

```python
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| CORS `allow_origins=["*"]` with credentials | Browser rejects response | List specific origins when using cookies |
| Generic 500 errors in production | No debugging context | Include request_id, log full traceback |
| Raising `Exception` in routes | Unstructured error responses | Use custom exception classes |
| Not handling `RequestValidationError` | Default Pydantic errors confuse API consumers | Custom handler with simpler format |
| Middleware modifying response body | Streaming breaks, memory issues | Only modify headers in middleware |
| Missing error handler for unhandled exceptions | Stack traces leak to clients | Catch-all handler returns generic message |
| Exposing internal error details | Security risk | Return generic message, log details server-side |
