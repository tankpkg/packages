# Observability and Debugging

Sources: Kubernetes official documentation (v1.32), Sander (Kubernetes Monitoring and Observability), Burns et al. (Kubernetes: Up and Running, 3rd ed.), Prometheus documentation, Grafana documentation, kubectl reference

Covers: kubectl debugging commands, pod troubleshooting flowcharts, events, log aggregation, Prometheus and Grafana setup, alerting, and common failure patterns with solutions.

## kubectl Debugging Cheat Sheet

### Pod Inspection

```bash
# List pods with status
kubectl get pods -n <ns> -o wide
kubectl get pods --all-namespaces --field-selector=status.phase!=Running

# Detailed pod info (events, conditions, container states)
kubectl describe pod <name> -n <ns>

# Logs
kubectl logs <pod> -n <ns>                    # current container
kubectl logs <pod> -c <container> -n <ns>     # specific container
kubectl logs <pod> --previous -n <ns>         # previous crashed container
kubectl logs <pod> -f -n <ns>                 # follow/stream
kubectl logs <pod> --since=1h -n <ns>         # last hour
kubectl logs <pod> --tail=100 -n <ns>         # last 100 lines
kubectl logs -l app=web -n <ns>               # all pods with label

# Execute into running container
kubectl exec -it <pod> -n <ns> -- /bin/sh
kubectl exec -it <pod> -c <container> -n <ns> -- /bin/bash

# Ephemeral debug container (distroless/minimal images)
kubectl debug -it <pod> --image=busybox:1.36 --target=<container>
kubectl debug -it <pod> --image=nicolaka/netshoot --target=<container>

# Copy files from/to pod
kubectl cp <pod>:/path/to/file ./local-file -n <ns>
kubectl cp ./local-file <pod>:/path/to/file -n <ns>
```

### Cluster and Node Inspection

```bash
# Cluster health
kubectl cluster-info
kubectl get nodes -o wide
kubectl top nodes                              # requires Metrics Server

# Node details and conditions
kubectl describe node <name>

# Resource usage
kubectl top pods -n <ns> --sort-by=memory
kubectl top pods -n <ns> --sort-by=cpu

# Events (sorted by time)
kubectl get events -n <ns> --sort-by=.metadata.creationTimestamp
kubectl get events --all-namespaces --field-selector=type=Warning

# API resources
kubectl api-resources                          # list all resource types
kubectl explain deployment.spec.strategy       # field documentation
```

### Resource Management

```bash
# Rollouts
kubectl rollout status deployment/<name> -n <ns>
kubectl rollout history deployment/<name> -n <ns>
kubectl rollout undo deployment/<name> -n <ns>
kubectl rollout restart deployment/<name> -n <ns>

# Scaling
kubectl scale deployment/<name> --replicas=5 -n <ns>

# Port forwarding
kubectl port-forward svc/<name> 8080:80 -n <ns>
kubectl port-forward pod/<name> 8080:8080 -n <ns>

# Dry run and diff
kubectl apply -f manifest.yaml --dry-run=server
kubectl diff -f manifest.yaml

# Force delete stuck pod
kubectl delete pod <name> --grace-period=0 --force -n <ns>
```

### Context and Namespace Management

```bash
# Switch context
kubectl config use-context <context-name>
kubectl config get-contexts

# Set default namespace
kubectl config set-context --current --namespace=production

# Or use kubens (from kubectx)
kubens production
```

## Pod Troubleshooting Flowchart

### Pod Status: Pending

| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| Insufficient CPU/memory | `kubectl describe pod` shows `Insufficient cpu` | Reduce requests, add nodes, or enable Cluster Autoscaler |
| No matching node (affinity/taint) | Events show `FailedScheduling` with affinity message | Fix nodeSelector/affinity or add tolerations |
| PVC not bound | Events show `persistentvolumeclaim not found` or `unbound` | Check StorageClass, PV availability |
| ResourceQuota exceeded | Events show `exceeded quota` | Increase quota or reduce resource requests |
| Too many pods on node | Events show `Too many pods` | Increase maxPods on node or add nodes |

### Pod Status: CrashLoopBackOff

| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| Application error | `kubectl logs <pod> --previous` shows exception/stack trace | Fix application code |
| OOM killed (exit code 137) | `describe pod` shows `OOMKilled` reason | Increase memory limit |
| Missing config/secret | Logs show `FileNotFoundError` or `env var not set` | Mount ConfigMap/Secret correctly |
| Liveness probe failing | Events show `Liveness probe failed` | Fix probe path/port/timing |
| Permission denied | Logs show permission errors | Fix SecurityContext (runAsUser, fsGroup) |
| Dependency unavailable | Logs show connection refused/timeout | Add init container to wait for dependency |

### Pod Status: ImagePullBackOff

| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| Image not found | Events show `manifest unknown` | Check image name and tag |
| Registry auth failed | Events show `unauthorized` | Create/fix imagePullSecrets |
| Rate limited | Events show `toomanyrequests` | Use private registry mirror |
| Network issue | Events show `timeout` | Check node network, DNS, firewall |

### Pod Status: Running but Not Working

