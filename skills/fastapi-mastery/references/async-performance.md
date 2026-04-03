# Async Patterns and Performance

Sources: FastAPI official documentation (fastapi.tiangolo.com/async), Python asyncio documentation, Starlette internals, Uvicorn documentation, production FastAPI performance patterns

Covers: async vs sync route selection, BackgroundTasks, Celery integration, WebSocket patterns, streaming responses, Redis caching, connection pooling, response optimization, and profiling.

## Async vs Sync Routes

FastAPI handles `async def` and `def` routes differently:

| Declaration | Execution | Thread |
|------------|-----------|--------|
| `async def` | Runs on the main event loop | Main async thread |
| `def` | Runs in a thread pool (via `run_in_executor`) | Background thread |

### When to Use Each

```python
# CORRECT: async for I/O-bound operations
@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSessionDep):
    return await session.get(User, user_id)

# CORRECT: sync for CPU-bound or blocking libraries
@router.post("/process-image/")
def process_image(file: UploadFile):
    image = PIL.Image.open(file.file)
    processed = apply_filters(image)  # CPU-bound
    return {"size": processed.size}

# WRONG: async def with blocking call -- blocks the event loop
@router.get("/bad/")
async def bad_route():
    time.sleep(5)  # Blocks ALL other requests
    return {"status": "done"}
```

### Decision Matrix

| Operation | Route Type | Reason |
|-----------|-----------|--------|
| SQLAlchemy async query | `async def` | Awaitable database I/O |
| HTTP call with httpx | `async def` | Awaitable network I/O |
| File read with aiofiles | `async def` | Awaitable file I/O |
| PIL image processing | `def` | CPU-bound, runs in thread pool |
| pandas data processing | `def` | CPU-bound |
| Blocking library (no async API) | `def` | Prevents event loop blocking |
| Simple computation, no I/O | Either | Minimal difference |

### Running Async Tasks Concurrently

```python
import asyncio

@router.get("/dashboard/")
async def dashboard(session: AsyncSessionDep):
    # Run independent queries concurrently
    users_task = session.execute(select(func.count()).select_from(User))
    orders_task = session.execute(select(func.count()).select_from(Order))
    revenue_task = session.execute(
        select(func.sum(Order.total)).where(Order.status == "completed")
    )

    users, orders, revenue = await asyncio.gather(
        users_task, orders_task, revenue_task
    )

    return {
        "total_users": users.scalar_one(),
        "total_orders": orders.scalar_one(),
        "total_revenue": float(revenue.scalar_one() or 0),
    }
```

## BackgroundTasks

For fire-and-forget work that takes less than a few seconds:

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str):
    # Simulated email sending
    await email_service.send(
        to=email,
        subject="Welcome!",
        body=f"Hello {name}, welcome aboard!",
    )

@router.post("/users/", status_code=201)
async def create_user(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends()],
):
    user = await service.create(data)
    background_tasks.add_task(send_welcome_email, user.email, user.name)
    return user  # Response sent immediately, email sends in background
```

### BackgroundTasks vs Celery

| Factor | BackgroundTasks | Celery |
|--------|----------------|--------|
| Infrastructure | None (in-process) | Redis/RabbitMQ broker + worker processes |
| Retry logic | None | Built-in with exponential backoff |
| Task monitoring | None | Flower dashboard, result backend |
| Scaling | Limited to single process | Horizontal worker scaling |
| Persistence | Lost on crash | Persisted in broker |
| Use case | Email notifications, logging, cache invalidation | Report generation, video processing, data pipelines |
| Duration limit | < 5 seconds recommended | Minutes to hours |

## Celery Integration

### Setup

```python
# app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

### Define Tasks

```python
# app/tasks/reports.py
from app.core.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_id: int):
    try:
        # Heavy processing
        data = fetch_report_data(report_id)
        pdf = render_pdf(data)
        upload_to_s3(pdf, f"reports/{report_id}.pdf")
        update_report_status(report_id, "completed")
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
```

### Trigger from Route

