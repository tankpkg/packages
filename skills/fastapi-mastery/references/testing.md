# Testing

Sources: FastAPI official documentation (fastapi.tiangolo.com/tutorial/testing), HTTPX documentation (python-httpx.org), pytest documentation, Starlette TestClient internals, production FastAPI test patterns

Covers: TestClient usage, async testing with httpx AsyncClient, dependency overrides, database test fixtures, authentication testing, factory patterns, and test organization.

## TestClient Basics

FastAPI's `TestClient` wraps HTTPX for synchronous testing:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/api/v1/items/",
        json={"name": "Widget", "price": 9.99},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget"
    assert "id" in data
```

### TestClient Request Methods

| Method | Example |
|--------|---------|
| GET with query params | `client.get("/items/", params={"skip": 0, "limit": 10})` |
| POST with JSON body | `client.post("/items/", json={"name": "Widget"})` |
| POST with form data | `client.post("/login", data={"username": "u", "password": "p"})` |
| PUT | `client.put("/items/1", json={"name": "Updated"})` |
| PATCH | `client.patch("/items/1", json={"price": 19.99})` |
| DELETE | `client.delete("/items/1")` |
| With headers | `client.get("/me", headers={"Authorization": "Bearer token"})` |
| With cookies | `client.get("/me", cookies={"session": "abc"})` |
| File upload | `client.post("/upload", files={"file": ("name.txt", b"content")})` |

## Dependency Overrides

Replace real dependencies with test doubles:

```python
from app.main import app
from app.core.database import get_session
from app.core.security import get_current_user
from app.users.models import User

# Test database session
async def override_get_session():
    async with test_session_maker() as session:
        yield session

# Fake authenticated user
def override_get_current_user():
    return User(id=1, name="Test User", email="test@example.com", is_active=True)

app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_get_current_user
```

### Override Cleanup

Always clean up overrides to prevent test pollution:

```python
import pytest

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
```

## Test Fixtures with pytest

### conftest.py Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_session, Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db_session):
    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### Authenticated Client Fixture

```python
from app.core.security import get_current_user, create_access_token
from app.users.models import User

@pytest.fixture
def test_user() -> User:
    return User(
        id=1,
        name="Test User",
        email="test@example.com",
        is_active=True,
        role="user",
    )

@pytest.fixture
def auth_client(client, test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield client
    # clear_overrides autouse fixture handles cleanup

@pytest.fixture
def admin_client(client):
    admin = User(id=99, name="Admin", email="admin@example.com", role="admin", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: admin
    yield client
```

### Use in Tests

```python
def test_list_items_authenticated(auth_client):
    response = auth_client.get("/api/v1/items/")
    assert response.status_code == 200

def test_list_items_unauthenticated(client):
    response = client.get("/api/v1/items/")
    assert response.status_code == 401

def test_delete_item_admin_only(admin_client):
    response = admin_client.delete("/api/v1/items/1")
    assert response.status_code == 200

def test_delete_item_regular_user(auth_client):
    response = auth_client.delete("/api/v1/items/1")
    assert response.status_code == 403
```

## Async Testing

Use `httpx.AsyncClient` when testing async-specific behavior:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.anyio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/v1/items/")
    assert response.status_code == 200
```

### When to Use Async Tests

| Scenario | Use |
|----------|-----|
| Standard route testing | `TestClient` (sync, simpler) |
| Testing async side effects | `AsyncClient` |
| Database operations in test setup | `AsyncClient` with `pytest-asyncio` |
| WebSocket testing | `TestClient` WebSocket methods |
| Streaming response testing | `AsyncClient` |

### pytest Configuration for Async

```ini
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # or "strict"
```

Install: `pip install pytest-asyncio` (or `pip install anyio pytest-anyio`).

## Database Testing Strategies

### Strategy 1: Rollback After Each Test

```python
@pytest.fixture
async def db_session():
    async with test_session_maker() as session:
        async with session.begin():
            yield session
        # Implicit rollback -- no commit, so changes are discarded
```

### Strategy 2: Truncate Tables Between Tests

```python
@pytest.fixture(autouse=True)
async def clean_tables(db_session):
    yield
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()
```

### Strategy 3: Separate Test Database

```python
# Use a completely separate database for tests
# Set TEST_DATABASE_URL in test environment
# Run migrations before test suite
# Drop database after test suite
```

| Strategy | Speed | Isolation | Complexity |
|----------|-------|-----------|------------|
| Rollback per test | Fast | High | Low |
| Truncate tables | Medium | High | Medium |
| Separate database | Slow | Highest | High |

Prefer rollback per test for unit tests. Use separate database for integration tests.

## Factory Pattern for Test Data

```python
# tests/factories.py
from app.users.models import User
from app.core.security import hash_password

class UserFactory:
    _counter = 0

    @classmethod
    def create(cls, **overrides) -> User:
        cls._counter += 1
        defaults = {
            "name": f"User {cls._counter}",
            "email": f"user{cls._counter}@example.com",
            "hashed_password": hash_password("testpassword"),
            "is_active": True,
            "role": "user",
        }
        defaults.update(overrides)
        return User(**defaults)

class ItemFactory:
    _counter = 0

    @classmethod
    def create(cls, **overrides) -> dict:
        cls._counter += 1
        defaults = {
            "name": f"Item {cls._counter}",
            "price": 9.99,
            "description": "Test item",
        }
        defaults.update(overrides)
        return defaults
```

### Use Factories in Tests

```python
async def test_list_users(auth_client, db_session):
    # Arrange
    for _ in range(3):
        user = UserFactory.create()
        db_session.add(user)
    await db_session.commit()

    # Act
    response = auth_client.get("/api/v1/users/")

    # Assert
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
```

## WebSocket Testing

```python
def test_websocket_echo(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text("Hello")
        data = ws.receive_text()
        assert data == "Message: Hello"

def test_websocket_json(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"action": "subscribe", "channel": "updates"})
        data = ws.receive_json()
        assert data["status"] == "subscribed"
```

## Test Organization

```
tests/
  __init__.py
  conftest.py           # Shared fixtures
  factories.py          # Test data factories
  features/
    __init__.py
    test_users.py       # User CRUD tests
    test_items.py       # Item CRUD tests
    test_auth.py        # Authentication tests
  integration/
    __init__.py
    test_workflows.py   # Multi-step workflows
```

### Naming Conventions

| Pattern | Example |
|---------|---------|
| Test function | `test_{action}_{scenario}` |
| Happy path | `test_create_user_valid_data` |
| Error case | `test_create_user_duplicate_email` |
| Auth test | `test_list_items_unauthenticated` |
| Edge case | `test_create_user_empty_name` |

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Not clearing `dependency_overrides` | Tests affect each other | `autouse` fixture with `.clear()` |
| Using production database in tests | Data corruption | Separate test database or rollback |
| Async test without `pytest-asyncio` | Tests silently skip or fail | Install and configure `asyncio_mode` |
| Sharing state between tests | Flaky, order-dependent tests | Factory pattern, rollback per test |
| Testing implementation instead of behavior | Brittle tests break on refactor | Test HTTP responses, not internals |
| Hardcoded test data | Collisions between tests | Factory with unique counters |
| Not testing error responses | Missing coverage | Test 4xx and 5xx explicitly |
