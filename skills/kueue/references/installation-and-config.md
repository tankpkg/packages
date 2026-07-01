# Installation and Configuration

Sources: Kueue official documentation (kueue.sigs.k8s.io/docs/installation/, /docs/reference/kueue-config.v1beta1/), kubernetes-sigs/kueue Helm chart, GitHub releases, KEPs for feature gates.

Covers: Install methods (kubectl, Helm OCI, Kustomize, GitOps), the `Configuration` kind reference, the feature-gate matrix, upgrade procedure, production hardening (HA, cert-manager, ServiceMonitor, PriorityClass, PDB), and a starter multi-tenant manifest.

## Install Methods

### kubectl apply (release manifests)

The fastest path. One file, no extra tooling.

```bash
KUEUE_VERSION=v0.14.0
kubectl apply --server-side -f \
  https://github.com/kubernetes-sigs/kueue/releases/download/${KUEUE_VERSION}/manifests.yaml

kubectl -n kueue-system wait deploy/kueue-controller-manager \
  --for=condition=Available --timeout=5m
```

`--server-side` is required because Kueue's CRDs are large and trip the client-side `Last-Applied-Configuration` annotation size limit.

**Prerequisites**: Kubernetes 1.29+. cert-manager only if you plan to disable Kueue's internal cert management.

### Helm chart (OCI)

The recommended production path. Chart lives in OCI registry `oci://registry.k8s.io/kueue/charts/kueue`.

```bash
helm install kueue oci://registry.k8s.io/kueue/charts/kueue \
  --version 0.14.0 \
  --namespace kueue-system \
  --create-namespace \
  --values values.yaml \
  --wait --timeout 5m
```

Minimal production `values.yaml`:

```yaml
controllerManager:
  replicas: 2
  manager:
    resources:
      requests: { cpu: "1", memory: 1Gi }
      limits:   { cpu: "2", memory: 2Gi }
    priorityClassName: system-cluster-critical
  podDisruptionBudget:
    enabled: true
    minAvailable: 1
  featureGates:
  - name: TopologyAwareScheduling
    enabled: true
  - name: MultiKueue
    enabled: true

enableCertManager: false      # use Kueue's internal cert management
enablePrometheus: true        # creates ServiceMonitor

managerConfig:                # injected into kueue-manager-config ConfigMap
  manageJobsWithoutQueueName: false
  integrations:
    frameworks:
    - "batch/job"
    - "kubeflow.org/pytorchjob"
    - "ray.io/rayjob"
```

### Kustomize from source

For developers and CI:

```bash
git clone https://github.com/kubernetes-sigs/kueue.git
cd kueue && git checkout v0.14.0
kubectl apply --server-side -k config/default
```

The `config/default` overlay enables internal cert management and standard feature gates. Customize via your own overlay.

### GitOps (ArgoCD)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: kueue, namespace: argocd }
spec:
  project: default
  destination: { server: https://kubernetes.default.svc, namespace: kueue-system }
  source:
    repoURL: https://github.com/kubernetes-sigs/kueue
    targetRevision: v0.14.0
    path: charts/kueue
    helm:
      valueFiles: [values.yaml]
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=true, ServerSideApply=true]
```

Pin `targetRevision` to a tag, never `main`. CRDs change between releases and ArgoCD can't safely auto-upgrade them without `ServerSideApply=true`.

## The Configuration Kind

Kueue's runtime configuration lives in a ConfigMap (`kueue-manager-config` in `kueue-system`) holding a serialized `Configuration` object (`config.kueue.x-k8s.io/v1beta1`, with `v1beta2` rolling out).

Edit, then restart the controller: `kubectl -n kueue-system rollout restart deploy/kueue-controller-manager`.

```yaml
apiVersion: config.kueue.x-k8s.io/v1beta1
kind: Configuration
namespace: kueue-system

# --- core controller plumbing ---
controller:
  groupKindConcurrency:
    Workload.kueue.x-k8s.io: 10
    ClusterQueue.kueue.x-k8s.io: 5
    LocalQueue.kueue.x-k8s.io: 5
  cacheSyncTimeout: 2m

clientConnection:
  qps: 100
  burst: 200

leaderElection:
  leaderElect: true
  resourceName: c1f6bfd2.kueue.x-k8s.io
  resourceNamespace: kueue-system

