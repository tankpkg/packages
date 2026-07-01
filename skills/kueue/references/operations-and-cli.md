# Operations, CLI, and Observability

Sources: Kueue documentation (kueue.sigs.k8s.io/docs/reference/kueuectl/, /metrics/, /tasks/manage/observability/, /tasks/troubleshooting/), kubernetes-sigs/kueue source (cmd/kueuectl, pkg/metrics).

Covers: full kueuectl command surface, Workload status interpretation (every condition + reason), ClusterQueue status fields, Prometheus metrics catalog with PromQL recipes, log diagnostics, troubleshooting trees for stuck/evicted/never-admitted workloads, performance tuning, drain/migrate/quota-update procedures.

## kueuectl CLI

### Install

```bash
# Via krew (recommended)
kubectl krew install kueue
kubectl kueue version

# Or download release binary directly
VERSION=v0.14.0
curl -L https://github.com/kubernetes-sigs/kueue/releases/download/${VERSION}/kueuectl-linux-amd64 -o kueuectl
chmod +x kueuectl && sudo mv kueuectl /usr/local/bin/
```

All kueuectl commands accept the standard kubectl global flags (`--kubeconfig`, `-n`, `-A`, `--context`, `--as`, `--request-timeout`).

### Command surface

| Verb | Resource | Use |
|------|----------|-----|
| `version` | — | Print client + controller image versions |
| `create` | `clusterqueue`, `localqueue`, `resourceflavor` | Bootstrap quota objects from CLI flags |
| `list` | `workload`, `clusterqueue`, `localqueue`, `resourceflavor`, `pods` | List with filters |
| `get` | (any) | Retrieve a single object as YAML/JSON |
| `describe` | `clusterqueue`, `localqueue`, `workload` | Human-readable status with computed fields |
| `stop` | `workload`, `clusterqueue`, `localqueue` | Hold or HoldAndDrain |
| `resume` | (same) | Reverse a stop |
| `delete` | (any) | Delete (CQ must be empty first) |
| `edit` / `patch` | (any) | In-place modification |

### Common invocations

```bash
# Create a ClusterQueue with cohort + quota in one shot
kueuectl create clusterqueue team-a-cq \
  --cohort=shared --queueing-strategy=BestEffortFIFO \
  --namespace-selector=matchLabels=team=team-a \
  --reclaim-within-cohort=LowerPriority \
  --preemption-within-cluster-queue=LowerPriority \
  --nominal-quota=cpu:100,memory:400Gi,nvidia.com/gpu:8 \
  --borrowing-limit=cpu:50,memory:200Gi,nvidia.com/gpu:4

# LocalQueue + ResourceFlavor
kueuectl create localqueue default --clusterqueue=team-a-cq -n team-a
kueuectl create resourceflavor gpu-a100 --node-labels=accelerator=nvidia-a100

# List workloads with status filter
kueuectl list workload -A --status=pending
kueuectl list workload --clusterqueue=team-a-cq --status=admitted
kueuectl list workload -n team-a -o wide

# Pods owned by a specific Job through the Workload
kueuectl list pods --for=job/training-1 -n team-a

# Describe (the most useful diagnostic command)
kueuectl describe clusterqueue team-a-cq
kueuectl describe workload <wl-name> -n team-a

# Stop / drain
kueuectl stop workload <wl> -n team-a                       # cancel reservation, evict
kueuectl stop clusterqueue team-a-cq --stop-policy=Hold    # no new admissions
kueuectl stop clusterqueue team-a-cq --stop-policy=HoldAndDrain
kueuectl resume clusterqueue team-a-cq

# Delete
kueuectl delete workload <wl> -n team-a
```

### Sample `describe clusterqueue` output

```
Name:                  team-a-cq
Status:                Active
Cohort:                shared
Pending Workloads:     3                       # in queue, not yet QuotaReserved
Reserving Workloads:   2                       # QuotaReserved=True, Admitted=False
Admitted Workloads:    5                       # actively running
Flavors Reservation:
  gpu-a100:
    cpu:               20/100 (5 borrowed)
    memory:            80Gi/400Gi
    nvidia.com/gpu:    4/8
  cpu:
    cpu:               50/100
    memory:            200Gi/400Gi
Fair Sharing Weight:   1.0   weighted-share=0.25
```

