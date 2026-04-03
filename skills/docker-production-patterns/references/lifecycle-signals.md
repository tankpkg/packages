# Container Lifecycle and Signals

Sources: Docker documentation (container stop, STOPSIGNAL, HEALTHCHECK), tini project documentation, dumb-init (Yelp) documentation, PID 1 signal handling research (Peter Malmgren, 2024-2026), Node.js/Python/Go signal handling patterns

Covers: the PID 1 problem in containers, SIGTERM and SIGKILL behavior, init systems (tini, dumb-init), exec form vs shell form implications, health check configuration, restart policies, and graceful shutdown patterns for Node.js, Python, Go, and Java.

## The PID 1 Problem

In a Linux container, the first process (PID 1) has special kernel behavior:

- Does NOT receive default signal handlers — SIGTERM is ignored unless explicitly handled
- Is responsible for reaping zombie child processes
- If PID 1 exits, the container stops

### Why This Matters

When Docker stops a container:

1. Docker sends SIGTERM to PID 1
2. Waits for grace period (default: 10 seconds)
3. Sends SIGKILL (cannot be caught or ignored)

If PID 1 does not handle SIGTERM, the application never shuts down gracefully — it just gets killed after the grace period.

### Shell Form Creates a Shell as PID 1

```dockerfile
# Shell form: /bin/sh -c is PID 1, not your application
CMD node server.js
# Process tree:
#   PID 1: /bin/sh -c "node server.js"
#   PID 7: node server.js
```

The shell (`/bin/sh`) is PID 1. Docker sends SIGTERM to the shell. The default shell does not forward signals to child processes. Your application never receives SIGTERM.

### Exec Form Makes Your App PID 1

```dockerfile
# Exec form: node is PID 1, receives signals directly
CMD ["node", "server.js"]
# Process tree:
#   PID 1: node server.js
```

Always use exec form for CMD and ENTRYPOINT in production.

## Init Systems

If the application cannot handle PID 1 responsibilities (signal forwarding, zombie reaping), use a lightweight init system.

### tini

The most widely used container init. 1 binary, ~30KB.

```dockerfile
# Install tini
RUN apt-get update && apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["tini", "--"]
CMD ["node", "server.js"]
# Process tree:
#   PID 1: tini -- node server.js
#   PID 7: node server.js
```

Or use Docker's built-in init:

```bash
docker run --init myapp
```

Docker's `--init` flag uses tini internally. Equivalent to adding tini in the Dockerfile, but controlled at run time.

### dumb-init (Yelp)

Similar to tini but with additional signal rewriting capabilities:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends dumb-init && \
    rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

### When to Use Init

| Scenario | Use init? | Reason |
|----------|-----------|--------|
| Application handles SIGTERM natively | No | App is a proper PID 1 |
| Application spawns child processes | Yes | Need zombie reaping |
| Shell scripts as entrypoint | Yes | Shells don't forward signals |
| Using exec form, single process | Optional | Direct signal handling works |
| Unknown/third-party application | Yes | Defensive default |

### Comparison

| Feature | tini | dumb-init | Docker --init |
|---------|------|-----------|---------------|
| Size | ~30 KB | ~60 KB | Built-in |
| Signal forwarding | Yes | Yes (with rewriting) | Yes |
| Zombie reaping | Yes | Yes | Yes |
| Signal rewriting | No | Yes | No |
| Alpine support | Yes (tini-static) | Yes | Yes |
| Distroless support | Copy binary | Copy binary | Run-time flag only |

## STOPSIGNAL

Override the default stop signal (SIGTERM) for applications that expect a different signal:

```dockerfile
# Nginx expects SIGQUIT for graceful shutdown
STOPSIGNAL SIGQUIT

# Default (usually not needed to specify)
STOPSIGNAL SIGTERM
```

### Common Application Signals

| Application | Graceful stop signal | Notes |
|-------------|---------------------|-------|
| Most applications | SIGTERM (default) | Standard graceful shutdown |
| Nginx | SIGQUIT | Graceful shutdown, finishes requests |
| Apache | SIGWINCH | Graceful stop of workers |
| PostgreSQL | SIGTERM | Smart shutdown |
| Redis | SIGTERM | Saves and exits |
| HAProxy | SIGUSR1 | Graceful stop |

## Grace Period

The time between SIGTERM and SIGKILL. Default is 10 seconds.

```bash
# Override at run time
docker stop --time 30 container_name

# In Compose
services:
  api:
    stop_grace_period: 30s
```

### Setting the Right Grace Period

