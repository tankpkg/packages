# Kueue Concepts and Architecture

Sources: Kueue official documentation (kueue.sigs.k8s.io/docs/concepts/), kubernetes-sigs/kueue API types (apis/kueue/v1beta1, apis/kueue/v1), Kueue v0.14+ release notes.

Covers: Kueue's positioning as a job-queueing layer above kube-scheduler, the eight core CRDs and their key fields, the suspend → quota → admission-check → admit lifecycle, controller architecture, and the resource/quota/borrowing model.

## What Kueue Is

Kueue is a Kubernetes-native job queueing controller for batch, AI/ML, and HPC workloads. It sits *above* the standard `kube-scheduler` and decides *when* a Job is allowed to start; it never schedules Pods to nodes itself. Once Kueue admits a Workload, it unsuspends the underlying Job and `kube-scheduler` places its Pods normally.

| Layer | Responsibility |
|-------|----------------|
| User submits Job with `kueue.x-k8s.io/queue-name` label | LocalQueue routing |
| Kueue mutating webhook | Sets `spec.suspend: true` on the Job |
| Kueue Job reconciler | Creates a Workload object representing the queued unit |
| Kueue Workload reconciler / scheduler | Reserves quota, runs admission checks, assigns flavors |
| Kueue Job reconciler | Patches `spec.suspend: false` after admission |
| `kube-scheduler` | Binds Pods to nodes using the assigned flavor's nodeLabels/tolerations |

## Positioning vs Other Schedulers

| System | Role | Relationship to Kueue |
|--------|------|----------------------|
| `kube-scheduler` | Pod-to-node binding | Kueue runs above it; both required |
| Volcano | Custom scheduler with gang scheduling, batch features | Alternative — replaces kube-scheduler |
| YuniKorn | Standalone scheduler with hierarchical queues | Alternative — replaces kube-scheduler |
| Cluster Autoscaler / Karpenter | Node provisioning | Kueue triggers provisioning via `ProvisioningRequest` AdmissionCheck |

Kueue's design choice: stay native, do not replace `kube-scheduler`. This means existing workloads keep working and only opt-in via the queue-name label.

## The Eight Core CRDs

All CRDs live under `kueue.x-k8s.io`. The current stable API group is `v1beta1`; `v1` is being introduced incrementally.

### 1. ResourceFlavor

A `(nodeLabels, nodeTaints, tolerations)` tuple — Kueue's name for "this class of hardware". Quotas are denominated per-flavor.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: gpu-a100
spec:
  nodeLabels:
    accelerator: nvidia-a100
  nodeTaints:
  - key: nvidia.com/gpu
    value: "true"
    effect: NoSchedule
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  topologyName: gpu-rack-topology   # optional, for TAS
```

Up to 8 nodeLabels and 8 tolerations per flavor. Taints must be `NoSchedule` or `NoExecute` (never `PreferNoSchedule`). When Kueue assigns this flavor to a Workload, it injects the tolerations into the Pod spec at unsuspend time so Pods can land on tainted nodes.

### 2. ClusterQueue

Cluster-wide quota pool. Defines how much of each `(flavor, resource)` pair is available, who can submit (`namespaceSelector`), what queueing strategy applies, and the preemption policy.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: team-a-cq
spec:
  cohort: shared-pool                      # join a cohort for borrowing
  namespaceSelector:                       # restrict who can use this CQ
    matchLabels: { team: team-a }
  queueingStrategy: BestEffortFIFO         # or StrictFIFO
  resourceGroups:
  - coveredResources: [cpu, memory, "nvidia.com/gpu"]
    flavors:
    - name: gpu-a100
      resources:
      - name: cpu
        nominalQuota: "100"
        borrowingLimit: "50"               # may borrow up to 50 more from cohort
        lendingLimit:   "80"               # may lend up to 80 to cohort
      - name: memory
        nominalQuota: "400Gi"
      - name: "nvidia.com/gpu"
        nominalQuota: "8"
  flavorFungibility:
    whenCanBorrow: TryNextFlavor           # try cheaper flavor before borrowing
    whenCanPreempt: TryNextFlavor
  preemption:
    reclaimWithinCohort: LowerPriority
    withinClusterQueue: LowerPriority
  admissionChecks: [provisioning-request]
  stopPolicy: None                         # or Hold / HoldAndDrain
```

Up to 16 resourceGroups per ClusterQueue. Each `resourceGroup.coveredResources` must be a disjoint set; the same resource can never appear in two groups.