# --- network endpoints ---
metrics:
  bindAddress: ":8443"
  enableClusterQueueResources: true
health:
  healthProbeBindAddress: ":8081"
webhook:
  port: 9443

# --- TLS for webhooks ---
internalCertManagement:
  enable: true                                # Kueue self-signs
  webhookServiceName: kueue-webhook-service
  webhookSecretName: kueue-webhook-server-cert

# --- which jobs Kueue manages ---
manageJobsWithoutQueueName: false             # if true, ALL jobs without label are queued
managedJobsNamespaceSelector:
  matchLabels:
    kueue.x-k8s.io/managed: "true"
integrations:
  frameworks:
  - "batch/job"
  - "kubeflow.org/pytorchjob"
  - "kubeflow.org/mpijob"
  - "jobset.x-k8s.io/jobset"
  - "ray.io/rayjob"
  - "pod"
  - "deployment"
  podOptions:
    namespaceSelector:
      matchExpressions:
      - { key: kubernetes.io/metadata.name, operator: NotIn, values: [kube-system, kueue-system] }

# --- gang scheduling ---
waitForPodsReady:
  enable: true
  timeout: 10m
  blockAdmission: true
  requeuingStrategy:
    timestamp: Eviction
    backoffLimitCount: 5
    backoffBaseSeconds: 60

# --- fair sharing ---
fairSharing:
  enable: true
  preemptionStrategies: [LessThanOrEqualToFinalShare]
admissionFairSharing:
  usageHalfLifeTime: 15m
  usageSamplingInterval: 5m
  resourceWeights:
    cpu: 1
    memory: 1
    "nvidia.com/gpu": 100

# --- multi-cluster ---
multiKueue:
  gcInterval: 1h
  origin: management-cluster

# --- garbage collection ---
objectRetentionPolicies:
  workloads:
    finalStateInactiveTTL: 24h

# --- resource transformations / DRA ---
resources:
  excludeResourcePrefixes: ["pod-overhead.kueue.x-k8s.io"]
  transformations:
  - input: "memory-fraction"
    strategy: Replace
    outputs:
      memory: "8Gi"

# --- experimental features ---
featureGates:
  TopologyAwareScheduling: true
  ElasticJobsViaWorkloadSlices: true
