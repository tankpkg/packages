# Compose for Production

Sources: Docker Compose Specification (2025-2026), Docker Compose production guide, Docker Compose profiles documentation, Docker networking documentation

Covers: production Compose configuration, profiles for environment-specific services, service dependencies and startup ordering, override files, secrets management, resource limits, networking patterns, and environment variable management.

## Compose v2 Production Configuration

Docker Compose is suitable for single-host production when high availability and auto-scaling are not required. The key is configuring production concerns that development Compose files omit: resource limits, restart policies, health checks, logging limits, and secrets.

### Minimal Production Service

```yaml
services:
  api:
    image: myrepo/api:v1.2.3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M
          cpus: "0.25"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    environment:
      NODE_ENV: production
    secrets:
      - db_password
    networks:
      - backend
```

### Production vs Development Concerns

| Concern | Development | Production |
|---------|------------|------------|
| Image source | Build from local source | Pull from registry (pinned tag) |
| Restart policy | `no` (default) | `unless-stopped` or `always` |
| Resource limits | None | Memory and CPU limits |
| Health checks | Optional | Required |
| Logging | Default (unlimited) | Rotation configured |
| Volumes | Bind mounts for hot reload | Named volumes only |
| Secrets | .env file or env vars | Compose secrets (file-based) |
| Ports | Expose for development access | Expose through reverse proxy only |
| Networks | Default bridge | Explicit named networks |

## Override Files

Split configuration into base + environment-specific overrides. Compose merges files in order.

### File Structure

```
project/
  docker-compose.yml           # Base: service definitions, networks, volumes
  docker-compose.override.yml  # Dev overrides (auto-loaded)
  docker-compose.prod.yml      # Production overrides
  docker-compose.test.yml      # Test overrides
```

### Base File (docker-compose.yml)

```yaml
services:
  api:
    image: myrepo/api:latest
    networks:
      - backend
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

volumes:
  pgdata:

networks:
  backend:
```

### Development Override (docker-compose.override.yml)

```yaml
services:
  api:
    build:
      context: .
      target: development
    volumes:
      - .:/app:cached
      - /app/node_modules
    ports:
      - "3000:3000"
      - "9229:9229"
    environment:
      NODE_ENV: development
      DEBUG: "*"

  db:
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: devpassword
```

### Production Override (docker-compose.prod.yml)

```yaml
services:
  api:
    image: myrepo/api:v1.2.3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
    secrets:
      - db_password
    environment:
      NODE_ENV: production

  db:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### Running with Overrides

```bash
# Development (auto-loads docker-compose.override.yml)
docker compose up

# Production (explicit override, skips override.yml)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Shorthand with COMPOSE_FILE
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose up -d
```

## Profiles

Profiles enable environment-specific services within a single Compose file. Services without a profile always start. Services with a profile only start when that profile is activated.

```yaml
services:
  api:
    image: myrepo/api:latest
    # No profile = always starts

  db:
    image: postgres:16-alpine
    # No profile = always starts

  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    profiles:
      - debug

  prometheus:
    image: prom/prometheus:latest
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    profiles:
      - monitoring
```

```bash
# Start core services only
docker compose up -d

# Start core + monitoring
docker compose --profile monitoring up -d

# Start core + debug + monitoring
docker compose --profile debug --profile monitoring up -d
```

### Profile Patterns

| Pattern | Example |
|---------|---------|
| Debug tools (dev only) | adminer, pgadmin, mailhog |
| Monitoring stack | prometheus, grafana, alertmanager |
| Testing dependencies | selenium, wiremock |
| Worker processes | background jobs, cron |
| Optional integrations | redis, elasticsearch |

## Service Dependencies

### depends_on with Health Checks

The `condition` field controls startup ordering based on service state:

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully

  migrations:
    image: myrepo/api:latest
    command: ["npm", "run", "migrate"]
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

### Dependency Conditions

| Condition | Waits until |
|-----------|------------|
| `service_started` | Container started (default, no health check wait) |
| `service_healthy` | Health check passes |
| `service_completed_successfully` | Container exits with code 0 |

### Startup Order Pattern

```
db (health check) -> migrations (runs, exits 0) -> api (starts)
redis (health check) ─────────────────────────────> api (starts)
```

Use `service_completed_successfully` for init containers (migrations, seed data).

## Resource Limits

Without limits, a single container can consume all host memory and crash other services.

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
          pids: 100
        reservations:
          memory: 256M
          cpus: "0.25"
```

### Limit Guidelines

| Service type | Memory limit | CPU limit |
|-------------|-------------|-----------|
| Node.js API | 256M-512M | 0.5-1.0 |
| Python API | 256M-1G | 0.5-1.0 |
| Go API | 64M-256M | 0.25-0.5 |
| PostgreSQL | 512M-2G | 0.5-2.0 |
| Redis | 128M-512M | 0.25-0.5 |
| Nginx | 64M-128M | 0.25 |

### OOM Behavior

When a container exceeds its memory limit, the kernel OOM killer terminates it. The container restarts per its restart policy. Monitor for OOM kills:

```bash
docker inspect --format='{{.State.OOMKilled}}' container_name
docker events --filter event=oom
```

## Networking

### Named Networks

Always use explicit named networks instead of the default bridge:

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  nginx:
    networks:
      - frontend
      - backend
  api:
    networks:
      - backend
  db:
    networks:
      - backend
```

### Network Isolation Patterns

| Pattern | Configuration | Effect |
|---------|--------------|--------|
| Internal network | `internal: true` | No external internet access |
| Service isolation | Separate networks per tier | Database unreachable from frontend |
| External access | Reverse proxy on frontend network only | Single entry point |

### DNS Service Discovery

Compose creates DNS entries for each service. Services communicate by service name:

```
# From api container
postgresql://db:5432/mydb    # 'db' resolves to database container
http://redis:6379            # 'redis' resolves to redis container
```

Service names are the DNS hostnames within the Compose network.

## Environment Management

### Priority Order (highest to lowest)

1. `docker compose run -e VAR=val` (command line)
2. `environment:` in Compose file
3. `--env-file` flag on command line
4. `env_file:` in Compose file
5. `.env` file in project directory

### .env vs env_file

| Feature | `.env` | `env_file:` |
|---------|--------|-------------|
| Purpose | Variable substitution in Compose file | Injected into container |
| Scope | Compose file parsing | Container runtime |
| Syntax | `VAR=value` | `VAR=value` |
| Location | Project root (auto-loaded) | Any path |

```yaml
services:
  api:
    image: myrepo/api:${IMAGE_TAG}  # ${IMAGE_TAG} from .env
    env_file:
      - ./config/common.env          # Injected into container
    environment:
      NODE_ENV: production            # Overrides env_file value
```

### Restart Policies

| Policy | Behavior | Use when |
|--------|----------|----------|
| `no` | Never restart | One-shot tasks, development |
| `always` | Restart unconditionally | Critical services |
| `unless-stopped` | Restart unless manually stopped | Standard production |
| `on-failure[:max]` | Restart only on non-zero exit | Workers, batch jobs |

## Compose Production Review Questions

1. Is Compose being used as a production runtime, staging convenience, or local-prod parity tool?
2. Are restart, healthcheck, and env decisions reflecting real operational behavior?
3. Is this Compose setup documenting the system clearly, or becoming a shadow orchestrator?