### 3. LocalQueue

Namespace-scoped pointer to a ClusterQueue. Users reference LocalQueues by name; admins control which ClusterQueue a LocalQueue maps to.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  name: team-a-queue
  namespace: team-a
spec:
  clusterQueue: team-a-cq                  # immutable after creation
  stopPolicy: None
```

The `LocalQueueDefaulting` feature gate enables auto-creation of a `default` LocalQueue per namespace, eliminating the need for users to specify a queue label on every Job.

### 4. Workload

The unit of queueing. One Workload per Job-like object (one batch Job → one Workload, one PyTorchJob → one Workload). Created and owned by the corresponding Job-controller integration.

Key spec fields:
- `podSets[]` — homogeneous groups of Pods with `name`, `template`, `count`, optional `minCount` for partial admission
- `queueName` — target LocalQueue
- `priorityClassName` + `priority` — for ordering and preemption
- `active` — set to false to pause the Workload without deleting it
- `maximumExecutionTimeSeconds` — auto-deactivate after this many seconds running

Key status fields:
- `conditions[]` — `QuotaReserved`, `Admitted`, `PodsReady`, `Finished`, `Evicted`, `Preempted`
- `admission.clusterQueue` — which CQ admitted it
- `admission.podSetAssignments[]` — flavor assignment per podset, with `topologyAssignment` if TAS used
- `admissionChecks[]` — per-check state: `Pending`, `Ready`, `Retry`, `Rejected`
- `requeueState` — counter and timestamp for backoff/retry

Users almost never create Workloads directly — they're synthesized by Kueue from the parent Job.

### 5. Cohort

A grouping of ClusterQueues that can borrow each other's unused quota. Originally an implicit string field on ClusterQueue, now also a CRD that supports hierarchy.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata:
  name: engineering
spec:
  parentName: company-root                 # hierarchical cohorts
  resourceGroups:                          # cohort-level quota pool
  - coveredResources: [cpu, "nvidia.com/gpu"]
    flavors:
    - name: gpu-a100
      resources:
      - name: cpu
        nominalQuota: "200"
      - name: "nvidia.com/gpu"
        nominalQuota: "16"
  fairSharing: { weight: "1" }
```

A ClusterQueue with `spec.cohort: engineering` becomes a member. With hierarchical cohorts, parent quota cascades to children, and `borrowingLimit` controls how much each level can borrow from its parent.

### 6. AdmissionCheck

A pluggable gate that runs after quota is reserved but before the Workload is fully admitted. Built-in checks include MultiKueue (route to a worker cluster) and ProvisioningRequest (trigger autoscaler). Custom controllers can implement their own checks.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: AdmissionCheck
metadata:
  name: provisioning-request
spec:
  controllerName: kueue.x-k8s.io/provisioning-request
  parameters:
    apiGroup: kueue.x-k8s.io
    kind: ProvisioningRequestConfig
    name: gpu-provisioning
```

ClusterQueues opt into a check by listing it in `spec.admissionChecks`. The check's `controllerName` identifies which controller will set the Ready/Retry/Rejected status on the Workload.

### 7. WorkloadPriorityClass

Like Pod `PriorityClass`, but only affects Workload ordering and preemption inside Kueue — never affects Pod scheduling priority.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: prod-high }
value: 1000
description: "Production training jobs"
```

A Workload can carry both a Pod `priorityClassName` (for kube-scheduler) and a `kueue.x-k8s.io/priority-class` label (for Kueue ordering). They're independent — use Workload priority for queue ordering without affecting in-cluster Pod priority.

### 8. Topology

Names a hierarchy of node-label keys (e.g., zone → rack → hostname) that Topology-Aware Scheduling can target.

```yaml
apiVersion: kueue.x-k8s.io/v1alpha1
kind: Topology
metadata: { name: gpu-rack-topology }
spec:
  levels:
  - nodeLabel: topology.kubernetes.io/zone
  - nodeLabel: gpu.example.com/rack
  - nodeLabel: kubernetes.io/hostname
```

A ResourceFlavor opts in via `spec.topologyName`; Workloads request topology placement via PodSet annotations. See `references/advanced-features.md` for the user-facing annotation API.

### Other CRDs (referenced from advanced features)