```

### Key fields

| Field | Effect |
|-------|--------|
| `manageJobsWithoutQueueName` | If `true`, *every* unsuspended Job is wrapped by Kueue. Dangerous on existing clusters — start with `false` and label opt-in jobs |
| `managedJobsNamespaceSelector` | Restricts the above to namespaces matching the selector. **Required** when any Pod-derived integration (`pod`, `deployment`, `statefulset`) is enabled |
| `integrations.frameworks` | Enables specific Job-controller integrations. Restart required after change |
| `integrations.podOptions.namespaceSelector` | Specifically scopes the `pod` integration's webhook |
| `internalCertManagement.enable: true` | Kueue self-signs the webhook serving cert. Set to `false` to use cert-manager |
| `clientConnection.qps`/`burst` | API server rate limiting. Raise for clusters with thousands of Workloads |
| `waitForPodsReady` | All-or-nothing scheduling. See `advanced-features.md` for details |
| `fairSharing.enable` | Enables DRF-style fair sharing among ClusterQueues in a cohort |
| `multiKueue.gcInterval` | How often the controller GCs orphaned remote Workloads |
| `objectRetentionPolicies.workloads.finalStateInactiveTTL` | Auto-delete completed Workloads after this duration |
| `featureGates` | Per-feature on/off, see table below |

## Feature Gates

Feature gates change frequently. The table below reflects v0.14 (May 2026); always check the current `keps/` directory in the kueue repo and the release notes for accurate state.

| Gate | Default | Stage | Since | What it does |
|------|---------|-------|-------|--------------|
| `FlavorFungibility` | true | Beta | 0.5 | Try multiple flavors per resourceGroup |
| `PartialAdmission` | true | Beta | 0.5 | Admit Jobs with fewer Pods than requested via `job-min-parallelism` |
| `MultiKueue` | true | Beta | 0.9 | Federated multi-cluster job dispatch |
| `MultiKueueBatchJobWithManagedBy` | true | GA | 0.13 | batch/v1 Job support in MultiKueue via `managedBy` |
| `VisibilityOnDemand` | true | Beta | 0.9 | On-demand visibility API for pending Workloads |
| `TopologyAwareScheduling` | true | Beta | 0.10 | Rack/zone/host topology placement |
| `LendingLimit` | true | GA | 0.13 | `lendingLimit` field on ClusterQueue resource quota |
| `LocalQueueDefaulting` | true | Beta | 0.13 | Auto-create `default` LocalQueue per managed namespace |
| `ObjectRetentionPolicies` | true | Beta | 0.13 | Auto-delete finished Workloads |
| `HierarchicalCohort` | true | Beta | 0.12 | Parent/child Cohort hierarchy |
| `AdmissionFairSharing` | true | Beta | 0.13 | Per-namespace fair share within a ClusterQueue |
| `AdmissionCheckValidationRules` | true | Beta | 0.13 | CEL validation on AdmissionCheck params |
| `ConfigurableResourceTransformations` | true | Beta | 0.13 | The `resources.transformations` field |
| `ManagedJobsNamespaceSelector` | true | GA | 0.13 | Honor `managedJobsNamespaceSelector` everywhere |
| `ElasticJobsViaWorkloadSlices` | false | Alpha | 0.14 | Workload slicing for elastic Jobs |
| `DynamicResourceAllocation` | false | Alpha | 0.13 | DRA device support in podSets |
| `TASBalancedPlacement` | false | Alpha | 0.13 | Balanced spread across topology domains |
| `FailureRecoveryPolicy` | false | Alpha | 0.13 | Auto-requeue on Pod failure |
| `LocalQueueMetrics` | false | Alpha | 0.10 | Per-LocalQueue metrics (high cardinality) |
| `AdmissionGatedBy` | false | Alpha | 0.14 | Custom external admission gates |

Set in Configuration:

```yaml
featureGates:
  TopologyAwareScheduling: true
  ElasticJobsViaWorkloadSlices: true
```

Or via container args:

```yaml
controllerManager:
  manager:
    extraArgs:
    - --feature-gates=TopologyAwareScheduling=true,ElasticJobsViaWorkloadSlices=true
```

## Upgrade Path

| Direction | Allowed | Notes |
|-----------|---------|-------|
| Patch upgrade (0.14.1 → 0.14.2) | Always | Bug fixes only |
| Minor upgrade (0.13 → 0.14) | One step at a time | Read EVERY release note between current and target |
| Skip-version upgrade | Not supported | Walk through each minor |
| Downgrade | Not supported | Backup CRDs, reinstall older version, restore objects |

Sample procedure:

```bash
# 1. Backup quota objects
kubectl get -A clusterqueues,localqueues,resourceflavors,cohorts,admissionchecks \
  -o yaml > kueue-backup.yaml

# 2. Helm upgrade
helm upgrade kueue oci://registry.k8s.io/kueue/charts/kueue \
  --version 0.14.0 -n kueue-system -f values.yaml --wait

# 3. Validate
kubectl -n kueue-system rollout status deploy/kueue-controller-manager
kubectl get clusterqueues
kueuectl version
```

Common breaking changes to watch for: deprecated feature gates being removed, deprecated config fields (e.g., legacy `queueVisibility` → `VisibilityOnDemand`), CRD schema tightening (validation that previously was lenient).

## Production Hardening

### Resource Sizing

| Cluster size | replicas | requests | limits |
|-------------|----------|----------|--------|
| Small (< 100 Workloads) | 1 | 200m CPU / 256Mi | 500m CPU / 512Mi |
| Medium (< 1k Workloads) | 2 | 500m / 512Mi | 1 / 1Gi |
| Large (< 10k Workloads) | 2 | 1 / 1Gi | 2 / 2Gi |
| Very large (10k+) | 2-3 | 2 / 2Gi | 4 / 4Gi |

A single kueue-controller-manager comfortably handles ~10k active Workloads. Above that, look at sharding by tenant cluster.

### High Availability

Two replicas + leader election + PodDisruptionBudget:

```yaml
controllerManager:
  replicas: 2
  podDisruptionBudget: { enabled: true, minAvailable: 1 }
  manager:
    priorityClassName: system-cluster-critical
