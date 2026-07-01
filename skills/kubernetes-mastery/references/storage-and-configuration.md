# Storage and Configuration

Sources: Kubernetes official documentation (v1.32), Luksa (Kubernetes in Action, 2nd ed.), Burns et al. (Kubernetes: Up and Running, 3rd ed.), CSI specification, AWS EBS/EFS CSI driver documentation, External Secrets Operator documentation

Covers: PersistentVolumes, PersistentVolumeClaims, StorageClasses, volume types, ConfigMaps, Secrets, projected volumes, External Secrets Operator, and ephemeral storage.

## Volume Types Overview

| Volume Type | Lifecycle | Access | Use Case |
|-------------|-----------|--------|----------|
| emptyDir | Pod lifetime | ReadWrite | Scratch space, inter-container sharing |
| hostPath | Node lifetime | ReadWrite | Node-level agents (avoid in production apps) |
| configMap | ConfigMap lifetime | ReadOnly | Configuration files |
| secret | Secret lifetime | ReadOnly | Credentials, certificates |
| persistentVolumeClaim | PVC lifetime | ReadWrite | Database storage, persistent data |
| projected | Combined sources | ReadOnly | Merge configMap + secret + downwardAPI + serviceAccountToken |
| downwardAPI | Pod lifetime | ReadOnly | Pod metadata (name, namespace, labels) |
| nfs | External | ReadWriteMany | Shared filesystem across pods |
| csi | External | Varies | Cloud provider volumes via CSI driver |

## PersistentVolumes and Claims

### Storage Provisioning Flow

```
StorageClass → PVC requests storage → PV provisioned → Pod mounts PVC
```

Dynamic provisioning (recommended): Create a StorageClass, reference it from PVC. The provisioner creates the PV automatically.

Static provisioning: Admin creates PV manually, PVC binds to it by capacity and access mode.

### StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com       # CSI driver
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Retain               # keep volume after PVC deletion
volumeBindingMode: WaitForFirstConsumer  # delay until pod schedules
allowVolumeExpansion: true          # allow PVC resize
```

### StorageClass Parameters by Provider

| Provider | Provisioner | Common Parameters |
|----------|------------|-------------------|
| AWS EBS | ebs.csi.aws.com | type (gp3/io2), iops, throughput, encrypted |
| AWS EFS | efs.csi.aws.com | provisioningMode, fileSystemId |
| GCE PD | pd.csi.storage.gke.io | type (pd-ssd/pd-standard), replication-type |
| Azure Disk | disk.csi.azure.com | skuName (StandardSSD_LRS/Premium_LRS) |
| Ceph RBD | rbd.csi.ceph.com | clusterID, pool, imageFeatures |
| NFS | nfs.csi.k8s.io | server, share |

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi
```

### Access Modes

| Mode | Abbreviation | Description |
|------|-------------|-------------|
| ReadWriteOnce | RWO | Single node read-write (most block storage) |
| ReadOnlyMany | ROX | Multiple nodes read-only |
| ReadWriteMany | RWX | Multiple nodes read-write (NFS, EFS, CephFS) |
| ReadWriteOncePod | RWOP | Single pod read-write (v1.29+, strictest) |

### Reclaim Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| Retain | PV preserved after PVC deletion | Production databases (manual cleanup) |
| Delete | PV and underlying storage deleted | Dev/test environments |
| Recycle | Deprecated; basic scrub then reuse | Do not use |

Use `Retain` for any data you cannot afford to lose. Manually manage retained PVs.

### Volume Expansion

Expand a PVC (StorageClass must have `allowVolumeExpansion: true`):

```bash
kubectl patch pvc app-data -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

For filesystem-based volumes, the pod may need to restart for the resize to take effect. Block-mode expansion is online.

### volumeBindingMode

| Mode | Behavior | When to Use |
|------|----------|-------------|
| Immediate | PV created immediately when PVC is created | Simple setups, no topology constraints |
| WaitForFirstConsumer | PV created when first pod using PVC is scheduled | Multi-zone clusters (ensures PV in same zone as pod) |

Use `WaitForFirstConsumer` in multi-zone clusters to prevent PV/pod zone mismatches.

## ConfigMaps

Store non-sensitive configuration data as key-value pairs.

### Create ConfigMap

```bash
# From literal values
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=CACHE_TTL=300

