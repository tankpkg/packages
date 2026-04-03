# Workloads and Controllers

Sources: Kubernetes official documentation (v1.32), Luksa (Kubernetes in Action, 2nd ed.), Ibryam/Huss (Kubernetes Patterns, 2nd ed.), Burns et al. (Kubernetes: Up and Running, 3rd ed.)

Covers: Pod anatomy, Deployment strategies, StatefulSets, DaemonSets, Jobs and CronJobs, ReplicaSets, init containers, sidecar pattern, pod lifecycle, and controller selection.

## Pod Anatomy

A Pod is the smallest deployable unit -- one or more containers sharing network namespace (localhost) and storage volumes.

### Pod Spec Essentials

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  labels:
    app: web
    version: v1
spec:
  serviceAccountName: app-sa    # never use default
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: myapp:1.2.3           # always use specific tags, never :latest
    ports:
    - containerPort: 8080
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        memory: 256Mi            # always limit memory
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30
      periodSeconds: 2
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 10
      failureThreshold: 3
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: db-host
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

### Pod Lifecycle Phases

| Phase | Description |
|-------|-------------|
| Pending | Accepted but not yet scheduled or pulling images |
| Running | At least one container running |
| Succeeded | All containers terminated with exit code 0 |
| Failed | At least one container terminated with non-zero exit code |
| Unknown | Cannot determine state (node communication failure) |

### Container States

| State | Meaning |
|-------|---------|
| Waiting | Not yet running (pulling image, waiting for init containers) |
| Running | Executing normally |
| Terminated | Finished execution (check exit code and reason) |

## Deployments

The primary controller for stateless applications. Manages ReplicaSets, which manage Pods.

### Deployment Spec

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: web
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1            # 1 extra pod during rollout
      maxUnavailable: 0       # zero-downtime: never drop below desired
  template:
    metadata:
      labels:
        app: web
    spec:
      # ... pod spec here
```

### Strategy Comparison

| Strategy | maxSurge | maxUnavailable | Behavior |
|----------|----------|----------------|----------|
| Zero-downtime | 1 | 0 | Never drops below replica count; slower rollout |
| Fast rollout | 25% | 25% | Default; trades some availability for speed |
| Recreate | N/A | N/A | Kills all old pods first, then creates new; causes downtime |

Use `maxUnavailable: 0` for production services that must maintain full capacity during updates.

### Rollout Commands

```bash
kubectl rollout status deployment/web          # watch progress
kubectl rollout history deployment/web         # view revisions
kubectl rollout undo deployment/web            # rollback to previous
kubectl rollout undo deployment/web --to-revision=3  # rollback to specific
kubectl rollout restart deployment/web         # trigger new rollout with same spec
kubectl rollout pause deployment/web           # pause mid-rollout
kubectl rollout resume deployment/web          # resume paused rollout
```

## StatefulSets

For workloads requiring stable network identities and persistent storage: databases, message queues, distributed systems.

### StatefulSet Guarantees

| Guarantee | Description |
|-----------|-------------|
| Stable pod names | `{name}-0`, `{name}-1`, `{name}-2` -- ordinal index, predictable |
| Stable DNS | `{pod}.{service}.{namespace}.svc.cluster.local` |
| Ordered deployment | Pods created 0, 1, 2 in sequence; waits for Ready before next |
| Ordered termination | Pods deleted in reverse order: 2, 1, 0 |
| Stable storage | Each pod gets its own PVC via `volumeClaimTemplates` |

### StatefulSet Spec

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres      # must match a headless Service
  replicas: 3
  podManagementPolicy: OrderedReady   # or Parallel for faster scaling
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0           # set >0 to canary specific ordinals
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

### When to Use StatefulSet vs Deployment

| Signal | Use |
|--------|-----|
| Each replica is identical and interchangeable | Deployment |
| Replicas need unique identity (primary/replica) | StatefulSet |
| Data must survive pod rescheduling | StatefulSet with PVC |
| Stateless application with external storage | Deployment |
| Ordered startup matters (leader election) | StatefulSet |

## DaemonSets

Run exactly one pod per node (or per matching node). Use for node-level agents.

### Common DaemonSet Use Cases

| Use Case | Example |
|----------|---------|
| Log collection | Fluentd, Fluent Bit, Filebeat |
| Metrics collection | Node Exporter, Datadog Agent |
| Network plugin | Calico, Cilium, kube-proxy |
| Storage driver | CSI node plugin |
| Security agent | Falco, Twistlock |

### DaemonSet Node Selection

```yaml
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/os: linux
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule       # run on control plane nodes too
```

Use `nodeSelector` or `nodeAffinity` to target specific node pools. Use `tolerations` to allow scheduling on tainted nodes.

## Jobs and CronJobs

### Job Spec

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  backoffLimit: 3              # retry up to 3 times on failure
  activeDeadlineSeconds: 600   # kill after 10 minutes
  ttlSecondsAfterFinished: 300 # clean up 5 min after completion
  template:
    spec:
      restartPolicy: Never     # or OnFailure
      containers:
      - name: migrate
        image: myapp:1.2.3
        command: ["./migrate", "--up"]
```