| Symptom | Diagnostic | Fix |
|---------|-----------|-----|
| Not receiving traffic | `kubectl get endpoints <svc>` shows empty | Fix selector labels match between Service and Pod |
| Readiness probe failing | `describe pod` shows `Readiness probe failed` | Fix probe or application health endpoint |
| Wrong configuration | Exec into pod, check env/config files | Fix ConfigMap/Secret values |
| Internal error | Check application logs | Fix application code |

## Kubernetes Events

Events are cluster-level records of state changes. Invaluable for debugging.

```bash
# Namespace events
kubectl get events -n production --sort-by='.lastTimestamp'

# Warning events only
kubectl get events -n production --field-selector type=Warning

# Events for specific resource
kubectl get events -n production --field-selector involvedObject.name=web-abc123

# Watch events in real-time
kubectl get events -n production -w
```

### Important Event Types

| Event | Meaning | Action |
|-------|---------|--------|
| FailedScheduling | Cannot place pod on any node | Check resources, affinity, taints |
| FailedMount | Volume mount failed | Check PVC, Secret, ConfigMap |
| Unhealthy | Probe failed | Check probe config and app health |
| BackOff | Container restarting repeatedly | Check logs for crash reason |
| FailedCreate | Controller cannot create pod | Check ResourceQuota, RBAC |
| Killing | Container being terminated | Check OOM, preemption, eviction |
| NodeNotReady | Node unhealthy | Check node status and kubelet |
| EvictedByVPA | VPA evicted pod for resize | Expected if VPA mode is Auto |

## Prometheus and Grafana

### Prometheus Stack Installation

```bash
# Using Helm (kube-prometheus-stack)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring-values.yaml
```

This installs Prometheus, Grafana, Alertmanager, node-exporter, kube-state-metrics, and default dashboards.

### Key Metrics to Monitor

| Category | Metric | Alert Threshold |
|----------|--------|----------------|
| Pod health | `kube_pod_status_phase{phase="Failed"}` | > 0 for 5 minutes |
| Container restarts | `kube_pod_container_status_restarts_total` | Increase > 3 in 15 min |
| CPU utilization | `container_cpu_usage_seconds_total` | > 80% sustained |
| Memory utilization | `container_memory_working_set_bytes` | > 85% of limit |
| Node readiness | `kube_node_status_condition{condition="Ready"}` | != true |
| PVC usage | `kubelet_volume_stats_used_bytes / capacity` | > 85% |
| API server latency | `apiserver_request_duration_seconds` | P99 > 1s |
| HPA status | `kube_horizontalpodautoscaler_status_current_replicas` | == maxReplicas sustained |

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-metrics
  labels:
    release: monitoring       # must match Prometheus selector
spec:
  selector:
    matchLabels:
      app: web
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### PrometheusRule (Alerting)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: app-alerts
  labels:
    release: monitoring
spec:
  groups:
  - name: app.rules
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) /
        sum(rate(http_requests_total[5m])) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Error rate > 5% for {{ $labels.service }}"
```

## Log Aggregation

### Approaches

| Approach | Tool | Complexity |
|----------|------|------------|
| Node-level agent (DaemonSet) | Fluent Bit, Fluentd, Filebeat | Low-medium |
| Sidecar per pod | Fluent Bit sidecar | Medium |
| Application direct shipping | App sends to Loki/ES directly | Low |

### Fluent Bit DaemonSet (Lightweight)

Fluent Bit collects container logs from `/var/log/containers/` and ships to a backend (Loki, Elasticsearch, CloudWatch).

### Grafana Loki (Lightweight Alternative to Elasticsearch)

Loki indexes metadata (labels) not log content. Cheaper to run than Elasticsearch for Kubernetes logs.

```bash
helm install loki grafana/loki-stack \
  -n monitoring \
  --set grafana.enabled=false \
  --set promtail.enabled=true
```

Query logs in Grafana with LogQL:

```
{namespace="production", app="web"} |= "error" | json | status >= 500
```

## Debugging Network Issues

```bash
# DNS resolution
kubectl run dns-test --rm -it --image=busybox:1.36 -- nslookup <service>

# Connectivity test
kubectl run net-test --rm -it --image=nicolaka/netshoot -- \
  curl -v http://<service>:<port>

# Check network policies
kubectl get networkpolicy -n <ns>
kubectl describe networkpolicy <name> -n <ns>

# Check endpoints
kubectl get endpoints <service> -n <ns>

# Packet capture (netshoot)
kubectl debug -it <pod> --image=nicolaka/netshoot --target=<container> -- \
  tcpdump -i any -n port 8080
```

## Common Debugging Patterns

| Problem | Quick Check | Common Fix |
|---------|------------|------------|
| Pod evicted | `kubectl describe pod` shows `Evicted` | Increase node resources or reduce pod requests |
| Node disk pressure | `kubectl describe node` shows `DiskPressure` | Clean up images: `docker system prune` or expand disk |
| DNS not resolving | `nslookup` fails from debug pod | Check CoreDNS pods, network policies blocking UDP 53 |
| Service returns 503 | Endpoints list empty | Fix label selector mismatch between Service and Pod |
| PVC stuck Pending | `kubectl describe pvc` | Check StorageClass exists and provisioner is running |
| HPA not scaling | `kubectl describe hpa` shows `<unknown>` | Deploy Metrics Server or fix resource requests |
