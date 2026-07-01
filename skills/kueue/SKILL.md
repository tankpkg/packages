---
name: "@tank/kueue"
description: |
  Kubernetes-native job queueing for batch, AI/ML, and HPC workloads using
  Kueue. Covers CRDs, suspend-then-admit scheduling, supported integrations,
  installation/configuration, observability, quota sharing, and production
  operations. Synthesizes kueue.sigs.k8s.io, kubernetes-sigs/kueue APIs and
  KEPs, kueuectl, Prometheus metrics, and cloud autoscaling patterns.

  Trigger phrases: "kueue", "kueuectl", "kubernetes job queue",
  "ClusterQueue", "LocalQueue", "ResourceFlavor", "Workload", "Cohort",
  "AdmissionCheck", "MultiKueue", "ProvisioningRequest", "Topology-Aware Scheduling", "Karpenter Kueue", "cluster autoscaler kueue", "GPU quota",
  "PyTorchJob", "RayJob", "MPIJob", "JobSet", "AppWrapper",
  "Kubeflow training", "gang scheduling", "fair sharing", "borrowing limit",
  "lending limit", "nominal quota", "waitForPodsReady", "Kueue metrics"
---

# Kueue

## Core Philosophy

1. **Suspend first, admit later** — Every supported Job is created in `suspend: true` state by Kueue's mutating webhook. The Workload object is the queueing unit; the Job only unsuspends after the Workload is admitted. Never bypass this by setting `suspend: false` manually.
2. **Quota lives on the ClusterQueue, naming lives on the LocalQueue** — Users submit Jobs with a `kueue.x-k8s.io/queue-name: <local-queue>` label. The LocalQueue points to a ClusterQueue, which holds the actual quota. This separates tenant identity from capacity policy.
3. **Cohorts are how slack capacity is shared** — Two ClusterQueues in the same `cohort` can borrow each other's unused `nominalQuota` up to their `borrowingLimit`. Without a cohort, quota is hard-isolated. Set `lendingLimit` to cap how much a queue can be borrowed from.
4. **Flavors map workloads to hardware** — A `ResourceFlavor` is a tuple of `(nodeLabels, taints, tolerations)`. Quota is per-flavor. The same `cpu` resource can have separate quotas for `spot` and `ondemand` flavors, and `flavorFungibility` controls fall-through behavior.
5. **AdmissionChecks gate the final unsuspend** — Quota reservation is necessary but not sufficient. AdmissionChecks (e.g., MultiKueue, ProvisioningRequest) must all pass `Ready` before the Workload transitions to `Admitted` and the Job unsuspends.

## Quick-Start: Common Problems

### "My Job is created but no Pods appear"

1. Check the Job has the queue label: `kubectl get job <name> -o jsonpath='{.metadata.labels.kueue\.x-k8s\.io/queue-name}'`
2. Check the Workload exists: `kubectl get workload -l kueue.x-k8s.io/job-name=<job>`
3. Read Workload conditions: `kubectl describe workload <wl>` — look at `QuotaReserved`, `Admitted`, `Inadmissible` reasons
4. If `Inadmissible`: quota is full or no flavor matches the Pod's nodeSelector
5. If `QuotaReserved` but not `Admitted`: an AdmissionCheck is pending
-> See `references/operations-and-cli.md`

### "Which Kueue CRD do I create first?"

| Order | CRD | Created by |
|-------|-----|-----------|
| 1 | `ResourceFlavor` | Cluster admin |
| 2 | `ClusterQueue` (references flavors, sets quota, optional cohort) | Cluster admin |
| 3 | `LocalQueue` in tenant namespace (points to ClusterQueue) | Namespace admin |
| 4 | `WorkloadPriorityClass` (optional) | Cluster admin |
| 5 | `Job/RayJob/PyTorchJob` with `kueue.x-k8s.io/queue-name` label | User |
-> See `references/concepts-and-architecture.md`

### "My framework isn't being managed by Kueue"

1. Check it's enabled in Kueue Configuration: `kubectl -n kueue-system get cm kueue-manager-config -o yaml | grep frameworks`
2. Restart kueue-controller-manager after editing config: `kubectl -n kueue-system rollout restart deploy/kueue-controller-manager`
3. For pod integration: `pod` framework must be enabled AND `managedJobsNamespaceSelector` must match the Pod's namespace
4. For Deployment/StatefulSet: requires the `pod` integration + label `kueue.x-k8s.io/queue-name` on the Pod template
-> See `references/job-integrations.md`

### "How do I let Cluster Autoscaler scale up GPU nodes for queued workloads?"

1. Add an `AdmissionCheck` of kind `ProvisioningRequest` to the GPU ClusterQueue
2. Create a `ProvisioningRequestConfig` referencing the autoscaler's provisioning class (`check-capacity.autoscaling.x-k8s.io`, `queued-provisioning.gke.io`, or Karpenter's class)
3. Pending Workload triggers a ProvisioningRequest → autoscaler scales nodes → Workload admitted → Pods schedule
-> See `references/advanced-features.md`

### "I want fair sharing between teams"

1. Enable in Configuration: `fairSharing.enable: true`
2. Put team ClusterQueues in the same `cohort`
3. Set `fairSharing.weight` per ClusterQueue (default 1)
4. Choose `preemptionStrategies` (LessThanOrEqualToFinalShare for stable, LessThanInitialShare for aggressive)
-> See `references/advanced-features.md` and `references/quota-and-tenancy-patterns.md`

## Decision Trees

