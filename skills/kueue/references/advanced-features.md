# Advanced Features

Sources: Kueue documentation (kueue.sigs.k8s.io/docs/concepts/preemption/, /fair_sharing/, /multikueue/, /topology_aware_scheduling/, /admission_check/, /elastic_workload/, /tasks/manage/setup_wait_for_pods_ready/), KEPs in kubernetes-sigs/kueue/keps for hierarchical cohorts and lending limits.

Covers: preemption (within-CQ + within-cohort), fair sharing (DRF + AdmissionFairSharing), MultiKueue (federated multi-cluster), Topology-Aware Scheduling, ProvisioningRequest (Cluster Autoscaler/Karpenter integration), hierarchical cohorts, WorkloadPriorityClass, partial admission and elastic jobs (workload slices), gang scheduling via waitForPodsReady, and writing a custom AdmissionCheckController.

## Preemption

Preemption evicts admitted Workloads to make room for a higher-priority pending Workload. Three independent policies on `ClusterQueue.spec.preemption`:

| Policy | Field | Values | What it controls |
|--------|-------|--------|-----------------|
| Within-queue | `withinClusterQueue` | `Never`, `LowerPriority`, `LowerOrNewerEqualPriority`, `Any` | Preempt other Workloads in the *same* CQ |
| Reclaim borrowed | `reclaimWithinCohort` | `Never`, `LowerPriority`, `Any` | Reclaim quota that's been borrowed by cohort siblings |
| Borrow with preemption | `borrowWithinCohort.policy` | `Never`, `LowerPriority` | While preempting, also borrow from cohort |

```yaml
preemption:
  withinClusterQueue: LowerPriority
  reclaimWithinCohort: Any                # take back nominal quota at any priority
  borrowWithinCohort:
    policy: LowerPriority
    maxPriorityThreshold: 999             # don't preempt anything ≥ 1000
```

### Two algorithms

**Classic preemption** (default) — fast, lightweight. Conditions: the preempting CQ's usage will be ≤ its `nominalQuota` after admission, OR `borrowWithinCohort` is enabled. Candidates: same-CQ Workloads matching `withinClusterQueue`, or borrowing siblings matching `reclaimWithinCohort`. Tie-break: borrowing siblings first, then lowest priority, then most recently admitted.

**Fair-sharing preemption** (when `fairSharing.enable: true`) — selects victims to equalize the cohort's DRF share. The strategies (`fairSharing.preemptionStrategies`) determine when preemption is allowed:
- `LessThanOrEqualToFinalShare` — preempt only if preempting CQ's *post-admission* DRF share ≤ target CQ's *post-eviction* share. Stable; no oscillation.
- `LessThanInitialShare` — preempt only if preempting CQ's *post-admission* share < target's *current* share. More aggressive.

Configure both in order: `[LessThanOrEqualToFinalShare, LessThanInitialShare]` tries the safer first, falls back to aggressive.

### Status after preemption

A preempted Workload's status carries:

```yaml
status:
  conditions:
  - type: Evicted
    status: "True"
    reason: Preempted
    message: 'Preempted to accommodate a workload (UID: ...) due to prioritization in the ClusterQueue'
  - type: Preempted
    status: "True"
    reason: InClusterQueue          # or InCohortReclamation, FairSharing
```

The Job's `spec.suspend` flips back to `true`, Pods are terminated, and the Workload re-enters the queue (typically with backoff).

## Fair Sharing

Two distinct features, both opt-in via `Configuration.fairSharing` and `Configuration.admissionFairSharing`:

### Cohort-level fair sharing (DRF + preemption)

Distributes borrowable cohort capacity across sibling CQs in proportion to `fairSharing.weight`. Higher weight → larger share entitled.

```yaml
# Configuration
fairSharing:
  enable: true
  preemptionStrategies: [LessThanOrEqualToFinalShare]

# Per-ClusterQueue
spec:
  cohort: shared
  fairSharing: { weight: "2" }            # this CQ gets 2x share
```

Share is exposed at `clusterQueue.status.fairSharing.weightedShare` and via the `kueue_cluster_queue_weighted_share` metric. Higher value = "currently using more than fair share". A pending Workload in a CQ with low share can preempt admitted Workloads from siblings with high share.

**Loop-free guarantee**: With `LessThanOrEqualToFinalShare`, if A could preempt B then `share(A_after) ≤ share(B_after)`. Symmetrically B can't preempt A — proves no thrashing.

### AdmissionFairSharing (per-namespace, intra-CQ)

Within a single CQ shared by multiple namespaces, this orders pending Workloads by historical resource usage of their LocalQueue, favoring those that have used less.