Use `kubectl get clusterqueue <name> -o yaml` to see the raw `.status.flavorsUsage`, `.status.flavorsReservation`, and `.status.fairSharing.weightedShare` underlying these aggregates.

## Workload Status Reference

`Workload.status.conditions[]` is the source of truth. Each condition has `type`, `status`, `reason`, `message`, `lastTransitionTime`.

| Condition `type` | When True | Common reasons |
|-----------------|-----------|----------------|
| `QuotaReserved` | Quota reserved in a CQ; flavor assignment in `status.admission` | `QuotaReserved` |
| `Admitted` | Quota reserved AND all admission checks Ready; Job is unsuspended | `Admitted` |
| `PodsReady` | All Pods reached Ready (only set if `waitForPodsReady` enabled) | `Started`, `PodsReady` |
| `Finished` | Underlying Job reached terminal state | `Succeeded`, `Failed` |
| `Evicted` | Workload removed from admission | `Preempted`, `PodsReadyTimeout`, `AdmissionCheck`, `ClusterQueueStopped`, `LocalQueueStopped`, `Deactivated`, `NodeFailures` |
| `Preempted` | (when Evicted=True with reason Preempted) | `InClusterQueue`, `InCohortReclamation`, `FairSharing` |
| `Inadmissible` | Workload tried but couldn't fit | `NoFit`, `FlavorNotFound`, `Preempted` |

Other status fields:

```yaml
status:
  admission:                                # present only while QuotaReserved=True
    clusterQueue: team-a-cq
    podSetAssignments:
    - name: main
      flavors:
        cpu: gpu-a100
        memory: gpu-a100
        nvidia.com/gpu: gpu-a100
      resourceUsage: { cpu: "4", memory: "16Gi", "nvidia.com/gpu": "1" }
      topologyAssignment:                   # only with TAS
        levels: [block, rack, hostname]
        domains: [{ values: [block-A, rack-1, gpu-001] }]
  admissionChecks:
  - name: provisioning-request
    state: Ready                            # Pending | Ready | Retry | Rejected
    podSetUpdates: [...]
  requeueState:                             # for backoff after eviction
    count: 2
    requeueAt: "2026-05-07T12:00:00Z"
  accumulatedPastExecutionTimeSeconds: 3600
```

### Common status patterns

| What you see | What it means | First diagnostic |
|-------------|--------------|------------------|
| Both `QuotaReserved=False, Admitted=False` | In queue, no quota | `kueuectl describe cq` to see if quota is full |
| `QuotaReserved=True, Admitted=False` | Quota OK, AdmissionCheck pending | Check `status.admissionChecks[].state` |
| `Admitted=True, PodsReady=False` (after timeout) | Pods can't all start | Check Pod events; flavor's nodeSelector might exclude available nodes |
| `Inadmissible=True, reason=NoFit` | No flavor combination fits | Verify Pod requests against ClusterQueue capacity per flavor |
| `Evicted=True, reason=Preempted` | Higher-priority Workload took resources | Check who preempted in events |
| `Evicted=True, reason=PodsReadyTimeout` | Gang scheduling failed within timeout | Increase `waitForPodsReady.timeout` or fix Pod startup |
| `Evicted=True, reason=Deactivated` | `spec.active` was set to false (admin or rejected check) | Re-activate or fix the rejection |

## ClusterQueue Status Reference

```yaml
status:
  conditions:
  - type: Active                            # only condition; True if scheduling enabled
    status: "True"
    reason: Ready                           # or FlavorNotFound, ResourceGroupNotFound, Stopped
  pendingWorkloads: 8                       # waiting in queue
  reservingWorkloads: 2                     # QuotaReserved=True, not yet Admitted
  admittedWorkloads: 12                     # actively running
  flavorsReservation:                       # quota reserved by admitted workloads
  - name: gpu-a100
    resources:
    - { name: cpu,            total: "20", borrowed: "5" }
    - { name: "nvidia.com/gpu", total: "4", borrowed: "0" }
  flavorsUsage:                             # actual Pod usage (≤ reservation)
  - name: gpu-a100
    resources:
    - { name: cpu, total: "18" }            # 18 < 20 reserved
  fairSharing:
    weightedShare: 0.25                     # for cohort fair sharing
```

`flavorsReservation - nominalQuota` = currently borrowed amount. `flavorsUsage` lags reservation when Pods are starting up.

