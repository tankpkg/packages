# Operations, Services, and Migration Recipes

Sources: Kueue documentation tasks (kueue.sigs.k8s.io/docs/tasks/run/, /tasks/manage/), Google Cloud GKE Kueue tutorials, Karpenter + Kueue integration docs, KubeCon talks 2024-2025.

Covers: production recipes for MPI/HPC topology-aware scheduling, Deployment quota, plain Pod queueing for Argo, AppWrapper gang admission, elastic Jobs, CI/CD runner pools, online-vs-batch LLM inference, staged rollout, verification commands, and gotchas.

## Recipe 8 — HPC MPI with topology-aware scheduling

**Scenario**: 8-process MPIJob requires all Pods on one rack for InfiniBand locality.

```yaml
apiVersion: kueue.x-k8s.io/v1alpha1
kind: Topology
metadata: { name: hpc-topology }
spec:
  levels:
  - { nodeLabel: cloud.example.com/rack }
  - { nodeLabel: kubernetes.io/hostname }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: hpc }
spec:
  nodeLabels: { hpc-capable: "true" }
  topologyName: hpc-topology
---
apiVersion: kubeflow.org/v1
kind: MPIJob
metadata:
  name: hpc-train
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  slotsPerWorker: 1
  cleanPodPolicy: Running
  mpiReplicaSpecs:
    Launcher:
      replicas: 1
      template:
        metadata:
          annotations: { kueue.x-k8s.io/podset-required-topology: cloud.example.com/rack }
        spec:
          containers:
          - { name: l, image: nvcr.io/nvidia/pytorch:23.04-py3, command: [mpirun, -np, "8", python, train.py], resources: { requests: { cpu: "8", "nvidia.com/gpu": "1" } } }
          restartPolicy: OnFailure
    Worker:
      replicas: 7
      template:
        metadata:
          annotations: { kueue.x-k8s.io/podset-required-topology: cloud.example.com/rack }
        spec:
          containers:
          - { name: w, image: nvcr.io/nvidia/pytorch:23.04-py3, resources: { requests: { cpu: "8", "nvidia.com/gpu": "1" } } }
          restartPolicy: OnFailure
```

**Verify**: `kubectl get pods -l mpi-job-name=hpc-train -o wide` — all 8 Pods should land on the same rack.

**Gotchas**: Required topology means the Workload won't admit at all if no rack has 8 free GPUs. Use `podset-preferred-topology` for soft constraints. The TAS feature gate (`TopologyAwareScheduling`) must be enabled.

## Recipe 9 — Long-running service with quota (Deployment)

**Scenario**: An inference Deployment competes for GPU quota alongside batch jobs.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  replicas: 10
  selector: { matchLabels: { app: api } }
  template:
    metadata:
      labels:
        app: api
        kueue.x-k8s.io/queue-name: default      # Pod-level label for the pod integration
    spec:
      containers:
      - { name: api, image: myinference:1.0, resources: { requests: { cpu: "2", memory: 4Gi, "nvidia.com/gpu": "1" } } }
```

Requires `pod` (and `deployment`) in `integrations.frameworks` and the namespace included in `managedJobsNamespaceSelector`. Each Pod is a separate Workload — scaling the Deployment up requests more quota.

**Gotchas**: If quota is full, new replicas stay Pending instead of forcing eviction. To gang-admit replicas atomically, prefer `LeaderWorkerSet` or wrap in an AppWrapper.

## Recipe 10 — Plain Pods for Argo Workflows

**Scenario**: Argo Workflow steps as plain Pods, queued through Kueue.

```yaml
# Configuration must enable: integrations.frameworks: [pod]
# and managedJobsNamespaceSelector matching argo namespace
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata: { generateName: pw-, namespace: argo }
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - { name: s1, template: worker }
    - - { name: s2, template: worker }
  - name: worker
    metadata:
      labels:
        kueue.x-k8s.io/queue-name: default
        kueue.x-k8s.io/pod-group-name: pw-group
      annotations:
        kueue.x-k8s.io/pod-group-total-count: "2"
    container:
      image: busybox
      command: [sh, -c, "sleep 60"]
      resources: { requests: { cpu: "2" } }