```yaml
admissionFairSharing:
  usageHalfLifeTime: 15m                 # exponential decay of historical usage
  usageSamplingInterval: 5m
  resourceWeights:
    cpu: 1
    memory: 1
    "nvidia.com/gpu": 100                # GPU usage dominates the dominant-resource calc
```

Use this when one namespace tends to flood the queue and starve others.

## MultiKueue (federated multi-cluster)

Run a *management* cluster that holds quotas + Workloads, dispatching the actual Job to one of N *worker* clusters. The management cluster's kueue-controller-manager keeps remote Workload/Job status in sync.

### Setup

**1. On each worker cluster**: install Kueue normally; create a service account that has cluster-admin (or scoped permissions for the workload kinds you'll dispatch). Export the kubeconfig.

**2. On the management cluster**: store each worker's kubeconfig as a secret in `kueue-system`:

```bash
kubectl -n kueue-system create secret generic worker1-kubeconfig --from-file=kubeconfig=worker1.kubeconfig
```

**3. Define the worker registry**:

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: MultiKueueCluster
metadata: { name: worker1 }
spec:
  kubeConfig: { locationType: Secret, location: worker1-kubeconfig }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: MultiKueueConfig
metadata: { name: multi-prod }
spec:
  clusters: [worker1, worker2]
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: AdmissionCheck
metadata: { name: multikueue-prod }
spec:
  controllerName: kueue.x-k8s.io/multikueue
  parameters: { apiGroup: kueue.x-k8s.io, kind: MultiKueueConfig, name: multi-prod }
```

**4. Wire the AdmissionCheck into the ClusterQueue** that should federate:

```yaml
spec:
  admissionChecks: [multikueue-prod]
```

### Lifecycle

1. Job submitted on management → Workload created → quota reserved
2. MultiKueue admission check controller picks targets per `dispatcherName` policy
3. Workload (and Job copy) created on chosen worker cluster(s)
4. First worker that admits "wins" — others get the Workload deleted
5. Manager mirrors `status` back to local Job and Workload
6. On completion, manager deletes the remote objects

### Dispatcher policies

| `dispatcherName` | Behavior | Trade-off |
|-----------------|----------|-----------|
| `kueue.x-k8s.io/multikueue-dispatcher-all-at-once` (default) | Copy to all workers immediately; first to admit wins | Fast, may stress autoscalers |
| `kueue.x-k8s.io/multikueue-dispatcher-incremental` | Add 3 workers per round; wait 5min before next round | Gentle on autoscalers, slower |
| Custom | External controller writes `status.nominatedClusterNames` | Full placement control |

### Supported workloads

batch/v1 Job (with `spec.managedBy: kueue.x-k8s.io/multikueue`), JobSet, all Kubeflow training jobs, RayJob, RayCluster, AppWrapper, Deployment, StatefulSet, LeaderWorkerSet, plain Pods, custom externalFrameworks. The `MultiKueueBatchJobWithManagedBy` feature gate (GA in 0.13) handles batch Jobs.

### Limitations

- Management cluster cannot also be a worker cluster (no self-loop)
- Workloads without `managedBy` (StatefulSet, LWS) get status synced via Kueue's mirror — local readiness may briefly disagree with worker truth
- A Workload can only run on *one* worker at a time; this is dispatch, not replication

## Topology-Aware Scheduling (TAS)

Place Pods within a network/hardware topology to maximize bandwidth (NVLink, NVSwitch, NCCL all-reduce, InfiniBand) for tightly-coupled training.

### Define the topology

Node labels expose a hierarchy. For example, an NVIDIA GPU rack:

```
node:    kubernetes.io/hostname=gpu-001
rack:    cloud.example.com/rack=rack-1
block:   cloud.example.com/block=block-A
```

Then a `Topology` CRD names the levels in order from coarsest to finest:

```yaml
apiVersion: kueue.x-k8s.io/v1alpha1
kind: Topology
metadata: { name: gpu-topology }
spec:
  levels:
  - nodeLabel: cloud.example.com/block
  - nodeLabel: cloud.example.com/rack
  - nodeLabel: kubernetes.io/hostname
```

A ResourceFlavor opts in:

```yaml
spec:
  nodeLabels: { accelerator: nvidia-h100 }
  topologyName: gpu-topology
```

### User-facing PodSet annotations

Applied to the workload's PodTemplate (`spec.template.metadata.annotations`):

| Annotation | Effect |
|-----------|--------|
| `kueue.x-k8s.io/podset-required-topology: <level>` | Hard: all Pods in this PodSet must land in one domain at this level. Workload won't admit if no single domain can fit |
| `kueue.x-k8s.io/podset-preferred-topology: <level>` | Soft: try to fit all in one domain; spread if necessary |
| `kueue.x-k8s.io/podset-unconstrained-topology: "true"` | Anywhere — TAS ignored, but Workload is still tracked |
| `kueue.x-k8s.io/podset-group-name: <group>` | Group multiple PodSets together so they all land in the same domain |
| `kueue.x-k8s.io/podset-slice-required-topology-constraints` (Alpha) | Multi-layer constraints: e.g., 32 pods per block AND 16 per rack |

### Capacity calculation

For each topology domain, TAS computes free capacity = `node-allocatable − usage from other admitted TAS Workloads − usage from non-TAS Pods (DaemonSets, kube-system, Deployments without TAS)`.

### Hot-swap on node failure

Three feature gates (default beta-on in 0.14): `TASFailedNodeReplacement`, `TASReplaceNodeOnPodTermination`, `TASFailedNodeReplacementFailFast`. When a TAS-pinned node fails, Kueue tries to find a replacement node in the same domain without disturbing other Pod-to-node bindings. With FailFast on, a single attempt; otherwise it retries with backoff before evicting the whole Workload.

### Balanced placement (alpha)

`TASBalancedPlacement` distributes Pods evenly across child domains (one level below the requested topology) instead of greedy-packing. Useful for all-to-all collective communication that benefits from uniform distribution.

## ProvisioningRequest (Cluster Autoscaler / Karpenter)

Two-stage admission: quota reservation succeeds → ProvisioningRequest is created → external autoscaler responds → Workload admits.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: AdmissionCheck
metadata: { name: gpu-provision }
spec:
  controllerName: kueue.x-k8s.io/provisioning-request
  parameters:
    apiGroup: kueue.x-k8s.io
    kind: ProvisioningRequestConfig
    name: gpu-provisioning-config
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ProvisioningRequestConfig
metadata: { name: gpu-provisioning-config }
spec:
  provisioningClassName: queued-provisioning.gke.io   # GKE; or check-capacity.autoscaling.x-k8s.io
  managedResources: ["nvidia.com/gpu"]
  retryStrategy:
    backoffLimitCount: 2
    backoffBaseSeconds: 60
    backoffMaxSeconds: 1800
  podSetMergePolicy: IdenticalWorkloadSchedulingRequirements
```

Provisioning class names you'll commonly see:

| Class | Provider |
|-------|----------|
| `check-capacity.autoscaling.x-k8s.io` | Generic Cluster Autoscaler — only checks if capacity exists |
| `queued-provisioning.gke.io` | GKE — reserves capacity via flex-start pricing |
| `karpenter.sh/...` | Karpenter | (consult Karpenter version's docs) |

ProvisioningRequest status flows through `Provisioned: false → true`, `Failed: true`, `BookingExpired: true`, `CapacityRevoked: true`. Kueue's AdmissionCheck mirrors these to its own state (`Pending → Ready → Retry/Rejected`).

### Per-Job overrides via annotations

```yaml
metadata:
  annotations:
    provreq.kueue.x-k8s.io/maxRunDurationSeconds: "3600"
```

Any annotation prefixed `provreq.kueue.x-k8s.io/` is forwarded as a parameter to the ProvisioningRequest CR.

## Hierarchical Cohorts

Cohort is now a CRD (was just a string). With `parentName`, cohorts form a tree, and capacity flows down.

```yaml
# Root: org pool
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: company }
spec: {}
---
# Child: department, gets weighted share
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: ml-platform }
spec:
  parentName: company
  fairSharing: { weight: "0.6" }            # gets 60% of company-level borrowable pool
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: data-platform }
spec:
  parentName: company
  fairSharing: { weight: "0.4" }
---
# Team CQ joins department cohort
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-llm }
spec:
  cohort: ml-platform                       # joins the department cohort, can borrow from siblings + parent
  resourceGroups: [...]
```

A Cohort can also carry its own `resourceGroups` defining a shared pool (children with `nominalQuota: 0` borrow from it). Use this for "the company has 100 GPUs total, allocate them across departments".

## WorkloadPriorityClass

Decouple Kueue ordering priority from kube-scheduler Pod priority.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: prod-high }
value: 10000
description: "Production training & inference"
```

Apply via label on the parent Job: `kueue.x-k8s.io/priority-class: prod-high`. Kueue copies it to `Workload.spec.priorityClassRef` and sets `.spec.priority`. The Pod's own `priorityClassName` (if any) is independent and used by kube-scheduler.

| Pod has PriorityClass | Job has WorkloadPriorityClass label | Kueue ordering | Pod scheduling |
|----------------------|------------------------------------|----------------|----------------|
| Yes | Yes | WPC value | Pod's PriorityClass |
| No | Yes | WPC value | (no Pod priority) |
| Yes | No | Pod's PriorityClass value | Pod's PriorityClass |
| No | No | 0 | (no Pod priority) |

Mutability: the label and `.spec.priority` are mutable while pending; immutable once `QuotaReserved=True`. Mutating the PriorityClass *value* doesn't propagate retroactively.

## Partial Admission and Elastic Jobs

### Partial admission

For Jobs with `parallelism: N`, allow admission with as few as `M` Pods.

```yaml
metadata:
  annotations:
    kueue.x-k8s.io/job-min-parallelism: "5"     # admit if at least 5 of 20 fit
spec:
  parallelism: 20
  completions: 20
```

Kueue clamps `spec.parallelism` to whatever fits between min and N at unsuspend time. Useful for Indexed Jobs that can run with degraded width.

### Elastic Jobs (workload slices, alpha)

Behind `ElasticJobsViaWorkloadSlices`. Lets a Job's `parallelism` change *without* eviction/requeue.

```yaml
metadata:
  annotations:
    kueue.x-k8s.io/elastic-job: "true"
  labels:
    kueue.x-k8s.io/queue-name: team-a-queue
spec:
  parallelism: 3
  completions: 100
```

Scaling up creates a new Workload "slice" referencing the same Job; the old slice is marked Finished. Scaling down updates the existing slice. Limited to: batch/v1 Job, RayJob, RayCluster. Not compatible with partial admission, MultiKueue, or TAS.

## Gang Scheduling — waitForPodsReady

All-or-nothing: if all Pods don't become Ready within the timeout, evict and requeue the whole Workload.

```yaml
# Configuration
waitForPodsReady:
  enable: true
  timeout: 10m
  recoveryTimeout: 3m
  blockAdmission: true                      # admit one Workload at a time
  requeuingStrategy:
    timestamp: Eviction                     # or Creation (preserves position)
    backoffLimitCount: 5
    backoffBaseSeconds: 60
    backoffMaxSeconds: 3600
```

Backoff per requeue: `min(backoffBaseSeconds × 2^n, backoffMaxSeconds)`.

`blockAdmission: true` is the standard fix for the "admitted-but-deadlocked" case where two large Workloads each get half their Pods running and starve. Sequential admission costs throughput on healthy clusters; pair with TAS or set `blockAdmission: false` if your physical capacity reliably matches your declared quota.

## AdmissionCheck Framework

`AdmissionCheck` is a generic gate. The built-in checks are MultiKueue and ProvisioningRequest; you can write your own.

### How a CQ uses checks

```yaml
spec:
  admissionChecks: [check-a, check-b]              # runs concurrently for every Workload
# OR per-flavor:
  admissionChecksStrategy:
    admissionChecks:
    - { name: check-a, onFlavors: [gpu-a100] }     # only when a100 is chosen
    - { name: check-b }                            # always
```

### State machine

| State | Meaning | Effect on Workload |
|-------|---------|-------------------|
| `Pending` | Not yet evaluated | Stay in QuotaReserved |
| `Ready` | Pass | If all checks Ready → `Admitted=True` |
| `Retry` | Transient failure | Workload evicted (if Admitted) or quota released; backoff then re-evaluate |
| `Rejected` | Hard failure | Workload deactivated (`spec.active: false`); event `AdmissionCheckRejected` |

Status carries `podSetUpdates[]` — annotations/labels/tolerations to inject into Pods at unsuspend time. ProvisioningRequest uses this to inject the `cluster-autoscaler.kubernetes.io/consume-provisioning-request` annotation.

### Writing a custom controller

Pattern, in pseudocode:

```go
// Watch Workload; for each one, find admissionChecks[] entries with our controllerName
for wl in workloads where check.controllerName == "mycorp.example.com/billing-check":
    decision := callBillingService(wl.spec.podSets)
    patchWorkloadStatus(wl, check.name, decision.state, decision.message, decision.podSetUpdates)
```

Reference implementation: `pkg/controller/admissionchecks/provisioning/` in the Kueue repo. Register the controller's name in your AdmissionCheck:

```yaml
spec:
  controllerName: mycorp.example.com/billing-check
  parameters: { apiGroup: ..., kind: ..., name: ... }
```

## Sources

- https://kueue.sigs.k8s.io/docs/concepts/preemption/
- https://kueue.sigs.k8s.io/docs/concepts/fair_sharing/
- https://kueue.sigs.k8s.io/docs/concepts/multikueue/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_multikueue/
- https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_topology_aware_scheduling/
- https://kueue.sigs.k8s.io/docs/concepts/admission_check/
- https://kueue.sigs.k8s.io/docs/concepts/admission_check/provisioning_request/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_provisioning_request/
- https://kueue.sigs.k8s.io/docs/concepts/cohort/
- https://kueue.sigs.k8s.io/docs/concepts/workload_priority_class/
- https://kueue.sigs.k8s.io/docs/concepts/elastic_workload/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_wait_for_pods_ready/
- https://github.com/kubernetes-sigs/kueue/tree/main/keps
