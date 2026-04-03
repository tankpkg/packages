# Project Structure

Sources: FastAPI official documentation (fastapi.tiangolo.com), zhanymkanov/fastapi-best-practices (17K stars), Pydantic v2 Settings documentation, production FastAPI codebase patterns

Covers: directory layouts for small to large projects, feature-based module organization, router wiring, configuration management with Pydantic BaseSettings, application factory pattern, and startup/shutdown lifecycle.

## Layout Patterns

### Small Project (< 10 routes)

```
project/
  app/
    __init__.py
    main.py
  requirements.txt
  Dockerfile
```

Single file works. Do not over-engineer early.

### Medium Project (10-50 routes)

Feature-based modules group related code together:

```
project/
  app/
    __init__.py
    main.py
    core/
      __init__.py
      config.py
      database.py
      security.py
    users/
      __init__.py
      router.py
      schemas.py
      service.py
      models.py
    items/
      __init__.py
      router.py
      schemas.py
      service.py
      models.py
  tests/
    __init__.py
    conftest.py
    test_users.py
    test_items.py
  alembic/
    versions/
    env.py
  alembic.ini
  pyproject.toml
  Dockerfile
```

### Large Project (50+ routes)

Add explicit layers and shared infrastructure:

```
project/
  app/
    __init__.py
    main.py
    core/
      config.py
      database.py
      security.py
      dependencies.py
      exceptions.py
      middleware.py
    features/
      users/
        router.py
        schemas.py
        service.py
        repository.py
        models.py
      orders/
        router.py
        schemas.py
        service.py
        repository.py
        models.py
    shared/
      pagination.py
      filtering.py
      email.py
  tests/
    conftest.py
    factories.py
    features/
      test_users.py
      test_orders.py
  alembic/
  pyproject.toml
```

## Feature Module Anatomy

Each feature module follows this internal structure:

| File | Responsibility |
|------|---------------|
| `router.py` | Route definitions, input validation, response formatting |
| `schemas.py` | Pydantic request/response models |
| `service.py` | Business logic, orchestration |
| `repository.py` | Database queries (optional, for large projects) |
| `models.py` | SQLAlchemy ORM models |
| `dependencies.py` | Feature-specific dependencies (optional) |

### Router File

Keep routes thin -- validate input, call service, return output:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, status
from .schemas import UserCreate, UserResponse
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: Annotated[UserService, Depends()],
):
    return await service.create(data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: Annotated[UserService, Depends()],
):
    return await service.get_by_id(user_id)
```

### Service File

Business logic lives here. Inject repositories and external services:

```python
from fastapi import Depends, HTTPException, status
from typing import Annotated
from app.core.database import AsyncSessionDep
from .models import User
from .schemas import UserCreate
from sqlalchemy import select

class UserService:
    def __init__(self, session: AsyncSessionDep):
        self.session = session

    async def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
```

## Router Wiring

Wire all feature routers in `main.py`:

```python
from fastapi import FastAPI
from app.users.router import router as users_router
from app.items.router import router as items_router
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
    )
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(items_router, prefix="/api/v1")
    return app

app = create_app()
```

### API Versioning Strategies

| Strategy | Implementation | Trade-off |
|----------|---------------|-----------|
| URL prefix | `/api/v1/users` via `prefix` param | Simple, explicit, duplicates routes |
| Header-based | Custom header `X-API-Version` | Clean URLs, harder to test in browser |
| No versioning | Single API, evolve carefully | Simplest, risk of breaking clients |

Prefer URL prefix versioning for public APIs. Use the router `prefix` parameter.

## Configuration Management

Use Pydantic `BaseSettings` for type-safe configuration from environment variables:

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "MyAPI"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = "redis://localhost:6379"

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    cors_origins: list[str] = ["http://localhost:3000"]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Settings Best Practices

| Practice | Reason |
|----------|--------|
| Use `@lru_cache` on the getter | Read `.env` once, reuse across requests |
| Define defaults for non-sensitive values | Simplify local development |
| Never default secrets | Force explicit configuration in production |
| Use `Field(alias=...)` for env vars | Map `DATABASE_URL` env var to `database_url` field |
| Split settings by concern for large apps | `DatabaseSettings`, `AuthSettings`, `CacheSettings` |
| Validate with Pydantic validators | Catch misconfig at startup, not at first request |

### Nested Settings for Large Projects

```python
class DatabaseSettings(BaseSettings):
    model_config = {"env_prefix": "DB_"}
    url: str
    pool_size: int = 5
    pool_overflow: int = 10

class AuthSettings(BaseSettings):
    model_config = {"env_prefix": "AUTH_"}
    secret: str
    algorithm: str = "HS256"
    expire_minutes: int = 30

class Settings(BaseSettings):
    db: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    debug: bool = False
```

## Application Factory Pattern

The factory pattern enables testing with different configurations:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, warm caches, connect to services
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: close connections, flush buffers
    await engine.dispose()

def create_app(settings=None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    # Register middleware
    from app.core.middleware import register_middleware
    register_middleware(app, settings)

    # Register routers
    from app.users.router import router as users_router
    app.include_router(users_router, prefix="/api/v1")

    return app
```

### Lifespan Events

Use the `lifespan` context manager (replaces deprecated `@app.on_event`):

| Phase | Use For |
|-------|---------|
| Before `yield` (startup) | Database connections, cache warming, ML model loading |
| After `yield` (shutdown) | Close connections, flush queues, cleanup temp files |

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await aioredis.from_url(settings.redis_url)
    yield
    # Shutdown
    await app.state.redis.close()
```

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Group by file type (`routers/`, `models/`) | Scattered feature logic | Group by feature |
| Import app directly in modules | Circular imports | Use `create_app()` factory |
| Global database session | Shared state across requests | Per-request session via `Depends()` |
| Settings as module-level dict | No validation, no type safety | `BaseSettings` with `@lru_cache` |
| Business logic in route handlers | Untestable, duplicated | Extract to service classes |
| Hardcoded configuration values | Cannot change per environment | Environment variables via `BaseSettings` |
| Skip `__init__.py` files | Import resolution breaks | Always include, even if empty |
| Monolithic `main.py` with all routes | Unmaintainable after 20 routes | Split into feature modules |