```

Pod-group annotations are the key — without them, each step Pod admits independently and you lose gang semantics.

**Gotchas**: `managedJobsNamespaceSelector` must include `argo`. Without `pod-group-total-count`, Kueue can't tell when the group is "complete".

## Recipe 11 — AppWrapper gang-admission for arbitrary workloads

**Scenario**: Atomically admit several resources together that wouldn't otherwise be one Workload.

```yaml
apiVersion: workload.codeflare.dev/v1beta2
kind: AppWrapper
metadata:
  name: bundled
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  components:
  - template:
      apiVersion: kubeflow.org/v1
      kind: PyTorchJob
      metadata: { name: trainer }
      spec: { ... }
  - template:
      apiVersion: v1
      kind: Service
      metadata: { name: trainer-svc }
      spec: { ... }
```

The PyTorchJob and Service are created together only when the AppWrapper admits.

## Recipe 12 — Elastic Job

**Scenario**: A Job whose `parallelism` changes mid-run, without re-suspension.

```yaml
# Requires: ElasticJobsViaWorkloadSlices=true feature gate
apiVersion: batch/v1
kind: Job
metadata:
  name: elastic
  labels: { kueue.x-k8s.io/queue-name: default }
  annotations: { kueue.x-k8s.io/elastic-job: "true" }
spec:
  parallelism: 3
  completions: 100
  template:
    spec:
      restartPolicy: Never
      containers:
      - { name: w, image: alpine, command: [sh, -c, "sleep 30"], resources: { requests: { cpu: "1" } } }
```

`kubectl scale --replicas=10 job/elastic` (or just patching parallelism) creates new slices without requeuing the existing work.

## Recipe 13 — CI/CD test runner pool (priority + cohort)

**Scenario**: GitHub Actions runner Jobs — PR checks low-priority, main-branch high-priority, both bursting from a shared pool.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: ci-main }
value: 1000
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: ci-pr }
value: 100
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: ci-cq }
spec:
  cohort: ci
  resourceGroups:
  - coveredResources: [cpu, memory]
    flavors:
    - name: default
      resources:
      - { name: cpu,    nominalQuota: "32",  borrowingLimit: "32" }
      - { name: memory, nominalQuota: "128Gi", borrowingLimit: "128Gi" }
  preemption: { withinClusterQueue: LowerPriority }
```

Submit each runner Job with `kueue.x-k8s.io/priority-class: ci-pr` (PRs) or `ci-main` (main). When CI is busy, main-branch runners preempt PR runners.

## Recipe 14 — LLM batch inference (online-priority preempts batch)

**Scenario**: Same GPU pool serves online inference (prompt-time critical) and batch inference (latency-tolerant). Online preempts batch.

```yaml
# Same shape as Recipe 2 (multi-team GPU sharing) — substitute teams with workload classes:
# - "online-cq" with high-priority WorkloadPriorityClass
# - "batch-cq" with low-priority, can be preempted by online
# Use cohort + reclaimWithinCohort: Any on online-cq
```

In practice, a vLLM serving Deployment with `kueue.x-k8s.io/priority-class: online` admits to the high-priority CQ. Ray batch jobs with `priority-class: batch` get whatever's left and shed when online demand spikes.

## Recipe 15 — Staged Kueue rollout on an existing cluster

A safe migration playbook over 4 weeks:

| Week | Action | Verify |
|------|--------|--------|
| 1 | Install Kueue with `manageJobsWithoutQueueName: false`. Create one CQ + LQ. No production Jobs labeled yet. | Controller Pods Healthy; metrics scraping; no behavior change |
| 2 | Pick one team's namespace. Add namespace label, label their Jobs with `queue-name`. Monitor admission/eviction. | Admission rate matches Job submission rate; no surprise evictions |
| 3 | Add second team. Put both CQs in a cohort. Set explicit `borrowingLimit`. | Idle quota from one team gets borrowed by the other |
| 4 | Add `WorkloadPriorityClass` for prod vs research. Enable `preemption.reclaimWithinCohort: LowerPriority` on prod CQ. | Production Jobs preempt research when cohort is full |
| later | Enable `fairSharing.enable: true`. Add ProvisioningRequest. Add MultiKueue if multi-cluster. | Per phase: confirm `kueue_cluster_queue_weighted_share` evens out; ProvReq flow works end-to-end |