| Factor | Guidance |
|--------|----------|
| In-flight HTTP requests | Grace period > max request timeout |
| Database transactions | Time to commit or rollback |
| Message queue processing | Time to finish current message + ack |
| File I/O | Time to flush buffers |
| Downstream connections | Time to drain connection pools |
| Default for most apps | 10-30 seconds |

Setting too long wastes time during deployments. Setting too short causes dropped requests.

## Health Checks

Health checks tell Docker (and orchestrators) whether a container is ready to serve traffic.

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
  CMD ["wget", "-q", "--spider", "http://localhost:8080/health"]
```

### Health Check Options

| Option | Default | Purpose |
|--------|---------|---------|
| `--interval` | 30s | Time between checks |
| `--timeout` | 30s | Max time for a single check |
| `--retries` | 3 | Consecutive failures before unhealthy |
| `--start-period` | 0s | Grace period for startup (failures don't count) |

### Health Check Commands by Runtime

| Runtime | Health check command |
|---------|-------------------|
| Node.js | `["CMD", "node", "-e", "fetch('http://localhost:3000/health').then(r => process.exit(r.ok ? 0 : 1))"]` |
| Python | `["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]` |
| Go | Built into binary: expose `/health` endpoint |
| Java | `["CMD", "wget", "-q", "--spider", "http://localhost:8080/actuator/health"]` |
| Nginx | `["CMD", "curl", "-f", "http://localhost:80/health"]` |
| PostgreSQL | `["CMD-SHELL", "pg_isready -U postgres"]` |
| Redis | `["CMD", "redis-cli", "ping"]` |
| Generic (no curl/wget) | `["CMD-SHELL", "test -f /tmp/healthy"]` (app touches file) |

### Health Check Best Practices

| Practice | Reason |
|----------|--------|
| Set `start-period` for slow-starting apps | Prevents false unhealthy during boot |
| Check actual application readiness, not just TCP | Ensures app is processing requests |
| Keep checks lightweight | Avoid database queries in health endpoint |
| Return 200 for healthy, 503 for unhealthy | Standard HTTP health check convention |
| Include dependency checks in readiness probe | If database is down, app cannot serve |

### Container States

| State | Meaning | Behavior |
|-------|---------|----------|
| `starting` | In start_period, checks running | Not considered unhealthy yet |
| `healthy` | Last N checks passed | Traffic routed normally |
| `unhealthy` | N consecutive failures | Restart per policy; no traffic from orchestrator |

## Restart Policies

| Policy | Behavior | Compose syntax | Use case |
|--------|----------|---------------|----------|
| `no` | Never restart | `restart: "no"` | One-shot, development |
| `always` | Always restart (including after daemon restart) | `restart: always` | Critical infrastructure |
| `unless-stopped` | Like always, but not after manual stop | `restart: unless-stopped` | Standard production |
| `on-failure` | Restart only on non-zero exit | `restart: on-failure` | Workers, batch |
| `on-failure:5` | Restart on failure, max 5 attempts | `restart: "on-failure:5"` | Crash loops |

## Graceful Shutdown Patterns

### Node.js

```javascript
const server = app.listen(3000);

process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    // Close database connections
    pool.end().then(() => {
      console.log('All connections closed');
      process.exit(0);
    });
  });

  // Force exit after timeout
  setTimeout(() => {
    console.error('Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
});
```

### Python (uvicorn / gunicorn)

```python
import signal
import sys

def graceful_shutdown(signum, frame):
    print("Shutting down gracefully...")
    # Close database connections, flush buffers
    db.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
```

Gunicorn handles SIGTERM natively — it sends SIGTERM to workers and waits for `graceful_timeout`.

### Go

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer stop()

srv := &http.Server{Addr: ":8080", Handler: router}
go func() { srv.ListenAndServe() }()

<-ctx.Done()
shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
srv.Shutdown(shutdownCtx)
```

### Java (Spring Boot)

Spring Boot handles graceful shutdown when configured:

```yaml
# application.yml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

### Shutdown Sequence Checklist

1. Receive SIGTERM
2. Stop accepting new connections
3. Finish in-flight requests (drain)
4. Close database connection pools
5. Flush log buffers
6. Deregister from service discovery
7. Exit with code 0

If any step blocks, the force-exit timeout (10s default) triggers SIGKILL.

## Entrypoint Scripts

When initialization is needed before the main process, use an entrypoint script with `exec`:

```bash
#!/bin/sh
set -e

# Run migrations
python manage.py migrate --noop

# Replace shell with application process
exec "$@"
```

```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

The `exec "$@"` replaces the shell with the CMD process, making CMD the new PID 1. Without `exec`, the shell remains PID 1 and signals are not forwarded.
