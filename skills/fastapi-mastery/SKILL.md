---
name: "@tank/fastapi-mastery"
description: |
  Production-grade FastAPI development. Covers project structure (routers,
  services, repositories), dependency injection (Depends, sub-dependencies,
  yield dependencies, overrides), Pydantic v2 integration (models, settings,
  validation), async SQLAlchemy 2.0 (sessions, Alembic migrations), authentication
  (OAuth2, JWT, API keys, scopes), middleware and error handling, background tasks
  and Celery, WebSockets, testing (TestClient, async tests, dependency overrides),
  deployment (uvicorn, Docker, Kubernetes), and performance optimization (connection
  pooling, caching, streaming).

  Synthesizes FastAPI official documentation (fastapi.tiangolo.com), Pydantic v2
  docs, SQLAlchemy 2.0 docs, Starlette internals, and production codebase patterns.

  Trigger phrases: "fastapi", "fastapi best practices", "fastapi production",
  "fastapi dependency injection", "fastapi Depends", "fastapi pydantic",
  "fastapi sqlalchemy", "fastapi authentication", "fastapi jwt",
  "fastapi testing", "fastapi docker", "fastapi project structure",
  "fastapi websocket", "fastapi background tasks", "fastapi middleware",
  "fastapi celery", "fastapi async", "fastapi deployment", "uvicorn",
  "fastapi alembic", "fastapi redis", "fastapi error handling"
---

# FastAPI Mastery

## Core Philosophy

1. **Type hints are the contract** -- FastAPI derives validation, serialization, and OpenAPI docs from type annotations. Invest in precise types and Pydantic models; everything downstream improves.
2. **Dependencies replace globals** -- Use `Depends()` for database sessions, settings, auth, and shared logic. Dependencies are composable, testable, and self-documenting.
3. **Async by default, sync when blocking** -- Use `async def` for I/O-bound routes (database, HTTP calls). Use `def` for CPU-bound work so FastAPI runs it in a thread pool automatically.
4. **Thin routes, fat services** -- Route functions validate input and return output. Business logic belongs in service classes injected via dependencies.
5. **Test through the API** -- Use `TestClient` with dependency overrides. Test behavior, not implementation. Override only what varies between environments.

## Quick-Start: Common Problems

### "How should I structure my FastAPI project?"

| Project Size | Structure |
|-------------|-----------|
| Small (< 10 routes) | Single `main.py` with inline routes |
| Medium (10-50 routes) | Feature-based: `app/{feature}/router.py, service.py, models.py` |
| Large (50+ routes) | Layered: routers -> services -> repositories + shared `core/` |

1. Group by feature, not by file type (no `routers/`, `models/`, `services/` top-level dirs)
2. Each feature module gets its own router, schemas, and service
3. Wire routers in `main.py` with `app.include_router()`
-> See `references/project-structure.md`

### "My dependency injection is getting complicated"

1. Use `Annotated` type aliases to avoid repeating `Depends()` signatures
2. Use `yield` dependencies for setup/teardown (database sessions, file handles)
3. Chain sub-dependencies -- FastAPI resolves the full dependency tree automatically
4. Override dependencies in tests with `app.dependency_overrides[original] = mock`
-> See `references/dependency-injection.md`

### "How do I set up the database properly?"

1. Use SQLAlchemy 2.0 async with `create_async_engine` and `async_sessionmaker`
2. Inject sessions via a `yield` dependency -- session per request, auto-cleanup
3. Set `expire_on_commit=False` for async sessions to avoid lazy-load errors
4. Use Alembic with async driver for migrations
-> See `references/database-integration.md`

### "What auth pattern should I use?"

| Scenario | Pattern |
|----------|---------|
| SPA / mobile calling your API | OAuth2 + JWT (access + refresh tokens) |
| Server-to-server | API key or Client Credentials |
| Simple internal tool | API key in header |
| Third-party integration | OAuth2 scopes |

-> See `references/authentication.md`

### "My tests are slow or flaky"

1. Use `TestClient` for sync tests -- no `async` overhead
2. Override database dependency to use a test database
3. Use `httpx.AsyncClient` only when testing async-specific behavior
4. Create fixtures for authenticated clients and test data
-> See `references/testing.md`

## Decision Trees

### Async vs Sync Route

| Operation | Use |
|-----------|-----|
| Database queries (SQLAlchemy async) | `async def` |
| HTTP calls (httpx, aiohttp) | `async def` |
| File I/O (large files) | `async def` with `aiofiles` |
| CPU-bound (image processing, ML) | `def` (runs in thread pool) |
| Blocking library (no async support) | `def` |

### Background Processing

| Task Duration | Tool |
|--------------|------|
| < 5 seconds, fire-and-forget | `BackgroundTasks` |
| 5-30 seconds, needs monitoring | `BackgroundTasks` with status tracking |
| > 30 seconds, retry logic, scheduling | Celery + Redis/RabbitMQ |
| Real-time progress updates | WebSocket + task queue |

### Database Library

| Need | Choice |
|------|--------|
| Full ORM control, complex queries | SQLAlchemy 2.0 async |
| Rapid prototyping, simpler models | SQLModel (SQLAlchemy + Pydantic) |
| Raw SQL, maximum performance | `encode/databases` or `asyncpg` directly |

## Reference Index

| File | Contents |
|------|----------|
| `references/project-structure.md` | Directory layouts, feature-based modules, router wiring, configuration management with Pydantic Settings, application factory pattern |
| `references/dependency-injection.md` | Depends patterns, yield dependencies, sub-dependencies, class-based deps, Annotated aliases, global dependencies, dependency overrides |
| `references/pydantic-models.md` | Pydantic v2 models, field validation, custom validators, serialization, discriminated unions, model_config, request/response schema design |
| `references/database-integration.md` | SQLAlchemy 2.0 async setup, session management, repository pattern, Alembic migrations, connection pooling, transaction handling |
| `references/authentication.md` | OAuth2PasswordBearer, JWT access/refresh tokens, API key auth, scopes, role-based access, security dependencies |
| `references/middleware-errors.md` | CORS, custom middleware, exception handlers, request validation errors, logging middleware, request ID tracking |
| `references/testing.md` | TestClient, async tests, dependency overrides, database test fixtures, authentication testing, factory patterns |
| `references/deployment.md` | Uvicorn workers, Docker multi-stage builds, Kubernetes probes, gunicorn, serverless (Mangum), environment configuration |
| `references/async-performance.md` | Async patterns, BackgroundTasks, Celery integration, WebSockets, streaming responses, caching, connection pooling, profiling |