### Job Patterns

| Pattern | `completions` | `parallelism` | Use Case |
|---------|--------------|---------------|----------|
| Single run | 1 (default) | 1 (default) | Database migration |
| Fixed completion count | N | M | Process N items, M at a time |
| Work queue | unset | M | Process until queue empty |

### CronJob Spec

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"          # 2 AM daily
  concurrencyPolicy: Forbid       # skip if previous still running
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  startingDeadlineSeconds: 300     # skip if 5 min late
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: backup-tool:latest
```

### CronJob Concurrency Policies

| Policy | Behavior |
|--------|----------|
| Allow | Multiple jobs can run simultaneously (default) |
| Forbid | Skip new job if previous still running |
| Replace | Kill running job and start new one |

Use `Forbid` for most production workloads to prevent resource contention.

## Init Containers

Run sequentially before app containers start. Use for setup tasks that must complete first.

```yaml
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 2; done']
  - name: run-migrations
    image: myapp:1.2.3
    command: ['./migrate', '--up']
  containers:
  - name: app
    image: myapp:1.2.3
```

### Init Container Use Cases

| Use Case | Example |
|----------|---------|
| Wait for dependency | Check database/cache connectivity |
| Run migrations | Schema changes before app starts |
| Download config | Fetch config from Vault or S3 |
| Set permissions | `chmod`/`chown` on mounted volumes |

Init containers share volumes with app containers. Write files in init, read in app.

## Sidecar Pattern

A helper container running alongside the main application container in the same pod.

### Native Sidecar Containers (v1.29+)

```yaml
spec:
  initContainers:
  - name: log-shipper
    image: fluent-bit:3.0
    restartPolicy: Always        # this makes it a sidecar (runs for pod lifetime)
  containers:
  - name: app
    image: myapp:1.2.3
```

Setting `restartPolicy: Always` on an init container makes it a native sidecar. It starts before app containers and runs for the pod's lifetime.

### Common Sidecar Patterns

| Pattern | Sidecar Role | Example |
|---------|-------------|---------|
| Log shipping | Collect and forward logs | Fluent Bit, Filebeat |
| Proxy | Handle network concerns | Envoy, Istio proxy |
| Config reloader | Watch for config changes | Reloader, configmap-reload |
| Auth proxy | Add authentication | OAuth2 Proxy |

## Label and Selector Best Practices

### Recommended Labels

| Label | Example | Purpose |
|-------|---------|---------|
| `app.kubernetes.io/name` | `postgres` | Application name |
| `app.kubernetes.io/instance` | `postgres-orders` | Instance identifier |
| `app.kubernetes.io/version` | `16.1` | Current version |
| `app.kubernetes.io/component` | `database` | Component role |
| `app.kubernetes.io/part-of` | `order-system` | Higher-level application |
| `app.kubernetes.io/managed-by` | `helm` | Tool managing the resource |

Use consistent labels across all resources. Selectors depend on them for Services, Deployments, NetworkPolicies, and monitoring.
