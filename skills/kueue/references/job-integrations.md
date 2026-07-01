# Job Integrations

Sources: Kueue official documentation (kueue.sigs.k8s.io/docs/tasks/run/), Kueue Configuration v1beta1/v1beta2 reference, Kubeflow Training Operator docs, KubeRay docs, JobSet spec, AppWrapper (CodeFlare) docs.

Covers: The universal `queue-name` label pattern, the `integrations.frameworks` enablement table, per-framework wiring (batch Job, JobSet, Kubeflow v1/v2, KubeRay, AppWrapper, plain Pods, Deployment, StatefulSet, LeaderWorkerSet, Spark), the suspend → admit → unsuspend lifecycle, common failure modes, and writing a custom integration.

## The Universal Pattern

Every Kueue-managed workload follows the same shape:

1. **User adds the queue-name label** — `kueue.x-k8s.io/queue-name: <local-queue>` on the workload's `metadata.labels`
2. **Kueue's framework-specific webhook suspends it** — sets `spec.suspend: true` (Job-like) or injects a scheduling gate (Pods)
3. **Kueue's framework reconciler creates a Workload** — one per parent object, with `podSets[]` derived from the parent's replica spec
4. **Workload waits in the queue** — until quota reservation + admission checks succeed
5. **Kueue unsuspends** — clears `spec.suspend` (Job-like) or removes the scheduling gate (Pods); injects flavor tolerations into Pod templates
6. **Pods schedule and run** — kube-scheduler binds them; Kueue tracks completion via the parent's status

**The first thing to check when a workload behaves wrong is always: did Kueue suspend it?** `kubectl get <kind> <name> -o jsonpath='{.spec.suspend}'`. If empty/false on a freshly created workload, the integration isn't wired up.

## Enablement Table (per Kueue version)

| Framework | `integrations.frameworks` string | Since | Suspend mechanism | Notes |
|-----------|---------------------------------|-------|------------------|-------|
| Kubernetes Job | `batch/job` | v0.1 | `spec.suspend` | The canonical case |
| JobSet | `jobset.x-k8s.io/jobset` | v0.6 | `spec.suspend` | Multi-job groups |
| Kubeflow PyTorchJob | `kubeflow.org/pytorchjob` | v0.3 | `spec.suspend` | Master + Workers |
| Kubeflow TFJob | `kubeflow.org/tfjob` | v0.3 | `spec.suspend` | PS + Worker |
| Kubeflow XGBoostJob | `kubeflow.org/xgboostjob` | v0.5 | `spec.suspend` | |
| Kubeflow PaddleJob | `kubeflow.org/paddlejob` | v0.5 | `spec.suspend` | |
| Kubeflow JAXJob | `kubeflow.org/jaxjob` | v0.13 | `spec.suspend` | |
| Kubeflow MPIJob (v2beta1) | `kubeflow.org/mpijob` | v0.3 | `spec.suspend` | HPC tightly-coupled |
| Kubeflow Trainer v2 TrainJob | `trainer.kubeflow.org/trainjob` | v0.14 | `spec.suspend` | Unified training API |
| KubeRay RayJob | `ray.io/rayjob` | v0.6 | `spec.suspend` | Requires `shutdownAfterJobFinishes: true` |
| KubeRay RayCluster | `ray.io/raycluster` | v0.6 | `spec.suspend` | Long-running Ray cluster |
| KubeRay RayService | `ray.io/rayservice` | v0.6 | `spec.suspend` | |
| AppWrapper | `workload.codeflare.dev/appwrapper` | v0.11 | Workload-level | Wraps any resource |
| Plain Pod | `pod` | v0.8 | Scheduling gate | Requires namespace selector |
| Deployment | `deployment` | v0.8 | Pod-level (rolling) | Requires namespace selector |
| StatefulSet | `statefulset` | v0.8 | Pod-level | Requires namespace selector |
| LeaderWorkerSet | `leaderworkerset.x-k8s.io/leaderworkerset` | v0.15 | `spec.suspend` | Distributed leader/worker |
| Spark SparkApplication | `sparkoperator.k8s.io/sparkapplication` | v0.14 | `spec.suspend` | |

The exact string format may include version suffixes (e.g., `batch/job.v1`) depending on Kueue version — check `kubectl get crd <crd> -o yaml` for the current admission webhook config or run `kubectl -n kueue-system describe deploy/kueue-controller-manager`.

## Enabling Integrations in Configuration

