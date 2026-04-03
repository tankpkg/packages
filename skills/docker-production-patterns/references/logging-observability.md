# Logging and Observability

Sources: Docker logging driver documentation (2025-2026), Docker resource constraints reference, Fluentd/Fluent Bit documentation, 12-Factor App methodology (Heroku), Prometheus Docker monitoring patterns

Covers: log drivers and configuration, log rotation, structured logging from containers, resource limits (CPU, memory, PIDs), OOM behavior and debugging, and container monitoring patterns.

## Container Logging Architecture

Docker captures stdout and stderr from every container. The logging driver determines where those streams go. Applications running in containers write to stdout/stderr — not to files inside the container.

### The 12-Factor Rule

Write logs to stdout/stderr and let the platform handle routing. No log files inside containers — they complicate rotation, are lost when containers stop, and bypass Docker's logging infrastructure.

```dockerfile
# Good: application logs to stdout
CMD ["node", "server.js"]

# Bad: application logs to file inside container
CMD ["node", "server.js", "--log-file=/var/log/app.log"]
```

## Log Drivers

### Driver Comparison

| Driver | Destination | Blocking | Local access | Production use |
|--------|------------|----------|-------------|----------------|
| `json-file` | Local JSON files | Yes (default) | `docker logs` works | Single host, with rotation |
| `local` | Compressed local files | Yes | `docker logs` works | Efficient local storage |
| `syslog` | Syslog daemon | Configurable | No `docker logs` | Unix syslog infrastructure |
| `journald` | systemd journal | Configurable | `docker logs` works | systemd hosts |
| `fluentd` | Fluentd collector | Configurable | No `docker logs` | Centralized logging stack |
| `awslogs` | CloudWatch Logs | Configurable | No `docker logs` | AWS deployments |
| `gcplogs` | Google Cloud Logging | Configurable | No `docker logs` | GCP deployments |
| `none` | Nowhere | N/A | No | Extremely chatty sidecars |

### json-file Driver (Default)

The default driver. Stores logs as JSON on the host filesystem.

**Without rotation, logs grow unbounded and fill the disk.**

```json
{
  "log": "Server started on port 3000\n",
  "stream": "stdout",
  "time": "2025-01-15T10:30:00.123456789Z"
}
```

### Configuring json-file with Rotation

#### Per-Container (Compose)

```yaml
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
        compress: "true"
        tag: "{{.Name}}"
```

#### Daemon-Wide Default

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Set in `/etc/docker/daemon.json`. Applies to all containers that do not override the log driver.

### Log Rotation Settings

| Option | Default | Recommended | Purpose |
|--------|---------|-------------|---------|
| `max-size` | Unlimited | `10m`-`50m` | Max size per log file |
| `max-file` | 1 | `3`-`5` | Number of rotated files |
| `compress` | `false` | `true` | Compress rotated files |
| `tag` | Container ID | `{{.Name}}` | Tag format in log entries |

### Disk Space Calculation

```
max_disk_per_container = max-size * max-file
total = max_disk_per_container * number_of_containers
```

Example: 10 containers with `max-size: 10m` and `max-file: 5` = 500 MB max log storage.

## Blocking vs Non-Blocking Mode

By default, log delivery blocks the container's stdout/stderr if the logging driver cannot keep up. This means a slow fluentd endpoint can freeze your application.

### Non-Blocking Mode

```yaml
services:
  api:
    logging:
      driver: fluentd
      options:
        mode: non-blocking
        max-buffer-size: 4m
        fluentd-address: localhost:24224
```

| Mode | Behavior | Risk |
|------|----------|------|
| `blocking` (default) | Container waits for driver | Application freezes if driver slow |
| `non-blocking` | Logs buffered in ring buffer | Logs dropped if buffer full |

Use non-blocking for production when log loss is acceptable over application freezing. Set `max-buffer-size` to control the ring buffer.

## Fluentd/Fluent Bit Integration

For centralized logging, use Fluentd or Fluent Bit as a log aggregator.

### Compose with Fluentd

```yaml
services:
  api:
    image: myrepo/api:latest
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: app.api
        fluentd-async: "true"

  fluentd:
    image: fluent/fluentd:v1.17
    volumes:
      - ./fluentd/conf:/fluentd/etc
    ports:
      - "24224:24224"
```

### Fluent Bit (Lightweight Alternative)

Fluent Bit uses ~450KB memory vs Fluentd's ~40MB. Preferred for sidecar patterns:

```yaml
services:
  fluent-bit:
    image: fluent/fluent-bit:latest
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
    profiles:
      - monitoring
```

## Structured Logging

Emit JSON logs from the application. Structured logs are parseable by log aggregators without regex.