| CRD | Purpose | Detail |
|-----|---------|--------|
| `MultiKueueConfig` | Lists worker clusters and dispatcher policy | See `advanced-features.md` |
| `MultiKueueCluster` | Per-worker-cluster config + kubeconfig secret | See `advanced-features.md` |
| `ProvisioningRequestConfig` | Parameters for ProvisioningRequest AdmissionCheck | See `advanced-features.md` |
| `AdmissionCheckPolicy` (proposed) | Group of checks applied together | KEP-stage |

## The Scheduling Lifecycle

A 13-step trace from `kubectl apply -f job.yaml` to Pod completion:

| Step | Actor | Action |
|------|-------|--------|
| 1 | User | Creates a Job with `kueue.x-k8s.io/queue-name: team-a-queue` |
| 2 | Mutating webhook | Sets `spec.suspend: true` (the Job creates no Pods) |
| 3 | Job reconciler | Creates a Workload owned by the Job |
| 4 | Workload reconciler | Looks up LocalQueue → resolves to ClusterQueue |
| 5 | Scheduler loop | Iterates pending workloads in queue order |
| 6 | Scheduler | Quota check: does CQ have enough nominal + borrow capacity? |
| 7 | Scheduler | Flavor assignment: try flavors per `flavorFungibility`; may invoke preemption |
| 8 | Workload status | Sets `QuotaReserved=True` with `admission.podSetAssignments` populated |
| 9 | AdmissionCheck controllers | Each listed check sets state to Ready/Retry/Rejected |
| 10 | Workload status | When all checks Ready → sets `Admitted=True` |
| 11 | Job reconciler | Patches Job to `spec.suspend: false` and injects flavor tolerations into Pods |
| 12 | kube-scheduler | Binds the now-unsuspended Pods to nodes |
| 13 | Job reconciler | When Job completes, sets `Finished=True` on Workload; quota is released |

State machine summary:

```
Pending  ──quota OK──▶  QuotaReserved  ──checks Ready──▶  Admitted  ──Pods done──▶  Finished
   │                          │                              │
   │                          ▼                              ▼
   └──Inadmissible───── (Evicted: preempted, check Rejected, queue Held, deactivated) ──┘
```

## Controller Architecture

Single Deployment: `kueue-controller-manager` in the `kueue-system` namespace, leader-elected for HA. The same binary runs all reconcilers, the scheduler loop, the metrics server, and the webhook server.

### Reconcilers

| Reconciler | Watches | Reconciles |
|-----------|---------|-----------|
| Job-integration reconcilers (one per framework) | batch.Job, PyTorchJob, RayJob, ... | Creates/updates the Workload, suspends/unsuspends the Job, injects tolerations |
| Workload reconciler / scheduler | Workload | Quota reservation, flavor assignment, admission check coordination, eviction |
| ClusterQueue reconciler | ClusterQueue | Updates `status.flavorsUsage`, pending counts; detects cohort cycles |
| LocalQueue reconciler | LocalQueue | Mirrors a subset of ClusterQueue stats into the namespace |
| AdmissionCheck reconciler | AdmissionCheck | Maintains the Active condition |
| Cohort reconciler | Cohort | Maintains the cohort tree, propagates fair-sharing weight |

### In-Memory Cache (the "snapshot")

The scheduler keeps an in-memory cache of every ClusterQueue's quota usage and every pending Workload's resource needs. Each scheduling cycle works against a *snapshot* of this cache, not the API server, so admission decisions are sub-millisecond. The cache is rebuilt at startup from the API server and incrementally updated by reconcilers.

### Webhooks

| Webhook | Type | Effect |
|---------|------|--------|
| Job mutating webhook (one per framework) | Mutating | Sets `spec.suspend: true` on creation; sets default queue name |
| Workload validating webhook | Validating | Rejects malformed podSets / impossible flavor requests |
| ClusterQueue / Cohort validating webhook | Validating | Catches cohort cycles, conflicting flavors |

Webhooks require TLS certificates. `internalCertManagement` (default true) auto-generates them; alternatively you can use cert-manager (`internalCertManagement.enable: false`).

## Resource Model

### Quota Math

For each `(ClusterQueue, flavor, resource)` cell:
- `nominalQuota` — guaranteed amount; cannot be revoked by cohort siblings
- `borrowingLimit` — max additional amount borrowable from cohort siblings (nil = unlimited within cohort)
- `lendingLimit` — max amount this CQ exposes for siblings to borrow (nil = all unused)
- `usage` — sum of resource requests across admitted Workloads
- `borrowed` — current amount this CQ is borrowing from cohort