```yaml
apiVersion: config.kueue.x-k8s.io/v1beta1
kind: Configuration
integrations:
  frameworks:
  - "batch/job"
  - "jobset.x-k8s.io/jobset"
  - "kubeflow.org/pytorchjob"
  - "kubeflow.org/mpijob"
  - "ray.io/rayjob"
  - "ray.io/raycluster"
  - "workload.codeflare.dev/appwrapper"
  - "pod"
  - "deployment"
  - "statefulset"
  - "leaderworkerset.x-k8s.io/leaderworkerset"
  externalFrameworks: []                  # for custom integrations
  podOptions:
    namespaceSelector:                    # required when "pod" is enabled
      matchExpressions:
      - key: kubernetes.io/metadata.name
        operator: NotIn
        values: [kube-system, kueue-system]
managedJobsNamespaceSelector:             # gates ALL Pod-derived integrations
  matchLabels: { kueue-managed: "true" }
```

After editing the ConfigMap, restart the controller: `kubectl -n kueue-system rollout restart deploy/kueue-controller-manager`. Webhooks re-register on startup.

## Per-Framework Recipes

### batch/v1 Job

The simplest case. Every other integration is a variant of this pattern.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  generateName: trainer-
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  parallelism: 4
  completions: 4
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: trainer
        image: alpine:3
        command: ["sh", "-c", "sleep 60"]
        resources:
          requests: { cpu: "1", memory: 200Mi }
```

**Optional annotations**:

| Annotation | Effect |
|-----------|--------|
| `kueue.x-k8s.io/job-min-parallelism: "5"` | Allow partial admission down to 5 of N parallelism |
| `kueue.x-k8s.io/elastic-job: "true"` | Allow scaling parallelism without restart (with workload slices) |
| `kueue.x-k8s.io/priority-class: <name>` | Use a Workload-level priority (not Pod priority) |
| `kueue.x-k8s.io/max-exec-time-seconds: "3600"` | Auto-deactivate after 1 hour of running |

### JobSet

Coordinates multiple replicated Jobs as a single quota unit. Resource calculation: Σ over `replicatedJobs[].replicas * .template.spec.parallelism * pod_request`.

```yaml
apiVersion: jobset.x-k8s.io/v1alpha2
kind: JobSet
metadata:
  generateName: training-
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  network: { enableDNSHostnames: true }
  replicatedJobs:
  - name: workers
    replicas: 4
    template:
      spec:
        parallelism: 1
        template:
          spec:
            restartPolicy: Never
            containers:
            - name: worker
              image: trainer:1.0
              resources: { requests: { cpu: "2", memory: 4Gi, "nvidia.com/gpu": "1" } }
```

### Kubeflow Trainer v1 — PyTorchJob (and TFJob, MPIJob, etc.)

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: distributed-training
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7
            resources: { requests: { cpu: "4", memory: 16Gi, "nvidia.com/gpu": "1" } }
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7
            resources: { requests: { cpu: "4", memory: 16Gi, "nvidia.com/gpu": "1" } }
```

`TFJob`, `XGBoostJob`, `PaddleJob`, `JAXJob`, `MPIJob` all follow the same shape — their replica spec maps to PodSets in the Workload, and Kueue computes total resources by summing across all replica types. For MPIJob, the launcher and worker spec form two PodSets.

### Kubeflow Trainer v2 — TrainJob

The v2 unified API. One CRD for all training frameworks; the algorithm is configured via `trainingRuntime`.

```yaml
apiVersion: trainer.kubeflow.org/v1alpha1
kind: TrainJob
metadata:
  name: pytorch-train
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  runtimeRef:
    name: pytorch-distributed
    apiGroup: trainer.kubeflow.org
    kind: ClusterTrainingRuntime
  trainer:
    numNodes: 4
    resourcesPerNode:
      requests: { cpu: "8", memory: 32Gi, "nvidia.com/gpu": "2" }
```

### KubeRay — RayJob

```yaml
apiVersion: ray.io/v1
kind: RayJob
metadata:
  name: ray-batch
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  shutdownAfterJobFinishes: true            # required for Kueue
  entrypoint: python /home/ray/script.py
  rayClusterSpec:
    rayVersion: '2.10.0'
    headGroupSpec:
      rayStartParams: { dashboard-host: '0.0.0.0' }
      template:
        spec:
          containers:
          - name: ray-head
            image: rayproject/ray:2.10.0
            resources: { requests: { cpu: "1", memory: 2Gi } }
    workerGroupSpecs:
    - groupName: default
      replicas: 4
      minReplicas: 4
      maxReplicas: 4
      template:
        spec:
          containers:
          - name: ray-worker
            image: rayproject/ray:2.10.0
            resources: { requests: { cpu: "4", memory: 8Gi, "nvidia.com/gpu": "1" } }
```