## Prometheus Metrics

Endpoint: `kueue-controller-manager-metrics-service:8443/metrics` (TLS). Helm chart with `enablePrometheus: true` creates a ServiceMonitor; otherwise apply `prometheus.yaml` from the release.

### Health metrics

| Metric | Type | Labels | Notes |
|--------|------|--------|-------|
| `kueue_admission_attempts_total` | Counter | `result` (success/inadmissible) | Each scheduling attempt |
| `kueue_admission_attempt_duration_seconds` | Histogram | `result` | Single-cycle scheduler latency |
| `kueue_build_info` | Gauge | `git_version`, `git_commit`, `build_date`, `go_version` | Always 1; metadata |

### Workload counters per ClusterQueue

| Metric | Type | Labels |
|--------|------|--------|
| `kueue_pending_workloads` | Gauge | `cluster_queue`, `status` (active/inadmissible) |
| `kueue_reserving_active_workloads` | Gauge | `cluster_queue` |
| `kueue_admitted_active_workloads` | Gauge | `cluster_queue` |
| `kueue_quota_reserved_workloads_total` | Counter | `cluster_queue`, `priority_class` |
| `kueue_admitted_workloads_total` | Counter | `cluster_queue`, `priority_class` |
| `kueue_finished_workloads_total` | Counter | `cluster_queue`, `priority_class` |
| `kueue_evicted_workloads_total` | Counter | `cluster_queue`, `reason`, `underlying_cause`, `priority_class` |
| `kueue_cluster_queue_status` | Gauge | `cluster_queue`, `status` |

### Latency histograms

| Metric | What it measures |
|--------|------------------|
| `kueue_quota_reserved_wait_time_seconds` | Workload creation → QuotaReserved |
| `kueue_admission_wait_time_seconds` | Workload creation → Admitted (covers checks too) |
| `kueue_admission_checks_wait_time_seconds` | QuotaReserved → Admitted (just the checks) |

### Quota gauges (require `metrics.enableClusterQueueResources: true`)

| Metric | Labels |
|--------|--------|
| `kueue_cluster_queue_nominal_quota` | `cluster_queue`, `flavor`, `resource` |
| `kueue_cluster_queue_resource_reservation` | (same) |
| `kueue_cluster_queue_resource_usage` | (same) |
| `kueue_cluster_queue_borrowing_limit` | (same) |
| `kueue_cluster_queue_lending_limit` | (same) |

### Cohort metrics

| Metric | Labels |
|--------|--------|
| `kueue_cohort_weighted_share` | `cohort` |
| `kueue_cohort_subtree_quota` | `cohort`, `flavor`, `resource` |
| `kueue_cohort_subtree_resource_reservations` | (same) |

### LocalQueue metrics (alpha — `LocalQueueMetrics` feature gate)

Same shape as ClusterQueue metrics but with `name` + `namespace` labels and prefix `kueue_local_queue_*`. High cardinality; enable selectively.

## PromQL recipes

```promql
# Pending workloads per CQ (most useful single-pane chart)
sum by (cluster_queue) (kueue_pending_workloads{status="active"})

# Quota utilization per (cq, flavor, resource), 0..1
sum by (cluster_queue, flavor, resource) (kueue_cluster_queue_resource_usage)
/
sum by (cluster_queue, flavor, resource) (kueue_cluster_queue_nominal_quota)

# Admission p50/p95/p99
histogram_quantile(0.50, sum by (le, cluster_queue) (rate(kueue_admission_wait_time_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le, cluster_queue) (rate(kueue_admission_wait_time_seconds_bucket[5m])))

# Eviction rate by reason
sum by (reason) (rate(kueue_evicted_workloads_total[5m]))

# Weighted share per CQ in a cohort (alarm when one CQ dominates)
kueue_cluster_queue_weighted_share

# Borrowing pressure: amount borrowed / nominal
sum by (cluster_queue, flavor, resource) (
  max(0, kueue_cluster_queue_resource_reservation - kueue_cluster_queue_nominal_quota)
) / sum by (cluster_queue, flavor, resource) (kueue_cluster_queue_nominal_quota)
```

### Suggested Grafana panels

