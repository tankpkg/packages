# Core Batch, AI, and Federation Recipes

Sources: Kueue documentation tasks (kueue.sigs.k8s.io/docs/tasks/run/, /tasks/manage/), Google Cloud GKE Kueue tutorials, Karpenter + Kueue integration docs, KubeCon talks 2024-2025.

Covers: copy-paste recipes for basic batch queues, multi-team GPU sharing, Kubeflow PyTorch training, Ray hyperparameter tuning, spot+on-demand fallback, GPU autoscaling with ProvisioningRequest, and MultiKueue federation.

Each recipe states scenario, prerequisites, complete YAML, expected behavior, verification commands, and common gotchas.

## Recipe 1 — Basic batch queue

**Scenario**: 100 parallel batch Pods (4 CPU, 8Gi each), 200-CPU CQ. First 50 admit; the rest queue.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: default }
spec: {}
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: batch-cq }
spec:
  namespaceSelector: {}
  resourceGroups:
  - coveredResources: [cpu, memory]
    flavors:
    - name: default
      resources:
      - { name: cpu, nominalQuota: "200" }
      - { name: memory, nominalQuota: "400Gi" }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: default, namespace: default }
spec: { clusterQueue: batch-cq }
---
apiVersion: batch/v1
kind: Job
metadata:
  generateName: batch-
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  parallelism: 100
  completions: 100
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: w
        image: busybox
        command: [sh, -c, "sleep 300"]
        resources: { requests: { cpu: "4", memory: 8Gi } }
```

**Verify**: `kueuectl describe cq batch-cq` should show 50 admitted Pods and 1 pending Workload (the rest waiting because Job's PodSet is treated atomically — see partial admission to admit fewer Pods).

**Gotchas**: Without a `kueue.x-k8s.io/queue-name` label, the Job runs immediately, bypassing Kueue. Pod requests >`nominalQuota` → Workload Inadmissible forever.

## Recipe 2 — Multi-team GPU sharing with preemption

**Scenario**: Two teams sharing 8 GPUs in a cohort. Production preempts research when GPUs are full.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: gpu-a100 }
spec:
  nodeLabels: { accelerator: nvidia-a100 }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: prod-priority }
value: 1000
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata: { name: research-priority }
value: 100
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: shared-gpus }
spec: {}
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: prod-cq }
spec:
  cohort: shared-gpus
  namespaceSelector: { matchLabels: { team: prod } }
  preemption: { reclaimWithinCohort: Any, withinClusterQueue: LowerPriority }
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - name: gpu-a100
      resources: [{ name: "nvidia.com/gpu", nominalQuota: "4", borrowingLimit: "4" }]
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: research-cq }
spec:
  cohort: shared-gpus
  namespaceSelector: { matchLabels: { team: research } }
  preemption: { withinClusterQueue: LowerPriority }     # never preempts prod
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - name: gpu-a100
      resources: [{ name: "nvidia.com/gpu", nominalQuota: "4", borrowingLimit: "4" }]
---
# Submit prod Job (preempts research if needed)
apiVersion: batch/v1
kind: Job
metadata:
  name: prod-inference
  namespace: prod-ns
  labels:
    kueue.x-k8s.io/queue-name: default
    kueue.x-k8s.io/priority-class: prod-priority
spec:
  parallelism: 4
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: c
        image: nvidia/cuda:12.0-runtime
        resources: { requests: { "nvidia.com/gpu": "1" } }
```

**Verify**: When the prod Job is submitted while research is using all 8 GPUs, watch `kueuectl describe workload <research>` — it should transition to `Evicted=True, reason=Preempted`. The prod Workload then admits.

**Gotchas**: Cohort name typo → no sharing. Forgetting `reclaimWithinCohort: Any` on prod-cq → prod can't take GPUs from research.

## Recipe 3 — Distributed PyTorch training (Kubeflow)

**Scenario**: 1 master + 3 workers, gang scheduled, requeued on failure.

```yaml
# (assumes ResourceFlavor "default" + ClusterQueue "ml-cq" with 4 GPU nominal exist)
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: default, namespace: default }
spec: { clusterQueue: ml-cq }
---
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-train
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0-cuda12.0-runtime
            resources: { requests: { "nvidia.com/gpu": "1" } }
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0-cuda12.0-runtime
            resources: { requests: { "nvidia.com/gpu": "1" } }
```

Pair with `Configuration.waitForPodsReady.enable: true` and `timeout: 10m` so the whole job is requeued if not all 4 Pods come up within the window.

**Verify**: `kueuectl describe workload pytorch-train` shows two PodSets (Master + Worker) and `Admitted=True` + `PodsReady=True`.

**Gotchas**: `PyTorchJob` needs Kueue's `kubeflow.org/pytorchjob` integration enabled. Master and Worker count toward the same Workload's quota — sum the GPUs.

## Recipe 4 — Ray hyperparameter tuning with elastic scaling

**Scenario**: RayJob head + autoscaling worker group, treated as elastic Workload.

```yaml
# Enable feature gate first: ElasticJobsViaWorkloadSlices=true
apiVersion: ray.io/v1
kind: RayJob
metadata:
  name: hp-tune
  labels: { kueue.x-k8s.io/queue-name: default }
  annotations: { kueue.x-k8s.io/elastic-job: "true" }
spec:
  shutdownAfterJobFinishes: true
  entrypoint: python /home/ray/tune.py
  rayClusterSpec:
    rayVersion: '2.10.0'
    enableInTreeAutoscaling: true
    autoscalerOptions: { idleTimeoutSeconds: 30, upscalingMode: Aggressive }
    headGroupSpec:
      rayStartParams: { dashboard-host: '0.0.0.0' }
      template:
        spec:
          containers:
          - { name: ray-head, image: rayproject/ray:2.10.0, resources: { requests: { cpu: "4" } } }
    workerGroupSpecs:
    - groupName: workers
      replicas: 1
      minReplicas: 1
      maxReplicas: 5
      template:
        spec:
          containers:
          - { name: ray-worker, image: rayproject/ray:2.10.0, resources: { requests: { cpu: "2" } } }
```