**RayJob limitations**: must be self-contained (creates its own RayCluster); cannot reference an external RayCluster. Maximum 7 worker groups (one PodSet for head + 7 = the Workload PodSet limit of 8).

**RayCluster** (long-running) and **RayService** follow the same suspend/unsuspend pattern but represent persistent allocations.

### AppWrapper — gang-admission for arbitrary workloads

When you need quota gating for a non-natively-supported resource, wrap it in an AppWrapper.

```yaml
apiVersion: workload.codeflare.dev/v1beta2
kind: AppWrapper
metadata:
  name: wrapped-pytorch
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  components:
  - template:
      apiVersion: kubeflow.org/v1
      kind: PyTorchJob
      metadata: { name: inner }
      spec:
        pytorchReplicaSpecs:
          Master: { replicas: 1, template: { spec: { containers: [{ name: m, image: pytorch/pytorch, resources: { requests: { cpu: "1" } } }] } } }
          Worker: { replicas: 3, template: { spec: { containers: [{ name: w, image: pytorch/pytorch, resources: { requests: { cpu: "1" } } }] } } }
```

The AppWrapper controller (CodeFlare) creates inner resources only after Kueue admits the wrapper. Useful for gang-admitting *combinations* of resources that would otherwise admit independently.

### Plain Pods

Two flavors: single Pod, and pod groups (gang). Both require `pod` in `integrations.frameworks` and a non-empty `managedJobsNamespaceSelector` so system Pods aren't queued.

```yaml
# single Pod
apiVersion: v1
kind: Pod
metadata:
  generateName: oneshot-
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  restartPolicy: OnFailure
  containers:
  - name: c
    image: busybox
    command: ["sleep", "30"]
    resources: { requests: { cpu: "2" } }
```

Pod groups (multiple Pods admitted together):

```yaml
apiVersion: v1
kind: Pod
metadata:
  generateName: gang-leader-
  labels:
    kueue.x-k8s.io/queue-name: team-a-queue
    kueue.x-k8s.io/pod-group-name: gang-1
  annotations:
    kueue.x-k8s.io/pod-group-total-count: "3"
    kueue.x-k8s.io/retriable-in-group: "false"   # so failed pods don't waste quota
spec:
  containers: [{ name: c, image: busybox, command: ["sleep","60"], resources: { requests: { cpu: "1" } } }]
  restartPolicy: Never
# ... two more Pods with same pod-group-name and total-count=3
```

All Pods in a group must carry the same `pod-group-name` and `pod-group-total-count`. The group is admitted as one Workload; it's complete when all member Pods finish.

### Deployment and StatefulSet

Treats the Deployment/StatefulSet's Pod template as a queueable unit, useful when you want quota for long-running services.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-server
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  replicas: 3
  selector: { matchLabels: { app: inference } }
  template:
    metadata:
      labels: { app: inference }
    spec:
      containers:
      - name: server
        image: my-inference:1.0
        resources: { requests: { cpu: "2", memory: 4Gi, "nvidia.com/gpu": "1" } }
```

The label can also be applied to the Pod template; the Deployment integration is built on top of the `pod` integration. Quota is checked per-Pod, so scaling the Deployment up requests more quota.

### LeaderWorkerSet

For distributed inference / fine-tuning where leader and worker Pods differ.

```yaml
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: lws-train
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  replicas: 2                               # 2 leader-worker groups
  leaderWorkerTemplate:
    size: 4                                 # 1 leader + 3 workers per group
    leaderTemplate:
      spec:
        containers:
        - { name: leader, image: trainer, resources: { requests: { cpu: "4", "nvidia.com/gpu": "1" } } }
    workerTemplate:
      spec:
        containers:
        - { name: worker, image: trainer, resources: { requests: { cpu: "4", "nvidia.com/gpu": "1" } } }
