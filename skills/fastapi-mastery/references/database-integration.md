# Database Integration

Sources: SQLAlchemy 2.0 official documentation (docs.sqlalchemy.org), FastAPI official documentation (fastapi.tiangolo.com), Alembic documentation, SQLModel documentation, production async database patterns

Covers: SQLAlchemy 2.0 async engine and session setup, per-request session injection, repository pattern, Alembic async migrations, connection pooling configuration, transaction management, and SQLModel as an alternative.

## SQLAlchemy 2.0 Async Setup

### Engine and Session Factory

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass
```

### Critical Configuration

| Setting | Value | Reason |
|---------|-------|--------|
| `expire_on_commit=False` | Required for async | Prevents lazy-load attempts after commit that fail in async context |
| `pool_pre_ping=True` | Recommended | Tests connection health before use; recovers from database restarts |
| `pool_recycle=1800` | Recommended | Recycles connections every 30 min; prevents stale connections |
| `echo=settings.debug` | Development only | Logs SQL statements; disable in production for performance |

### Database URL Format

| Database | Async Driver | URL Format |
|----------|-------------|------------|
| PostgreSQL | asyncpg | `postgresql+asyncpg://user:pass@host:5432/db` |
| PostgreSQL | psycopg (v3) | `postgresql+psycopg://user:pass@host:5432/db` |
| MySQL | aiomysql | `mysql+aiomysql://user:pass@host:3306/db` |
| SQLite | aiosqlite | `sqlite+aiosqlite:///./test.db` |

## Session Dependency

Inject a per-request database session using a yield dependency:

```python
# app/core/database.py
from typing import Annotated, AsyncGenerator
from fastapi import Depends

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]
```

Use in routes:

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSessionDep):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Session Lifecycle per Request

```
Request arrives
  -> get_session() creates AsyncSession
    -> Route handler uses session
      -> Session auto-commits on success (if configured)
      -> Session auto-rollbacks on exception
  -> get_session() cleanup: session closes
Response sent
```

## ORM Model Definition

```python
# app/users/models.py
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### SQLAlchemy 2.0 Type Mapping

| Python Type | SQLAlchemy Column |
|-------------|-------------------|
| `int` | `Integer` (auto-detected) |
| `str` | `String` (specify length) |
| `bool` | `Boolean` |
| `float` | `Float` |
| `datetime` | `DateTime` |
| `date` | `Date` |
| `Decimal` | `Numeric(precision, scale)` |
| `dict` | `JSON` |
| `list` | Requires relationship or `ARRAY` (PostgreSQL) |

## Repository Pattern

Separate database queries from business logic:

```python
# app/users/repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(User).offset(skip).limit(limit).order_by(User.id)
        )
        users = list(result.scalars().all())
        return users, total

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
```

### Wire Repository as Dependency

```python
# app/users/dependencies.py
from typing import Annotated
from fastapi import Depends
from app.core.database import AsyncSessionDep
from .repository import UserRepository

async def get_user_repository(session: AsyncSessionDep) -> UserRepository:
    return UserRepository(session)

UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
```

## Transaction Management

### Explicit Transaction Control

```python
async def transfer_funds(
    session: AsyncSessionDep,
    from_id: int,
    to_id: int,
    amount: Decimal,
):
    async with session.begin():
        from_account = await session.get(Account, from_id, with_for_update=True)
        to_account = await session.get(Account, to_id, with_for_update=True)

        if from_account.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        from_account.balance -= amount
        to_account.balance += amount
    # commit happens automatically when `begin()` context exits without error
```

### Session with Auto-Commit Dependency

```python
async def get_session_with_commit() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Alembic Async Migrations

### Setup

```bash
pip install alembic
alembic init -t async alembic
```

### Configure `alembic/env.py`

```python
from app.core.database import Base, engine
from app.users.models import User  # Import all models

target_metadata = Base.metadata

async def run_async_migrations() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
```

### Migration Commands

| Command | Purpose |
|---------|---------|
| `alembic revision --autogenerate -m "description"` | Generate migration from model changes |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Revert one migration |
| `alembic history` | Show migration history |
| `alembic current` | Show current revision |

### Migration Best Practices

| Practice | Reason |
|----------|--------|
| Always review autogenerated migrations | Alembic cannot detect all changes (column renames, data migrations) |
| Name migrations descriptively | `add_users_email_index` not `auto_001` |
| Test migrations on a copy of production data | Catch data-dependent failures |
| Include downgrade logic | Enable rollback in emergencies |
| Run migrations in CI before deployment | Fail fast on migration errors |

## Connection Pooling

### Pool Configuration

```python
engine = create_async_engine(
    database_url,
    pool_size=5,          # Persistent connections in pool
    max_overflow=10,      # Extra connections when pool is full
    pool_timeout=30,      # Seconds to wait for connection from pool
    pool_recycle=1800,    # Recycle connections every 30 minutes
    pool_pre_ping=True,   # Test connection before checkout
)
```

### Pool Sizing Formula

```
pool_size = (num_workers * expected_concurrent_queries) + headroom
```

For a typical deployment: 4 workers, 2 concurrent queries each = `pool_size=10, max_overflow=5`.

| Deployment | pool_size | max_overflow |
|-----------|-----------|-------------|
| Development | 5 | 0 |
| Small production (1-2 workers) | 5 | 10 |
| Medium production (4 workers) | 10 | 15 |
| Large production (8+ workers) | 20 | 30 |

### Connection Pool Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `pool_size=100` | Exhausts database connection limit | Size relative to actual concurrency |
| No `pool_pre_ping` | Stale connections cause random errors | Enable for production |
| Creating engine per request | No pooling, connection overhead | Create once at startup |
| No `pool_recycle` | Long-lived connections go stale | Recycle every 1800s |

## SQLModel Alternative

SQLModel combines SQLAlchemy and Pydantic in a single model:

```python
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255, unique=True)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
```

### SQLAlchemy vs SQLModel

| Criterion | SQLAlchemy 2.0 | SQLModel |
|-----------|---------------|----------|
| Complexity | Higher, more explicit | Lower, less boilerplate |
| Pydantic integration | Separate models needed | Unified models |
| Advanced queries | Full SQLAlchemy API | Full SQLAlchemy API |
| Relationship handling | Mature, well-tested | Works but fewer patterns documented |
| Async support | Native async | Native async (uses SQLAlchemy under the hood) |
| Ecosystem | Huge, battle-tested | Growing, backed by FastAPI creator |
| Recommendation | Complex domains, existing projects | New projects, simple CRUD |

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Missing `expire_on_commit=False` | `MissingGreenlet` errors after commit | Set on `async_sessionmaker` |
| Lazy-loading relationships in async | Implicit I/O fails in async context | Use `selectinload()` or `joinedload()` |
| Forgetting to import models in `env.py` | Alembic misses tables in autogenerate | Import all models before `target_metadata` |
| N+1 queries | Fetching related objects one by one | Use eager loading: `selectinload(User.orders)` |
| Not closing engine on shutdown | Connection leak | `await engine.dispose()` in lifespan |
| Sharing sessions across requests | Race conditions, data corruption | Per-request session via dependency |