| Panel | Query template | Use |
|-------|----------------|-----|
| Pending workloads (line per CQ) | `sum by (cluster_queue) (kueue_pending_workloads{status="active"})` | Spot queue buildup |
| Quota utilization stacked area | `sum by (flavor) (kueue_cluster_queue_resource_usage{cluster_queue="$cq"})` | Per-CQ saturation |
| Eviction rate pie | `sum by (reason) (rate(kueue_evicted_workloads_total[5m]))` | Why are workloads dying? |
| Admission latency p99 stat | `histogram_quantile(0.99, rate(kueue_admission_wait_time_seconds_bucket[5m]))` | Scheduler health |
| Cohort weighted share gauge | `kueue_cluster_queue_weighted_share` | Fair sharing fairness |

## Logs and Events

```bash
# Tail controller logs
kubectl -n kueue-system logs deploy/kueue-controller-manager -f

# Increase verbosity (edit ConfigMap then rollout restart)
# Set in Configuration:
#   logLevel: 4              # 0=info, 1=debug, 2=trace, 4=very verbose
# Or pass --zap-log-level=debug as a container arg

# Workload events (one of the most useful debug surfaces)
kubectl describe workload <wl> -n <ns>
```

| Log line | Means |
|----------|-------|
| `Workload admitted to ClusterQueue X` | QuotaReserved + all checks Ready, Job unsuspended |
| `Workload evicted: Preempted` | A higher-priority Workload took resources |
| `Could not update Workload status` | Optimistic concurrency conflict; reconciler retries |
| `Flavor not found` | A ClusterQueue references a ResourceFlavor that doesn't exist |
| `Admission check Pending → Retry` | External check (ProvisioningRequest, MultiKueue) failed transiently |
| `couldn't suspend Job` | Webhook race or RBAC denied; check webhook health |

## Troubleshooting Trees

### "Workload stuck Pending"

1. `kueuectl describe workload <wl>` — check the conditions
2. If `QuotaReserved=False`:
   - `kueuectl describe cq <cq>` — is `pendingWorkloads` blocking?
   - Look at `flavorsReservation` vs `nominalQuota` — full?
   - Workload Pod request fits any flavor? Check `flavors` block under each `resourceGroup`
   - Is `namespaceSelector` excluding the Workload's namespace?
3. If `Inadmissible=True, reason=NoFit`:
   - The Workload's nodeSelector or topology constraints can't be satisfied by any flavor
   - `kubectl get nodes --show-labels` to verify nodes have the labels referenced by ResourceFlavor
4. If `QuotaReserved=True, Admitted=False`:
   - `status.admissionChecks[]` will show which check is `Pending`
   - For ProvisioningRequest: `kubectl get provisioningrequest -n <ns> -o wide`
   - For MultiKueue: `kubectl logs -n kueue-system deploy/kueue-controller-manager | grep multikueue`

### "Workload was admitted but evicted"

```bash
kueuectl describe workload <wl>             # find Evicted reason
kubectl get events -n <ns> --field-selector involvedObject.name=<wl>
```

| Reason | Meaning | Fix |
|--------|---------|-----|
| `Preempted` | Higher-priority Workload pushed it out | Raise priority, increase quota, change preemption policy |
| `PodsReadyTimeout` | Gang scheduling didn't complete in `waitForPodsReady.timeout` | Increase timeout; ensure cluster has capacity |
| `AdmissionCheck` | A check entered Retry state after admission | Check the relevant check controller's logs |
| `ClusterQueueStopped` / `LocalQueueStopped` | Operator put queue in Hold | `kueuectl resume cq <name>` |
| `Deactivated` | `spec.active=false` (admin or hard rejection) | Investigate why; may need new submission |
| `NodeFailures` (TAS) | Nodes the workload was pinned to failed | Check node health |

### "Cluster Autoscaler not scaling for queued GPU workloads"

The autoscaler doesn't see Pods (they're suspended). It only reacts to `ProvisioningRequest`.

```bash
# Are ProvisioningRequest objects being created?
kubectl get provisioningrequest -A

# Is the AdmissionCheck wired into the CQ?
kubectl get clusterqueue <gpu-cq> -o yaml | grep -A2 admissionChecks

# Check autoscaler logs for ProvisioningRequest entries
kubectl -n kube-system logs deploy/cluster-autoscaler | grep ProvisioningRequest
```

### "MultiKueue worker won't connect"