```

Total quota = `replicas × size × per-Pod request`. All groups admit together.

### Spark — SparkApplication

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: pi
  labels: { kueue.x-k8s.io/queue-name: team-a-queue }
spec:
  type: Scala
  mode: cluster
  image: spark:3.5
  mainClass: org.apache.spark.examples.SparkPi
  mainApplicationFile: local:///opt/spark/examples/jars/spark-examples.jar
  driver:   { cores: 1, memory: "1g" }
  executor: { cores: 2, memory: "2g", instances: 4 }
```

Driver and executor become two PodSets.

## Common Mistakes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Job runs immediately, no Workload created | Missing `kueue.x-k8s.io/queue-name` label | Add label to `metadata.labels` |
| Workload created, stays Pending forever | Quota too low or no flavor matches Pod nodeSelector | `kueuectl describe workload` to read NoFit reason |
| `kubectl get workload` returns nothing | Framework not in `integrations.frameworks` list | Add string and restart kueue-controller-manager |
| System pods getting queued | `pod` integration enabled with permissive `managedJobsNamespaceSelector` | Tighten the selector to opt-in namespaces only |
| Pod group: pods admit individually | Annotation `pod-group-total-count` missing or mismatched | All members must have the same total-count and group-name |
| RayJob never admits | Missing `shutdownAfterJobFinishes: true` | Set it; Kueue requires self-cleanup |
| Job unsuspended without admission | Webhook not running (cert-manager issue) | Check `kubectl -n kueue-system get pods` and webhook configuration |
| Deployment stays at 0 replicas | Pod-level Workload not created because namespace not in `managedJobsNamespaceSelector` | Label the namespace |
| `MaxPodSets` exceeded error | Workload has > 8 PodSets (e.g., RayCluster with 8 workergroups) | Reduce worker groups to ≤7 (head + 7 = 8) |
| MPIJob with launcher Pod outside Kueue control | Launcher uses `restartPolicy: OnFailure`, can't be suspended cleanly | Use Job mode for launcher (`launcherCreationPolicy: WaitForWorkersReady`) |

## Lifecycle Summary

For Job-like APIs:

```
[user creates Job with queue-name label]
         │
         ▼
Mutating webhook sets spec.suspend=true
         │
         ▼
Job reconciler creates Workload (status: Pending)
         │
         ▼
Workload reconciler reserves quota → QuotaReserved
         │
         ▼
Admission checks evaluated → Admitted
         │
         ▼
Job reconciler patches spec.suspend=false (and injects flavor tolerations)
         │
         ▼
kube-scheduler binds Pods → Pods run
         │
         ▼
Job completes → Workload Finished, quota released
```

For Pod integration: replace "spec.suspend=true" with "scheduling gate `kueue.x-k8s.io/admission` injected" and "patches spec.suspend=false" with "removes scheduling gate".

## Custom Integrations

For workload types not on the table, two paths:

**Path 1: AppWrapper.** Wrap your custom resource in an AppWrapper. No code; Kueue treats the wrapper as the queueing unit.

**Path 2: Implement an integration.** Write a controller that:
1. Watches your custom resource
2. Suspends it on creation (whatever your resource's "don't run yet" semantics are)
3. Creates a Workload with `podSets[]` reflecting your resource's pod requirements
4. Watches the Workload — when `Admitted=True`, unsuspend
5. Reports completion / failure to the Workload

Register the type via `integrations.externalFrameworks`. The Kueue codebase has a tutorial `site/content/en/docs/tasks/dev/integrate_a_custom_job/` and the in-tree integrations under `pkg/controller/jobs/` are the best reference implementation.

## Sources

- https://kueue.sigs.k8s.io/docs/tasks/run/
- https://kueue.sigs.k8s.io/docs/tasks/run/jobs/
- https://kueue.sigs.k8s.io/docs/tasks/run/jobsets/
- https://kueue.sigs.k8s.io/docs/tasks/run/kubeflow/
- https://kueue.sigs.k8s.io/docs/tasks/run/rayjobs/
- https://kueue.sigs.k8s.io/docs/tasks/run/rayclusters/
- https://kueue.sigs.k8s.io/docs/tasks/run/plain_pods/
- https://kueue.sigs.k8s.io/docs/tasks/run/deployment/
- https://kueue.sigs.k8s.io/docs/tasks/run/statefulset/
- https://kueue.sigs.k8s.io/docs/tasks/run/appwrappers/
- https://kueue.sigs.k8s.io/docs/tasks/run/leaderworkerset/
- https://kueue.sigs.k8s.io/docs/reference/kueue-config.v1beta1/
- https://github.com/kubernetes-sigs/kueue/tree/main/pkg/controller/jobs