```

Only the leader does scheduling work; the standby just keeps the lease alive.

### Webhook Certificates

Default: Kueue manages its own webhook serving certs (`internalCertManagement.enable: true`). Cert is regenerated on Pod restart.

For organizations standardizing on cert-manager:

```yaml
# values.yaml
enableCertManager: true
internalCertManagement:
  enable: false
```

This creates `Certificate` and `Issuer` resources for the webhook.

### Prometheus Monitoring

If you have prometheus-operator, install with `--set enablePrometheus=true` to get a ServiceMonitor:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: { name: kueue, namespace: kueue-system }
spec:
  selector: { matchLabels: { control-plane: controller-manager, app.kubernetes.io/name: kueue } }
  endpoints:
  - port: https
    scheme: https
    bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    tlsConfig: { insecureSkipVerify: true }
    interval: 30s
```

Without prometheus-operator, scrape `kueue-controller-manager-metrics-service:8443` directly. See `operations-and-cli.md` for the metric catalog.

## kueuectl CLI Setup

Install via krew:

```bash
kubectl krew install kueue
kubectl kueue version
```

Or download the binary directly from the GitHub release matching your server version. See `operations-and-cli.md` for the full command surface.

## Multi-Tenancy Starter Manifest

Use this shape for the first real tenant rollout. Keep the full object set in source control, but start with small quotas and explicit namespace labels.

```yaml
apiVersion: v1
kind: Namespace
metadata: { name: team-research, labels: { kueue.x-k8s.io/managed: "true", department: research } }
---
apiVersion: v1
kind: Namespace
metadata: { name: team-prod, labels: { kueue.x-k8s.io/managed: "true", department: prod } }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: gpu-a100 }
spec:
  nodeLabels: { accelerator: nvidia-a100 }
  tolerations: [{ key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }]
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: company }
spec: {}
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: research-cq }
spec:
  cohort: company
  namespaceSelector: { matchLabels: { department: research } }
  resourceGroups:
  - coveredResources: [cpu, memory, "nvidia.com/gpu"]
    flavors:
    - name: gpu-a100
      resources:
      - { name: cpu, nominalQuota: "32", borrowingLimit: "32" }
      - { name: memory, nominalQuota: "128Gi", borrowingLimit: "128Gi" }
      - { name: "nvidia.com/gpu", nominalQuota: "4", borrowingLimit: "4" }
  flavorFungibility: { whenCanBorrow: TryNextFlavor, whenCanPreempt: TryNextFlavor }
  preemption: { reclaimWithinCohort: LowerPriority, withinClusterQueue: LowerPriority }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: prod-cq }
spec:
  cohort: company
  namespaceSelector: { matchLabels: { department: prod } }
  resourceGroups: [{ coveredResources: [cpu, memory, "nvidia.com/gpu"], flavors: [{ name: gpu-a100, resources: [{ name: cpu, nominalQuota: "32", borrowingLimit: "32" }, { name: memory, nominalQuota: "128Gi", borrowingLimit: "128Gi" }, { name: "nvidia.com/gpu", nominalQuota: "4", borrowingLimit: "4" }] }] }]
  preemption: { reclaimWithinCohort: Any, withinClusterQueue: LowerPriority }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: default, namespace: team-research }
spec: { clusterQueue: research-cq }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: default, namespace: team-prod }
spec: { clusterQueue: prod-cq }
```

Apply and verify with `kubectl apply -f starter.yaml`, `kueuectl get clusterqueue`, and `kueuectl get localqueue -A`. Submit jobs with `kueue.x-k8s.io/queue-name: default`; Kueue routes them by namespace labels. Add `WorkloadPriorityClass` objects only after basic admission works.

## Sources

- https://kueue.sigs.k8s.io/docs/installation/
- https://kueue.sigs.k8s.io/docs/installation/install-via-helm/
- https://kueue.sigs.k8s.io/docs/installation/upgrade/
- https://kueue.sigs.k8s.io/docs/reference/kueue-config.v1beta1/
- https://github.com/kubernetes-sigs/kueue/tree/main/charts/kueue
- https://github.com/kubernetes-sigs/kueue/tree/main/keps
- https://github.com/kubernetes-sigs/kueue/releases