```bash
# Does the secret exist on the manager?
kubectl -n kueue-system get secret <worker>-kubeconfig

# Can the manager actually reach the worker API server with that kubeconfig?
KUBECONFIG=<(kubectl -n kueue-system get secret <worker>-kubeconfig -o jsonpath='{.data.kubeconfig}' | base64 -d) \
  kubectl cluster-info

# Manager logs
kubectl -n kueue-system logs deploy/kueue-controller-manager | grep -i multikueue
```

## Operational Procedures

### Drain a ClusterQueue for maintenance

```bash
kueuectl stop clusterqueue <cq> --stop-policy=Hold        # let running finish
# wait until kueuectl describe cq shows admittedWorkloads: 0
# perform maintenance
kueuectl resume clusterqueue <cq>
```

For an emergency hard drain: `--stop-policy=HoldAndDrain` evicts admitted Workloads immediately. Pending Workloads either re-admit elsewhere if a sibling CQ has capacity, or stay pending.

### Migrate Workloads to a different ClusterQueue

```bash
# 1. Create a new LocalQueue pointing at the new CQ
kueuectl create localqueue migrate-target --clusterqueue=new-cq -n <ns>

# 2. For each Workload, patch the LocalQueue reference (only works while Pending)
kubectl label workload <wl> -n <ns> kueue.x-k8s.io/queue-name=migrate-target --overwrite
```

Note: admitted Workloads can't be moved without being evicted first.

### Update quota safely

ClusterQueue `nominalQuota`, `borrowingLimit`, and `lendingLimit` are mutable. Increases are immediately visible to the scheduler — additional pending Workloads will admit on the next cycle. Decreases don't evict already-admitted Workloads; they just prevent further admission until usage drops.

```bash
kubectl patch clusterqueue team-a-cq --type=merge -p \
  '{"spec":{"resourceGroups":[{"flavors":[{"name":"gpu-a100","resources":[{"name":"nvidia.com/gpu","nominalQuota":"16"}]}]}]}}'
```

### Backup / restore

The CRDs are reconcilable from source-of-truth Job objects, but Workload status (admission state, requeue counters) is not. Backup with:

```bash
kubectl get -A workload,clusterqueue,localqueue,resourceflavor,cohort,admissioncheck,workloadpriorityclass -o yaml > kueue-backup.yaml
```

On restart, the controller rebuilds quota state from the admitted Workloads it finds — so as long as Workloads are persisted, no quota is lost.

## Performance Tuning

| Knob | Where | Effect |
|------|-------|--------|
| `clientConnection.qps` / `burst` | Configuration | API server rate limit; raise for >1k Workloads |
| `controller.groupKindConcurrency.Workload.kueue.x-k8s.io` | Configuration | Parallel reconcile workers |
| `webhook.timeoutSeconds` | Configuration | Webhook request budget; raise on slow API servers |
| `metrics.enableClusterQueueResources` | Configuration | Adds gauges; small CPU cost |
| `LocalQueueMetrics` feature gate | Configuration | High cardinality; enable selectively |

### Scaling limits

A single kueue-controller-manager comfortably handles ~10k active Workloads. Hard limits in current design:

- 256 flavors per ClusterQueue
- 16 resource groups per ClusterQueue
- 8 PodSets per Workload (so 1 head + 7 RayCluster worker groups, etc.)
- 64 resources per flavor

There is no built-in sharding — for clusters that exceed these limits, run multiple Kueue controllers each managing a subset of ClusterQueues (currently requires custom kustomization).

## Sources

- https://kueue.sigs.k8s.io/docs/reference/kueuectl/
- https://kueue.sigs.k8s.io/docs/reference/metrics/
- https://kueue.sigs.k8s.io/docs/tasks/manage/observability/setup_prometheus/
- https://kueue.sigs.k8s.io/docs/tasks/manage/observability/common_grafana_queries/
- https://kueue.sigs.k8s.io/docs/tasks/troubleshooting/
- https://kueue.sigs.k8s.io/docs/tasks/troubleshooting/troubleshooting_jobs/
- https://kueue.sigs.k8s.io/docs/tasks/troubleshooting/troubleshooting_queues/
- https://github.com/kubernetes-sigs/kueue/tree/main/cmd/kueuectl
- https://github.com/kubernetes-sigs/kueue/tree/main/pkg/metrics