### JSON Log Format

```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "info",
  "message": "Request completed",
  "method": "GET",
  "path": "/api/users",
  "status": 200,
  "duration_ms": 45,
  "request_id": "abc-123",
  "service": "api"
}
```

### Structured Logging Libraries

| Language | Library | JSON output |
|----------|---------|-------------|
| Node.js | pino, winston | Built-in JSON format |
| Python | structlog, python-json-logger | Built-in |
| Go | zerolog, zap | Built-in |
| Java | Logback + JSON encoder | Via logstash-logback-encoder |
| Rust | tracing + tracing-subscriber | Via json feature |

### Log Levels in Production

| Level | Use for | Volume |
|-------|---------|--------|
| `error` | Failures requiring attention | Low |
| `warn` | Degraded behavior, approaching limits | Low-medium |
| `info` | Business events, request summaries | Medium |
| `debug` | Diagnostic detail | High (disabled in prod) |
| `trace` | Extremely verbose | Very high (disabled in prod) |

Set production log level to `info`. Enable `debug` temporarily for troubleshooting using environment variable:

```yaml
environment:
  LOG_LEVEL: ${LOG_LEVEL:-info}
```

## Resource Limits

### Memory Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

Docker enforces memory limits via cgroups. When a container exceeds its limit, the kernel OOM killer terminates it.

### CPU Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1.5"
        reservations:
          cpus: "0.25"
```

| Setting | Meaning |
|---------|---------|
| `cpus: "1.0"` | Container can use 1 full CPU core |
| `cpus: "0.5"` | Container gets 50% of one core |
| `cpus: "2.0"` | Container can use 2 full cores |
| Reservation | Minimum guaranteed (for scheduling) |
| Limit | Maximum allowed (hard cap) |

### PID Limits

Prevent fork bombs and runaway process spawning:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          pids: 100
```

Or via Docker run:

```bash
docker run --pids-limit 100 myapp
```

### Memory Limit per Language

| Language | Considerations | Limit guidance |
|----------|---------------|----------------|
| Node.js | V8 heap + buffers; set `--max-old-space-size` | Limit = 1.5x `--max-old-space-size` |
| Python | No built-in memory cap | Monitor RSS, set limit with margin |
| Go | GC aware of cgroup memory limits (Go 1.19+) | `GOMEMLIMIT` = 90% of container limit |
| Java | Set `-Xmx` to ~75% of container limit | JVM reads cgroup limits since JDK 10 |
| Rust | No GC, predictable memory | Limit based on workload profiling |

### Node.js Memory Example

```dockerfile
ENV NODE_OPTIONS="--max-old-space-size=384"
# Container memory limit: 512M
# V8 heap limit: 384M (leaves ~128M for buffers, native code, overhead)
```

### Go Memory Example

```dockerfile
ENV GOMEMLIMIT=460MiB
# Container memory limit: 512M
# Go memory target: 460M (90% of limit)
```

## OOM Debugging

### Detect OOM Kills

```bash
# Check if container was OOM killed
docker inspect --format='{{.State.OOMKilled}}' container_name

# Watch for OOM events
docker events --filter event=oom

# Host-level OOM logs
dmesg | grep -i "oom\|killed"
journalctl -k | grep -i oom
```

### Common OOM Causes

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Memory leak | RSS grows linearly over time | Profile and fix the leak |
| Undersized limit | Peak usage exceeds limit | Increase limit or optimize |
| JVM heap too large | `-Xmx` exceeds container limit | Set `-Xmx` to 75% of limit |
| Unbounded caches | In-memory cache grows forever | Set max cache size, use LRU |
| Large file processing | Loading full file into memory | Stream processing |

## Monitoring Patterns

### Docker Stats

```bash
# Live resource usage
docker stats

# Single container, no streaming
docker stats --no-stream container_name
```

### Prometheus Metrics

Expose container metrics to Prometheus via cAdvisor:

```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports:
      - "8080:8080"
    profiles:
      - monitoring
```

### Key Metrics to Monitor

| Metric | Warning threshold | Critical threshold |
|--------|------------------|-------------------|
| Container memory usage | > 80% of limit | > 95% of limit |
| Container CPU usage | > 80% sustained | > 95% sustained |
| Container restart count | > 1 in 5 min | > 3 in 5 min |
| Disk usage (logs) | > 70% | > 90% |
| Container health status | Unhealthy | N/A |

### Docker Events for Alerting

```bash
# Stream events for monitoring
docker events --filter type=container \
  --filter event=die \
  --filter event=oom \
  --filter event=health_status \
  --format '{{.Time}} {{.Actor.Attributes.name}} {{.Action}}'
```