# From file
kubectl create configmap nginx-config --from-file=nginx.conf

# From env file
kubectl create configmap app-config --from-env-file=app.env
```

### ConfigMap Manifest

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: info
  CACHE_TTL: "300"
  config.yaml: |
    database:
      host: postgres
      port: 5432
    cache:
      ttl: 300
```

### Mount as Environment Variables

```yaml
spec:
  containers:
  - name: app
    envFrom:
    - configMapRef:
        name: app-config       # all keys become env vars
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL        # single key
```

### Mount as Files

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: config
      mountPath: /etc/app/config.yaml
      subPath: config.yaml      # mount single file, not entire directory
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: config.yaml
        path: config.yaml
```

### ConfigMap Update Behavior

| Mount Type | Update Behavior |
|-----------|----------------|
| Volume mount (no subPath) | Auto-updated within ~1 minute (kubelet sync period) |
| Volume mount with subPath | NOT auto-updated; requires pod restart |
| Environment variable | NOT auto-updated; requires pod restart |

For automatic config reloads, mount as a volume (without subPath) and have the application watch the file for changes, or use a sidecar like `configmap-reload`.

## Secrets

Store sensitive data (passwords, tokens, TLS certificates). Base64-encoded, not encrypted by default.

### Secret Types

| Type | Use Case |
|------|----------|
| Opaque | Generic key-value (default) |
| kubernetes.io/tls | TLS certificate and key |
| kubernetes.io/dockerconfigjson | Image pull credentials |
| kubernetes.io/basic-auth | Username and password |
| kubernetes.io/ssh-auth | SSH private key |
| kubernetes.io/service-account-token | SA token (legacy) |

### Create Secrets

```bash
# Generic secret
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=s3cret

# TLS secret
kubectl create secret tls app-tls \
  --cert=tls.crt \
  --key=tls.key

# Docker registry
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass
```

### Mount as Files (Preferred over Env Vars)

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
      defaultMode: 0400        # read-only for owner
```

Mount secrets as files instead of environment variables. Environment variables appear in process listings, crash dumps, and log output.

## Projected Volumes

Combine multiple volume sources into a single mount:

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: all-config
      mountPath: /etc/app
  volumes:
  - name: all-config
    projected:
      sources:
      - configMap:
          name: app-config
      - secret:
          name: app-secrets
      - downwardAPI:
          items:
          - path: labels
            fieldRef:
              fieldPath: metadata.labels
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600
          audience: my-api
```

## Immutable ConfigMaps and Secrets

Mark as immutable to prevent accidental changes and improve performance (kubelet skips watch):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v2
immutable: true
data:
  LOG_LEVEL: info
```

To update immutable resources: create a new ConfigMap with a new name, update the pod spec to reference it, delete the old one. Kustomize configMapGenerator handles this automatically via content hashing.

## External Secrets Operator (ESO)

Sync secrets from external managers (Vault, AWS SM, GCP SM) into Kubernetes Secrets.

### SecretStore (Namespaced)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault
  namespace: production
spec:
  provider:
    vault:
      server: https://vault.example.com
      path: secret
      auth:
        kubernetes:
          mountPath: kubernetes
          role: app-role
```

### ExternalSecret

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
  - secretKey: db-password
    remoteRef:
      key: secret/data/production/db
      property: password
  - secretKey: api-key
    remoteRef:
      key: secret/data/production/api
      property: key
```

ESO creates and maintains a Kubernetes Secret (`app-secrets`) that stays in sync with the external source. Applications consume it like any other Secret.

## Ephemeral Storage

### emptyDir

Temporary storage that exists for the pod's lifetime. Shared between containers in the same pod.

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: cache
      mountPath: /tmp/cache
  - name: sidecar
    volumeMounts:
    - name: cache
      mountPath: /data/cache
  volumes:
  - name: cache
    emptyDir:
      sizeLimit: 1Gi           # enforce size limit
      medium: Memory            # use tmpfs (RAM-backed, faster, counts against memory limit)
```

| medium | Backed By | Speed | Counted Against |
|--------|-----------|-------|----------------|
| "" (default) | Node disk | Disk speed | Ephemeral storage limits |
| Memory | tmpfs (RAM) | RAM speed | Container memory limits |