Quota changes are non-destructive: increasing nominalQuota never evicts; decreasing just blocks new admissions. So you can iterate quota numbers safely in production.

## Pattern Selection Cheatsheet

| If your goal is... | Use this recipe |
|--------------------|-----------------|
| Just learn Kueue | Recipe 1 (basic batch) |
| Multi-team GPU isolation | Recipe 2 (cohort + preemption + WorkloadPriorityClass) |
| Distributed PyTorch / TensorFlow training | Recipe 3 (Kubeflow PyTorchJob) |
| Hyperparameter sweeps with elastic compute | Recipe 4 (RayJob + elastic) |
| Cost optimization with spot fallback | Recipe 5 (two flavors + flavorFungibility) |
| GPU autoscaling | Recipe 6 (ProvisioningRequest + Karpenter/CA) |
| Multi-region or multi-cluster federation | Recipe 7 (MultiKueue) |
| Tightly-coupled HPC / NCCL | Recipe 8 (TAS + MPIJob) |
| Long-running services on quota | Recipe 9 (Deployment integration) |
| Argo Workflows steps | Recipe 10 (plain Pods + pod-group) |
| Gang-admit a non-supported workload | Recipe 11 (AppWrapper) |
| Job that grows/shrinks at runtime | Recipe 12 (elastic via workload slices) |
| CI/CD runners with bursting | Recipe 13 (priority + cohort) |
| Mixed online + batch GPU serving | Recipe 14 (preemption hierarchy) |
| Migrating existing cluster onto Kueue | Recipe 15 (staged rollout) |

## Common Verification Commands

```bash
# Workload status
kueuectl describe workload <name>
kueuectl list workload --status=pending --clusterqueue=<cq>

# Quota state
kueuectl describe clusterqueue <cq>
kubectl get clusterqueue <cq> -o jsonpath='{.status.flavorsUsage}' | jq

# Events for a stuck Workload
kubectl get events --field-selector involvedObject.name=<wl>

# Verify the Job is suspended by Kueue (not running yet)
kubectl get job <name> -o jsonpath='{.spec.suspend}'

# Check admission check progress
kubectl get workload <wl> -o jsonpath='{.status.admissionChecks}' | jq
```

## Common Gotchas (master list)

1. Missing `kueue.x-k8s.io/queue-name` label → Workload never created.
2. Job runs immediately (not suspended) → integration not enabled, or the framework string mismatch.
3. Workload Inadmissible forever → Pod requests don't fit any flavor's quota, OR ResourceFlavor `nodeLabels` don't match real nodes.
4. QuotaReserved=True but Admitted=False → AdmissionCheck stuck in Pending; check the relevant controller.
5. Pods admit but never become Ready → flavor's nodeSelector / tolerations don't match Pod placement.
6. Borrowing not happening → `cohort` field missing, or `borrowingLimit: 0` set.
7. Preemption not happening → wrong priority order, or preemption policy = Never.
8. ProvisioningRequest never created → AdmissionCheck not listed in CQ's `admissionChecks`.
9. MultiKueue worker not connecting → kubeconfig secret missing, wrong namespace, or insufficient RBAC.
10. Pod integration capturing system Pods → tighten `managedJobsNamespaceSelector`.

## Sources

- https://kueue.sigs.k8s.io/docs/tasks/run/
- https://kueue.sigs.k8s.io/docs/tasks/manage/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_provisioning_request/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_multikueue/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_topology_aware_scheduling/
- https://kueue.sigs.k8s.io/docs/tasks/run/rayjobs/
- https://kueue.sigs.k8s.io/docs/tasks/run/kubeflow/
- https://kueue.sigs.k8s.io/docs/tasks/run/plain_pods/
- https://github.com/kubernetes-sigs/kueue/tree/main/examples