```python
from app.tasks.reports import generate_report

@router.post("/reports/")
async def create_report(data: ReportCreate, service: ReportServiceDep):
    report = await service.create(data)
    generate_report.delay(report.id)  # Enqueue task
    return {"id": report.id, "status": "processing"}

@router.get("/reports/{report_id}/status")
async def report_status(report_id: int):
    task = generate_report.AsyncResult(report_id)
    return {"status": task.state, "result": task.result}
```

## WebSocket Patterns

### Basic WebSocket Endpoint

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

### Connection Manager

```python
class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    def connect(self, client_id: str, websocket: WebSocket):
        self.connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)

    async def send_to(self, client_id: str, message: str):
        ws = self.connections.get(client_id)
        if ws:
            await ws.send_text(message)

    async def broadcast(self, message: str):
        disconnected = []
        for client_id, ws in self.connections.items():
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(client_id)
        for cid in disconnected:
            self.disconnect(cid)

manager = ConnectionManager()
```

### WebSocket Authentication

```python
from fastapi import Query, WebSocket, WebSocketException, status

@app.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    session: AsyncSessionDep = Depends(),
):
    try:
        user = await validate_token(token, session)
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    await websocket.accept()
    # ... handle messages
```

## Streaming Responses

### Server-Sent Events (SSE)

```python
from fastapi.responses import StreamingResponse
import asyncio

async def event_generator():
    while True:
        data = await get_latest_data()
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(1)

@router.get("/stream/events")
async def stream_events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

### File Streaming

```python
from fastapi.responses import StreamingResponse

@router.get("/download/{file_id}")
async def download_file(file_id: int):
    async def file_iterator():
        async with aiofiles.open(f"/files/{file_id}", "rb") as f:
            while chunk := await f.read(8192):
                yield chunk

    return StreamingResponse(
        file_iterator(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=file_{file_id}"},
    )
```

## Redis Caching

### Setup

```python
# app/core/cache.py
import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_cache(key: str) -> str | None:
    return await redis_client.get(key)

async def set_cache(key: str, value: str, ttl: int = 300):
    await redis_client.set(key, value, ex=ttl)

async def invalidate_cache(pattern: str):
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)
```

### Cache Decorator Pattern

```python
import functools
import json

def cached(ttl: int = 300, prefix: str = "cache"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached_result = await get_cache(key)
            if cached_result:
                return json.loads(cached_result)
            result = await func(*args, **kwargs)
            await set_cache(key, json.dumps(result, default=str), ttl)
            return result
        return wrapper
    return decorator
```

## Performance Optimization

### Response Model Performance

```python
# Slow: Pydantic validates the entire response
@router.get("/items/", response_model=list[ItemResponse])
async def list_items():
    return items

# Faster for large payloads: skip validation when you trust the data
from fastapi.responses import ORJSONResponse

@router.get("/items/")
async def list_items():
    items = await fetch_items()
    return ORJSONResponse(content=[item.dict() for item in items])
```

### Install orjson for Faster JSON

```bash
pip install orjson
```

```python
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
```

### Performance Checklist

| Optimization | Impact | Effort |
|-------------|--------|--------|
| Use `async def` for I/O routes | High | Low |
| Enable `uvloop` and `httptools` | Medium | Low |
| Use `orjson` for serialization | Medium | Low |
| Connection pooling (database, Redis) | High | Low |
| Cache frequent queries in Redis | High | Medium |
| Use `selectinload` for relationships | High | Low |
| Stream large responses | Medium | Medium |
| Profile with `py-spy` or `yappi` | Diagnostic | Medium |
| Avoid N+1 queries | High | Medium |
| Use CDN for static assets | High | Low |

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| `async def` with blocking call | Blocks all concurrent requests | Use `def` or `run_in_executor` |
| Creating connections per request | Connection overhead, pool exhaustion | Singleton engine, per-request sessions |
| No cache invalidation strategy | Stale data served | TTL + explicit invalidation on write |
| WebSocket without ping/pong | Dead connections consume resources | Implement heartbeat |
| Background task exception ignored | Silent failures | Log exceptions in background tasks |
| Streaming without backpressure | Memory growth for slow clients | Limit buffer size |
