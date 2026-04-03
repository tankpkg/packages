# Autoscaling and Resources

Sources: Kubernetes official documentation (v1.32), Rosso et al. (Production Kubernetes), Kubernetes Autoscaler GitHub repository, Karpenter documentation (v1.1), VPA documentation, Kubecost documentation

Covers: Resource requests and limits, QoS classes, LimitRanges, ResourceQuotas, HPA (v1/v2), VPA, Cluster Autoscaler, Karpenter, right-sizing strategies, and cost optimization.

## Resource Requests and Limits

Every container should declare resource requests. Memory limits are critical. CPU limits are debatable.

### Requests vs Limits

| Dimension | Requests | Limits |
|-----------|----------|--------|
| Purpose | Scheduler guarantee (reserved capacity) | Maximum allowed consumption |
| CPU behavior | Guaranteed CPU shares | Throttling above limit (CFS quota) |
| Memory behavior | Guaranteed memory | OOM killed above limit |
| Scheduling | Used to find a node with capacity | Not used for scheduling |
| Default if omitted | 0 (best-effort) | Unlimited |

### Setting Values

```yaml
resources:
  requests:
    cpu: 100m          # 0.1 CPU core (100 millicores)
    memory: 128Mi      # 128 MiB
  limits:
    memory: 256Mi      # always set memory limit
    # cpu: omitted     # consider omitting for latency-sensitive apps
```

### CPU Units

| Value | Meaning |
|-------|---------|
| 1 | 1 vCPU / 1 core |
| 500m | 0.5 CPU (500 millicores) |
| 100m | 0.1 CPU (100 millicores) |
| 250m | 0.25 CPU |

### Memory Units

| Value | Meaning |
|-------|---------|
| 128Mi | 128 mebibytes (binary, 128 * 1024^2 bytes) |
| 1Gi | 1 gibibyte |
| 256M | 256 megabytes (decimal, 256 * 10^6 bytes) |

Use Mi/Gi (binary) for consistency with how the kernel reports memory.

### The CPU Limits Debate

| Position | Argument |
|----------|----------|
| Set CPU limits | Prevents noisy neighbor; predictable latency in multi-tenant |
| Omit CPU limits | Avoids throttling; pods burst into unused capacity; lower tail latency |
| Compromise | Set limits = 2-5x requests for headroom without unlimited burst |

CPU throttling occurs when a container exceeds its CFS quota within a scheduling period (100ms). Throttled containers experience increased latency, slow responses, and false liveness probe failures.

Recommendation: omit CPU limits for latency-sensitive workloads. Set them for batch jobs and multi-tenant clusters where fairness matters.

## Quality of Service Classes

Kubernetes assigns QoS classes based on resource declarations. QoS determines eviction priority under node pressure.

| QoS Class | Condition | Eviction Priority |
|-----------|-----------|-------------------|
| Guaranteed | requests == limits for all containers (CPU and memory) | Last (highest priority) |
| Burstable | At least one request or limit set, but not equal | Middle |
| BestEffort | No requests or limits set | First (lowest priority) |

### QoS Selection Guide

| Workload | Recommended QoS | How |
|----------|-----------------|-----|
| Critical production service | Guaranteed | Set requests == limits |
| General application | Burstable | Set requests < limits |
| Development/testing | Burstable or BestEffort | Requests only |
| Batch processing | Burstable | Low requests, moderate limits |

## LimitRanges

Enforce per-pod and per-container resource constraints within a namespace.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - type: Container
    default:                   # applied if container has no limits
      cpu: 500m
      memory: 256Mi
    defaultRequest:            # applied if container has no requests
      cpu: 100m
      memory: 128Mi
    min:
      cpu: 50m
      memory: 64Mi
    max:
      cpu: 2
      memory: 2Gi
  - type: Pod
    max:
      cpu: 4
      memory: 4Gi
```

LimitRanges inject defaults at admission time. Pods without resource declarations get the `defaultRequest` and `default` limit values.

## ResourceQuotas

Enforce aggregate resource consumption limits per namespace.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "100"
    services: "20"
    persistentvolumeclaims: "30"
    configmaps: "50"
    secrets: "50"
```

When a ResourceQuota is active, every pod must declare resource requests and limits (or have them injected by a LimitRange).

## Horizontal Pod Autoscaler (HPA)