### Which Queueing Strategy?

| Signal | Strategy |
|--------|----------|
| Strict in-order admission (FIFO with head-of-line blocking acceptable) | `StrictFIFO` |
| Maximize throughput, allow later workloads to admit if head is blocked | `BestEffortFIFO` (default) |
| Need priority-based ordering | Add `WorkloadPriorityClass` to either |

### Which Preemption Policy?

| Goal | `withinClusterQueue` | `reclaimWithinCohort` |
|------|---------------------|----------------------|
| No preemption (hard isolation) | `Never` | `Never` |
| Higher priority preempts lower | `LowerPriority` | `LowerPriority` |
| Reclaim borrowed capacity | (own choice) | `Any` |
| Anything goes (research clusters) | `Any` | `Any` |

### Flavor Fungibility Behavior

| `whenCanBorrow` | `whenCanPreempt` | Behavior |
|----------------|-----------------|----------|
| `Borrow` | `TryNextFlavor` | Try borrowing in current flavor before falling through |
| `TryNextFlavor` | `TryNextFlavor` | Always try next flavor first (e.g., spot before on-demand) |
| `Borrow` | `Preempt` | Aggressive: borrow or preempt within current flavor before fallback |

### Single ClusterQueue or Many?

| Signal | Topology |
|--------|----------|
| Small team, one project | 1 ClusterQueue, no cohort |
| Multiple teams, want sharing | N ClusterQueues, same cohort, `borrowingLimit` set |
| Org → Department → Team hierarchy | Hierarchical Cohorts (parent/child) |
| Strict per-team isolation | N ClusterQueues, no cohort (or `borrowingLimit: 0`) |
| Multi-cluster federation | MultiKueue with management + worker clusters |

## Reference Index

| File | Contents |
|------|----------|
| `references/concepts-and-architecture.md` | Problem positioning, all CRDs (ResourceFlavor, ClusterQueue, LocalQueue, Workload, Cohort, AdmissionCheck, Topology, WorkloadPriorityClass), scheduling lifecycle (suspend → quota check → flavor assignment → admission check → unsuspend), controller architecture (reconcilers, in-memory cache, webhooks), resource model with borrowing/lending semantics, queueing strategies |
| `references/job-integrations.md` | Universal `kueue.x-k8s.io/queue-name` pattern, full `integrations.frameworks` enablement table, per-framework YAML for batch/v1 Job, JobSet, Kubeflow v1 (PyTorchJob/TFJob/MPIJob/XGBoostJob/PaddleJob/JAXJob), Kubeflow Trainer v2 (TrainJob), KubeRay (RayJob/RayCluster/RayService), AppWrapper, plain Pods (single + groups), Deployment/StatefulSet, LeaderWorkerSet, Spark, custom integrations |
| `references/installation-and-config.md` | kubectl apply / Helm OCI (`oci://registry.k8s.io/kueue/charts/kueue`) / Kustomize / GitOps install, full `Configuration` kind reference (manageJobsWithoutQueueName, managedJobsNamespaceSelector, integrations, multiKueue, fairSharing, waitForPodsReady, internalCertManagement, leaderElection), feature gates table by maturity, upgrade path, HA + cert-manager + ServiceMonitor production setup |
| `references/advanced-features.md` | Preemption (withinClusterQueue, reclaimWithinCohort, borrowWithinCohort), Fair Sharing (DRF, weights, preemption strategies, AdmissionFairSharing), MultiKueue (architecture, MultiKueueConfig/Cluster, dispatcherName, supported jobs), Topology-Aware Scheduling (Topology CRD, podset annotations, NCCL locality), ProvisioningRequest (Cluster Autoscaler + Karpenter integration), Hierarchical Cohorts, WorkloadPriorityClass, Partial Admission + Elastic Jobs (workload slices), waitForPodsReady gang scheduling, custom AdmissionCheckController pattern |
| `references/operations-and-cli.md` | Full `kueuectl` command surface (create/list/get/describe/stop/resume/delete/edit), Workload status interpretation (Pending/QuotaReserved/Admitted/Finished/Evicted + reasons), ClusterQueue status fields, Prometheus metrics catalog (kueue_pending_workloads, kueue_admission_attempt_duration_seconds, etc.), PromQL recipes, log diagnostics, troubleshooting trees for stuck/evicted/never-admitted workloads, performance tuning, drain/migrate procedures |
| `references/quota-and-tenancy-patterns.md` | Quota semantics (nominalQuota / borrowingLimit / lendingLimit / effectiveQuota), single-tenant pattern, multi-team patterns (equal-share with borrowing, tiered priority, reserved + shared pool, strict isolation), hierarchical cohort design, flavor patterns (spot+on-demand, GPU classes, cross-zone), preemption design, namespace selectors, RBAC, cost allocation, anti-patterns, safe migration playbook |
| `references/core-batch-ai-recipes.md` | End-to-end YAML recipes for basic batch queueing, multi-team GPU sharing with preemption, distributed PyTorch (Kubeflow), Ray hyperparameter tuning, spot+on-demand fallback, GPU autoscaling with ProvisioningRequest/Karpenter/Cluster Autoscaler, and MultiKueue federated dispatch |
| `references/operations-services-migration-recipes.md` | Production YAML recipes for MPI/HPC topology-aware scheduling, long-running Deployment quota, Argo/plain Pod queueing, AppWrapper gang admission, elastic jobs, CI/CD runner pools, online-vs-batch LLM inference, staged rollout, verification commands, and gotchas |