**Verify**: As Ray's autoscaler grows the worker group, you'll see new Workload slices and the old slice marked `Finished`. `kueuectl get workload` lists them.

**Gotchas**: Without `ElasticJobsViaWorkloadSlices` feature gate, the Workload is static at the initial replicas. Without `shutdownAfterJobFinishes: true`, Kueue rejects RayJob.

## Recipe 5 — Spot + on-demand fallback

**Scenario**: Workloads admit on spot first; fall through to on-demand when spot is exhausted.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: spot }
spec:
  nodeLabels: { capacity-type: spot }
  tolerations: [{ key: spot, operator: Equal, value: "true", effect: NoSchedule }]
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: ondemand }
spec:
  nodeLabels: { capacity-type: on-demand }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: cost-optimized }
spec:
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: spot,     resources: [{ name: cpu, nominalQuota: "100" }] }
    - { name: ondemand, resources: [{ name: cpu, nominalQuota: "50" }] }
  flavorFungibility:
    whenCanBorrow: TryNextFlavor          # do not borrow more spot — go to on-demand
    whenCanPreempt: TryNextFlavor
```

Workloads with `tolerations: [{key: spot}]` admit on spot first. Workloads without that toleration skip the spot flavor (its NoSchedule taint excludes them).

**Gotchas**: Without the toleration in the ResourceFlavor, Kueue won't inject it and Pods can't land on tainted spot nodes. Without `flavorFungibility.whenCanBorrow: TryNextFlavor`, Kueue would borrow more spot from the cohort instead of falling through to on-demand.

## Recipe 6 — GPU job with Karpenter / Cluster Autoscaler (ProvisioningRequest)

**Scenario**: GPU Workload pending → ProvisioningRequest created → Karpenter scales up GPU node → Workload admits.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: gpu-h100 }
spec:
  nodeLabels: { accelerator: nvidia-h100 }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ProvisioningRequestConfig
metadata: { name: gpu-prov }
spec:
  provisioningClassName: check-capacity.autoscaling.x-k8s.io   # generic CA class; or karpenter.sh/<class>
  managedResources: ["nvidia.com/gpu"]
  retryStrategy: { backoffLimitCount: 3, backoffBaseSeconds: 60, backoffMaxSeconds: 1800 }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: AdmissionCheck
metadata: { name: gpu-provision }
spec:
  controllerName: kueue.x-k8s.io/provisioning-request
  parameters: { apiGroup: kueue.x-k8s.io, kind: ProvisioningRequestConfig, name: gpu-prov }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: gpu-cq }
spec:
  admissionChecks: [gpu-provision]
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - { name: gpu-h100, resources: [{ name: "nvidia.com/gpu", nominalQuota: "8" }] }
---
apiVersion: batch/v1
kind: Job
metadata:
  generateName: gpu-train-
  labels: { kueue.x-k8s.io/queue-name: default }
spec:
  parallelism: 8
  template:
    spec:
      restartPolicy: Never
      nodeSelector: { accelerator: nvidia-h100 }
      containers:
      - name: trainer
        image: nvidia/cuda:12.0-runtime
        resources: { requests: { "nvidia.com/gpu": "1" } }
```

**Verify**: `kubectl get provisioningrequest -A` shows a request created when the Workload is submitted. After Karpenter or CA provisions nodes, the AdmissionCheck transitions to Ready and the Workload admits.

**Gotchas**: Wrong `provisioningClassName` → no autoscaler picks up the request. Workload Pods need the same nodeSelector as ResourceFlavor's `nodeLabels`.

## Recipe 7 — Multi-cluster federation with MultiKueue

**Scenario**: One management cluster, two worker clusters. Job submitted on management is dispatched to least-loaded worker.

On the **management cluster** (after creating kubeconfig secrets `worker1-kubeconfig` and `worker2-kubeconfig`):

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: MultiKueueCluster
metadata: { name: worker1 }
spec: { kubeConfig: { locationType: Secret, location: worker1-kubeconfig } }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: MultiKueueCluster
metadata: { name: worker2 }
spec: { kubeConfig: { locationType: Secret, location: worker2-kubeconfig } }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: MultiKueueConfig
metadata: { name: federation }
spec: { clusters: [worker1, worker2] }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: AdmissionCheck
metadata: { name: federate }
spec:
  controllerName: kueue.x-k8s.io/multikueue
  parameters: { apiGroup: kueue.x-k8s.io, kind: MultiKueueConfig, name: federation }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: federated-cq }
spec:
  admissionChecks: [federate]
  resourceGroups:
  - coveredResources: [cpu]
    flavors: [{ name: default, resources: [{ name: cpu, nominalQuota: "1000" }] }]
```

Each worker cluster needs Kueue installed and a ClusterQueue named the same way (`federated-cq`).

**Gotchas**: Worker secret must live in `kueue-system`. The management cluster cannot also be a worker. For batch/v1 Jobs the management Job needs `spec.managedBy: kueue.x-k8s.io/multikueue`.

## Sources

- https://kueue.sigs.k8s.io/docs/tasks/run/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_provisioning_request/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_multikueue/
- https://kueue.sigs.k8s.io/docs/tasks/run/rayjobs/
- https://kueue.sigs.k8s.io/docs/tasks/run/kubeflow/
- https://github.com/kubernetes-sigs/kueue/tree/main/examples