The admission check is: `usage + new_workload_request ≤ nominalQuota + min(borrowingLimit, sibling_lendable)`.

### Cohort Borrowing

ClusterQueues in the same cohort form a single borrowing pool per `(flavor, resource)`. A CQ's unused `nominalQuota` (up to its `lendingLimit`) is available for siblings to borrow. Borrowing is symmetric — there's no "owner" of borrowed capacity.

When a sibling's own workload arrives and would normally fit inside its `nominalQuota`, the borrower may be preempted via `preemption.reclaimWithinCohort` (Never / LowerPriority / Any). This is how nominal quota stays guaranteed.

### Flavor Fungibility

When a Workload's resources can be served by multiple flavors (e.g., spot or on-demand), `flavorFungibility` controls fall-through:

| `whenCanBorrow` | Behavior |
|-----------------|----------|
| `Borrow` (default) | If borrowing in current flavor works, use it |
| `TryNextFlavor` | Skip to next flavor before borrowing — useful for "try cheap flavor first" |

| `whenCanPreempt` | Behavior |
|------------------|----------|
| `TryNextFlavor` (default) | Try next flavor before resorting to preemption in current |
| `Preempt` | Preempt within current flavor before falling through |

Real example: list `[spot, ondemand]` with `whenCanBorrow: TryNextFlavor` means "try spot, if spot is full borrow on-demand instead of borrowing more spot from the cohort".

## Queueing Strategies

| Strategy | Behavior | When to use |
|----------|----------|-------------|
| `BestEffortFIFO` (default) | Workloads sorted by priority then creation; head-of-line workloads that can't fit are skipped so smaller jobs can admit | Maximize cluster utilization |
| `StrictFIFO` | Strict FIFO — head of queue blocks all others | Strong fairness when starvation is unacceptable |

Combine with `WorkloadPriorityClass` to get priority-then-FIFO ordering.

## Workload Status Conditions

| Condition | True means |
|-----------|-----------|
| `QuotaReserved` | Quota allocated; flavor assignment exists in `status.admission` |
| `Admitted` | Quota reserved AND all admission checks Ready; Job will be unsuspended |
| `PodsReady` | All Pods have started and are Ready (only set when `waitForPodsReady` is enabled) |
| `Finished` | Underlying Job completed (success or failure) |
| `Evicted` | Workload removed from admission; reason explains why (Preempted, AdmissionCheck, Deactivated, etc.) |

The `Inadmissible` condition is *not* a separate state — it's reported as a reason when scheduling fails. Possible reasons include: `NoFit` (insufficient quota), `Preempted`, `RequeuedByAdmissionCheck`, `Deactivated`.

## Stop Policy

Both ClusterQueue and LocalQueue support `stopPolicy`:

| Value | Behavior |
|-------|----------|
| `None` (default) | Normal admission |
| `Hold` | Stop admitting new Workloads; running Workloads keep running |
| `HoldAndDrain` | Stop admitting AND evict all admitted Workloads (they re-queue elsewhere or stay pending) |

Use `Hold` for safe drains during maintenance, `HoldAndDrain` for emergencies.

## Where to Look Next

| Topic | Reference |
|-------|-----------|
| How to install + the Configuration kind | `installation-and-config.md` |
| Per-framework wiring (Kubeflow, Ray, Pods, ...) | `job-integrations.md` |
| Preemption, fair sharing, MultiKueue, TAS, ProvisioningRequest | `advanced-features.md` |
| kueuectl + Prometheus metrics + troubleshooting | `operations-and-cli.md` |
| Real-world cohort/flavor topologies | `quota-and-tenancy-patterns.md` |
| End-to-end recipes | `use-cases-and-recipes.md` |

## Sources

- https://kueue.sigs.k8s.io/docs/concepts/
- https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/
- https://kueue.sigs.k8s.io/docs/concepts/local_queue/
- https://kueue.sigs.k8s.io/docs/concepts/resource_flavor/
- https://kueue.sigs.k8s.io/docs/concepts/workload/
- https://kueue.sigs.k8s.io/docs/concepts/cohort/
- https://kueue.sigs.k8s.io/docs/concepts/admission_check/
- https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/
- https://kueue.sigs.k8s.io/docs/concepts/workload_priority_class/
- https://github.com/kubernetes-sigs/kueue/tree/main/apis/kueue/v1beta1
- https://github.com/kubernetes-sigs/kueue/tree/main/apis/kueue/v1