Scales the number of pod replicas based on observed metrics.

### HPA v2 (Current)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 20
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300      # 5 min cooldown
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### HPA Metric Types

| Type | Source | Example |
|------|--------|---------|
| Resource | CPU/memory utilization | `averageUtilization: 70` |
| Pods | Custom per-pod metric | `requests_per_second` from Prometheus |
| Object | Metric on another K8s object | Ingress `requests-per-second` |
| External | Metric from outside cluster | SQS queue depth, Pub/Sub backlog |

### Custom Metrics with Prometheus Adapter

```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: 100
```

Requires Prometheus Adapter or KEDA to expose custom metrics via the metrics API.

### HPA Prerequisites

1. Metrics Server deployed (`kubectl top pods` must work)
2. Resource requests set on target containers (HPA compares current vs requested)
3. For custom metrics: Prometheus Adapter or KEDA installed

### HPA Debugging

```bash
kubectl get hpa web-hpa
kubectl describe hpa web-hpa           # check conditions, events
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/pods" | jq  # check metrics API
```

## KEDA (Kubernetes Event-Driven Autoscaling)

Extends HPA with 60+ event sources. Scales to/from zero.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker
spec:
  scaleTargetRef:
    name: worker-deployment
  minReplicaCount: 0               # scale to zero
  maxReplicaCount: 50
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123456/my-queue
      queueLength: "5"             # 1 replica per 5 messages
      awsRegion: us-east-1
```

KEDA is preferred over raw Prometheus Adapter for event-driven scaling (queues, streams, cron).

## Vertical Pod Autoscaler (VPA)

Adjusts CPU and memory requests based on historical usage. Does NOT change replica count.

### VPA Modes

| Mode | Behavior |
|------|----------|
| Off | Recommendations only (view via `kubectl describe vpa`) |
| Initial | Sets resources on pod creation; no live updates |
| Auto | Evicts and recreates pods with new resource values |

### VPA Spec

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  updatePolicy:
    updateMode: "Off"            # start with Off, graduate to Auto
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: 50m
        memory: 64Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
```

### VPA + HPA Interaction

Do not use VPA (Auto mode) and HPA on the same CPU/memory metric simultaneously -- they conflict. Safe combinations:

| HPA Metric | VPA Controls | Conflict? |
|-----------|-------------|-----------|
| CPU utilization | CPU + memory | Yes (conflict) |
| Custom metric (RPS) | CPU + memory | No (safe) |
| Memory utilization | CPU only | No (safe) |

Use VPA in `Off` mode alongside HPA to get recommendations without automatic changes.

## Cluster Autoscaler

Scales the number of nodes based on pending pods that cannot be scheduled.

### How It Works

1. Pod is pending (insufficient node resources)
2. Cluster Autoscaler detects pending pods
3. Simulates scheduling to find which node group to expand
4. Adds nodes to the node group
5. Scale-down: removes underutilized nodes (< 50% utilization for 10+ minutes)

### Key Configuration

| Parameter | Default | Recommendation |
|-----------|---------|---------------|
| scale-down-unneeded-time | 10m | 10-15m for production |
| scale-down-utilization-threshold | 0.5 | 0.5-0.65 |
| max-graceful-termination-sec | 600 | Match your longest pod shutdown |
| expander | random | priority (for mixed instance types) |

## Karpenter (Node Autoscaler)

Karpenter (now CNCF project) is a next-generation node autoscaler. Faster than Cluster Autoscaler, provisions nodes directly via cloud API.

### Karpenter vs Cluster Autoscaler

| Feature | Cluster Autoscaler | Karpenter |
|---------|-------------------|-----------|
| Provisioning speed | Minutes (via ASG) | Seconds (direct API) |
| Instance selection | Fixed node groups | Dynamic best-fit |
| Consolidation | Remove underutilized nodes | Bin-pack and replace |
| Multi-arch | Manual node groups | Automatic |
| Cloud support | All major clouds | AWS GA, Azure preview |

## Right-Sizing Strategy

1. Deploy with generous requests (overprovisioned)
2. Enable VPA in `Off` mode for recommendations
3. Monitor actual usage with Prometheus for 2+ weeks
4. Set requests to P95 of actual usage + 20% buffer
5. Set memory limits to 1.5-2x requests
6. Review monthly and adjust
