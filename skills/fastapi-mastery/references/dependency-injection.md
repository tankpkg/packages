# Dependency Injection

Sources: FastAPI official documentation (fastapi.tiangolo.com/tutorial/dependencies), Starlette dependency system internals, zhanymkanov/fastapi-best-practices, production FastAPI patterns

Covers: Depends patterns, yield dependencies for setup/teardown, sub-dependency chains, class-based dependencies, Annotated type aliases, global dependencies, and dependency overrides for testing.

## Core Concepts

FastAPI's dependency injection system resolves a tree of callables before executing route handlers. Any callable (function, class, generator) can be a dependency.

### Basic Function Dependency

```python
from typing import Annotated
from fastapi import Depends, Query

async def pagination_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
):
    return {"skip": skip, "limit": limit}

PaginationDep = Annotated[dict, Depends(pagination_params)]

@router.get("/items/")
async def list_items(pagination: PaginationDep):
    return await service.list(skip=pagination["skip"], limit=pagination["limit"])
```

### Class-Based Dependency

Classes with `__init__` work as dependencies. FastAPI injects constructor parameters:

```python
from dataclasses import dataclass

@dataclass
class PaginationParams:
    skip: int = Query(0, ge=0)
    limit: int = Query(100, le=500)

PaginationDep = Annotated[PaginationParams, Depends()]

@router.get("/items/")
async def list_items(pagination: PaginationDep):
    return await service.list(skip=pagination.skip, limit=pagination.limit)
```

When using `Depends()` with no argument on a class type, FastAPI calls the class constructor. This gives typed attribute access instead of dictionary keys.

## Annotated Type Aliases

Define reusable dependency types to avoid repeating `Depends()`:

```python
from typing import Annotated
from fastapi import Depends
from app.core.database import get_session
from app.core.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User

# Define once in core/dependencies.py
AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

# Use everywhere
@router.get("/profile")
async def get_profile(
    user: CurrentUserDep,
    session: AsyncSessionDep,
):
    return user
```

### Alias Best Practices

| Practice | Reason |
|----------|--------|
| Define aliases in a central `dependencies.py` | Single source of truth |
| Name with `Dep` suffix | Clearly marks dependency types |
| Use `Annotated` (not bare `Depends()` default) | Preserves type info for editors and mypy |
| Keep aliases close to their dependency function | Easier discovery |

## Yield Dependencies

Use `yield` for setup/teardown patterns. Code before `yield` runs before the route; code after runs after the response is sent:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def get_session(
    session_factory: Annotated[async_sessionmaker, Depends(get_session_factory)],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Yield Dependency Rules

| Rule | Detail |
|------|--------|
| Only one `yield` per dependency | FastAPI enforces this |
| Code after `yield` always runs | Even if the route raises an exception |
| Exceptions in cleanup are suppressed | Log them explicitly |
| Cannot modify the response after yield | Response is already sent |
| Yield dependencies can use sub-dependencies | Full dependency tree still resolves |

### Common Yield Patterns

**Database session** (most common):

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

**Temporary file cleanup**:

```python
import tempfile, os

def get_temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)
```

**Distributed lock**:

```python
async def get_lock(redis: RedisDep, resource_id: str):
    lock = redis.lock(f"lock:{resource_id}", timeout=30)
    await lock.acquire()
    yield lock
    await lock.release()
```

## Sub-Dependencies

Dependencies can depend on other dependencies, forming a tree:

```python
async def get_settings() -> Settings:
    return Settings()

async def get_database_engine(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncEngine:
    return create_async_engine(settings.database_url)

async def get_session(
    engine: Annotated[AsyncEngine, Depends(get_database_engine)],
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session

async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    payload = decode_token(token)
    user = await session.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401)
    return user
```

FastAPI resolves: `get_settings -> get_database_engine -> get_session -> get_current_user`. Each dependency in the tree is called once per request, even if multiple routes depend on it.

### Dependency Caching

FastAPI caches dependency results within a single request. If two dependencies both depend on `get_session`, the same session instance is shared:

```python
# Both get the SAME session instance per request
@router.post("/transfer")
async def transfer(
    user_service: Annotated[UserService, Depends()],   # gets session
    account_service: Annotated[AccountService, Depends()],  # gets same session
):
    ...
```

To disable caching (get a fresh instance each time):

```python
Depends(get_session, use_cache=False)
```

## Global Dependencies

Apply dependencies to entire routers or the whole app:

```python
# Router-level: all routes require authentication
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

# App-level: all routes get rate limiting
app = FastAPI(dependencies=[Depends(rate_limiter)])
```

Global dependencies run but their return values are not injected into route parameters. Use them for side effects: authentication checks, rate limiting, logging, request validation.

## Dependency Overrides for Testing

Override any dependency at test time without modifying production code:

```python
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_session

# Mock dependency
async def override_get_session():
    async with test_session_maker() as session:
        yield session

# Apply override
app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)

def test_create_user():
    response = client.post("/api/v1/users/", json={"name": "Test"})
    assert response.status_code == 201

# Clean up
app.dependency_overrides.clear()
```

### Override Patterns

| Scenario | Override Strategy |
|----------|------------------|
| Test database | Override `get_session` with test DB session |
| Mock external API | Override HTTP client dependency with mock |
| Skip auth in tests | Override `get_current_user` to return a fake user |
| Custom settings | Override `get_settings` with test settings |

### Fixture-Based Overrides

```python
import pytest
from app.main import app

@pytest.fixture
def client():
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = lambda: fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## Advanced Patterns

### Parameterized Dependencies

Create dependency factories for configurable behavior:

```python
def require_role(allowed_roles: list[str]):
    async def role_checker(user: CurrentUserDep):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.delete("/{item_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_item(item_id: int):
    ...

@router.get("/", dependencies=[Depends(require_role(["admin", "editor"]))])
async def list_items():
    ...
```

### Service Injection via Class Dependencies

Inject services that themselves depend on infrastructure:

```python
class UserService:
    def __init__(
        self,
        session: AsyncSessionDep,
        settings: Annotated[Settings, Depends(get_settings)],
    ):
        self.session = session
        self.settings = settings

    async def create(self, data: UserCreate) -> User:
        ...

# FastAPI resolves session and settings automatically
@router.post("/users/")
async def create_user(
    data: UserCreate,
    service: Annotated[UserService, Depends()],
):
    return await service.create(data)
```

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Calling the dependency (`Depends(func())`) | Executes immediately, bypasses DI | Pass the callable: `Depends(func)` |
| Circular dependencies | Import error at startup | Restructure, use lazy imports |
| Heavy computation in dependencies | Blocks every request | Cache results or move to startup |
| Forgetting `use_cache=False` | Shared mutable state between deps | Explicitly disable when needed |
| Not cleaning up `dependency_overrides` | Test pollution | Use fixture with cleanup |
| Sync generator for async teardown | Teardown may not await properly | Use `async def` with `yield` |
