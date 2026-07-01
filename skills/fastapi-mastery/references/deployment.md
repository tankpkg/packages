# Deployment

Sources: FastAPI official documentation (fastapi.tiangolo.com/deployment), Uvicorn documentation (uvicorn.org), Docker official best practices, Kubernetes documentation, production FastAPI deployment patterns

Covers: Uvicorn configuration and workers, Docker multi-stage builds, Kubernetes health probes, gunicorn with uvicorn workers, serverless deployment with Mangum, environment configuration, and production readiness checklist.

## Uvicorn Configuration

Uvicorn is the recommended ASGI server for FastAPI.

### Development

```bash
# Using FastAPI CLI (recommended)
fastapi dev app/main.py

# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Single worker
fastapi run app/main.py --port 8000

# Multiple workers
fastapi run app/main.py --port 8000 --workers 4

# Direct uvicorn with full control
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools
```

### Uvicorn Settings

| Setting | Development | Production |
|---------|------------|------------|
| `--reload` | Yes | No |
| `--workers` | 1 | `(2 * CPU cores) + 1` |
| `--host` | `127.0.0.1` | `0.0.0.0` |
| `--loop` | Default | `uvloop` (Linux) |
| `--http` | Default | `httptools` |
| `--access-log` | Yes | Depends (use structured logging instead) |
| `--proxy-headers` | No | Yes (behind reverse proxy) |
| `--forwarded-allow-ips` | N/A | Proxy IP or `*` |
| `--limit-concurrency` | None | Set based on memory |
| `--timeout-keep-alive` | 5 | 5-30 |

### Worker Count Formula

```
workers = (2 * cpu_cores) + 1
```

For a 4-core machine: 9 workers. Adjust based on memory -- each worker consumes 50-200MB depending on application.

## Gunicorn with Uvicorn Workers

For process management with auto-restart on worker death:

```bash
gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
```

Note: Modern uvicorn (with `--workers`) handles worker management natively. Gunicorn is optional but adds features like graceful reload (`kill -HUP`) and automatic worker restart.

### Gunicorn vs Uvicorn Workers

| Feature | Uvicorn `--workers` | Gunicorn + Uvicorn |
|---------|--------------------|--------------------|
| Worker management | Basic | Mature (auto-restart, graceful reload) |
| Signal handling | Basic | Advanced (HUP, USR1, USR2) |
| Pre-fork model | Yes | Yes |
| Configuration file | No | `gunicorn.conf.py` |
| Memory management | Manual | Better (worker recycling) |
| Recommendation | Simple deployments, containers | VMs, bare metal, complex setups |

## Docker Deployment

### Production Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

# Security: non-root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /code

# Copy dependencies from builder
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages

# Copy application code
COPY ./app /code/app

# Switch to non-root user
USER app

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--proxy-headers"]
```

### Dockerfile Best Practices

| Practice | Reason |
|----------|--------|
| Multi-stage builds | Smaller final image (no build tools) |
| Non-root user | Security -- limits container escape damage |
| Copy requirements first | Docker layer caching for faster rebuilds |
| `--no-cache-dir` on pip | Smaller image, no cached wheels |
| `.dockerignore` file | Exclude tests, docs, .git from image |
| Pin base image version | Reproducible builds |
| Use `CMD` exec form (JSON array) | Proper signal handling, graceful shutdown |
| `EXPOSE` port | Documentation and tooling hints |

### .dockerignore

```
.git
.venv
__pycache__
*.pyc
tests/
docs/
.env
.env.*
docker-compose*.yml
README.md
```

### Docker Compose for Development

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./app:/code/app  # Hot reload in dev

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

## Kubernetes Deployment

### Health Probes

```python
# app/main.py or app/health/router.py
from fastapi import APIRouter
from sqlalchemy import text

health_router = APIRouter(tags=["health"])

@health_router.get("/healthz")
async def liveness():
    """Liveness probe: is the process alive?"""
    return {"status": "ok"}

@health_router.get("/readyz")
async def readiness(session: AsyncSessionDep):
    """Readiness probe: can the service handle requests?"""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "detail": "Database unavailable"},
        )
```

### Kubernetes Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: app
          image: myregistry/fastapi-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: database-url
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "128Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "1000m"
```

### Container Replication Strategy

| Deployment | Workers per Container | Containers |
|-----------|----------------------|------------|
| Docker Compose (single host) | `(2 * cores) + 1` | 1 |
| Kubernetes | 1 | Scale with HPA |
| Serverless | 1 | Platform manages |

In Kubernetes: run one uvicorn process per container, scale horizontally with replicas. The cluster handles load balancing.

## Serverless Deployment

### AWS Lambda with Mangum

```python
# app/main.py
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

# ... routes ...

# Lambda handler
handler = Mangum(app, lifespan="off")
```

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["app.main.handler"]
```

### Serverless Considerations

| Factor | Impact |
|--------|--------|
| Cold starts | 1-5 seconds on first invocation |
| Connection pooling | Cannot maintain persistent pools -- use RDS Proxy |
| Lifespan events | Unreliable -- disable with `lifespan="off"` |
| WebSockets | Not supported on Lambda |
| File system | Read-only except `/tmp` (512MB-10GB) |
| Timeout | 15 minutes maximum |

## Environment Configuration

### 12-Factor App Pattern

| Principle | Implementation |
|-----------|---------------|
| Config via env vars | Pydantic `BaseSettings` reads from environment |
| One codebase, many deploys | Same image, different env vars per environment |
| Port binding | `--port` flag, not hardcoded |
| Stateless processes | No in-process state -- use Redis/database |
| Logs as event streams | Structured JSON to stdout |

### Environment Files

```
# .env.example (commit this)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/app
REDIS_URL=redis://localhost:6379
JWT_SECRET=change-me-in-production
DEBUG=true

# .env (do NOT commit)
DATABASE_URL=postgresql+asyncpg://prod-user:prod-pass@prod-host:5432/app
JWT_SECRET=<generated-secret>
DEBUG=false
```

## Production Readiness Checklist

| Item | Check |
|------|-------|
| HTTPS via TLS termination proxy | Nginx, Traefik, or cloud load balancer |
| Non-root Docker user | `USER app` in Dockerfile |
| Health endpoints | `/healthz` (liveness) and `/readyz` (readiness) |
| Structured logging | JSON format to stdout |
| Graceful shutdown | `CMD` exec form, `--proxy-headers` |
| Secret management | Environment variables or secret manager (not .env in production) |
| Database migrations before deploy | Alembic in init container or pre-deploy step |
| Rate limiting | Middleware or API gateway |
| CORS configured | Specific origins, not `["*"]` with credentials |
| Docs disabled in production | `docs_url=None` or auth-gated |
| Error responses sanitized | No stack traces in responses |
| Connection pool sized correctly | Monitor and tune `pool_size` |

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| `--reload` in production | Performance overhead, file watching | Remove flag |
| Root user in container | Security vulnerability | `USER app` in Dockerfile |
| No health checks | Kubernetes sends traffic to unhealthy pods | Add `/healthz` and `/readyz` |
| Hardcoded secrets | Secrets in source control | Environment variables |
| Missing `--proxy-headers` | Wrong client IP behind load balancer | Add flag when behind proxy |
| `docs_url="/docs"` in production | OpenAPI schema exposed | Set `docs_url=None` or gate with auth |
| No graceful shutdown handling | Requests dropped during deploy | Exec form CMD, readiness probe |
