# Helm and Kustomize

Sources: Helm official documentation (v3.17), Kustomize official documentation, Kubernetes official documentation (v1.32), Lander (Managing Kubernetes), CNCF Artifact Hub documentation

Covers: Helm chart anatomy, values and templates, chart repositories, hooks, dependency management, Kustomize bases and overlays, patches, strategic merge, generators, and Helm vs Kustomize selection.

## Helm Overview

Helm is a package manager for Kubernetes. Charts are packages of pre-configured Kubernetes resources.

### Helm Architecture (v3)

No Tiller (removed in v3). Helm CLI talks directly to the Kubernetes API server using kubeconfig credentials.

```
helm install → renders templates with values → applies to cluster
helm upgrade → diffs templates → applies changes
helm rollback → restores previous release revision
```

### Essential Helm Commands

```bash
# Repository management
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo postgres

# Install
helm install my-release bitnami/postgresql -f values.yaml -n databases

# Upgrade
helm upgrade my-release bitnami/postgresql -f values.yaml -n databases

# Rollback
helm rollback my-release 1 -n databases

# Uninstall
helm uninstall my-release -n databases

# Debug and inspect
helm template my-release bitnami/postgresql -f values.yaml    # render locally
helm get values my-release -n databases                        # see applied values
helm get manifest my-release -n databases                      # see rendered manifests
helm history my-release -n databases                           # see revisions
helm lint ./my-chart                                           # validate chart
helm diff upgrade my-release ./my-chart -f values.yaml         # requires helm-diff plugin
```

## Helm Chart Anatomy

```
my-chart/
  Chart.yaml              # metadata: name, version, dependencies
  values.yaml             # default configuration values
  templates/              # Go template files
    deployment.yaml
    service.yaml
    ingress.yaml
    _helpers.tpl           # reusable template functions
    NOTES.txt              # post-install instructions
  charts/                  # dependency charts (vendored)
  .helmignore              # files to exclude from packaging
```

### Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: A web application chart
type: application          # or library
version: 1.2.0             # chart version (bump on chart changes)
appVersion: "3.4.5"        # application version
dependencies:
- name: postgresql
  version: "13.x"
  repository: "https://charts.bitnami.com/bitnami"
  condition: postgresql.enabled
```

### Values and Templates

`values.yaml` provides defaults. Override at install/upgrade time:

```yaml
# values.yaml
replicaCount: 3
image:
  repository: myapp
  tag: "1.2.3"
  pullPolicy: IfNotPresent
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    memory: 256Mi
ingress:
  enabled: true
  host: app.example.com
```

Template referencing values:

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

### Template Functions Cheat Sheet

| Function | Purpose | Example |
|----------|---------|---------|
| `include` | Render named template | `{{ include "app.labels" . }}` |
| `toYaml` | Convert to YAML string | `{{ toYaml .Values.resources }}` |
| `nindent` | Newline + indent | `{{ ... \| nindent 4 }}` |
| `default` | Fallback value | `{{ .Values.port \| default 8080 }}` |
| `quote` | Wrap in quotes | `{{ .Values.name \| quote }}` |
| `required` | Fail if missing | `{{ required "name required" .Values.name }}` |
| `tpl` | Render string as template | `{{ tpl .Values.annotation . }}` |
| `lookup` | Query live cluster | `{{ lookup "v1" "Secret" "ns" "name" }}` |
| `if/else` | Conditional | `{{- if .Values.ingress.enabled }}` |
| `range` | Loop | `{{- range .Values.hosts }}` |

### Helm Hooks

Execute resources at specific lifecycle points:

| Hook | When |
|------|------|
| `pre-install` | Before any resources installed |
| `post-install` | After all resources installed |
| `pre-upgrade` | Before upgrade begins |
| `post-upgrade` | After upgrade completes |
| `pre-delete` | Before deletion |
| `pre-rollback` | Before rollback |
| `test` | On `helm test` |

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": hook-succeeded
```

### Dependency Management

```bash
helm dependency update ./my-chart    # download dependencies to charts/
helm dependency build ./my-chart     # rebuild from lock file
```

Control sub-chart values via parent values:

```yaml
# parent values.yaml
postgresql:
  enabled: true
  auth:
    postgresPassword: secret
```

## Kustomize Overview

Kustomize uses overlays to patch base manifests without templates. Built into kubectl since v1.14.

```bash
kubectl apply -k ./overlays/production     # apply kustomized manifests
kubectl kustomize ./overlays/production     # render without applying
```

### Directory Structure

```
base/
  kustomization.yaml
  deployment.yaml
  service.yaml
overlays/
  dev/
    kustomization.yaml
    replica-patch.yaml
  staging/
    kustomization.yaml
  production/
    kustomization.yaml
    resource-patch.yaml
    hpa.yaml
```

### Base kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
- service.yaml
commonLabels:
  app: myapp
```

### Overlay kustomization.yaml

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
- hpa.yaml                    # additional resources for prod
namespace: production
namePrefix: prod-
commonLabels:
  env: production
patches:
- path: resource-patch.yaml
  target:
    kind: Deployment
    name: myapp
images:
- name: myapp
  newTag: "1.2.3"
configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=info
  - CACHE_TTL=300
secretGenerator:
- name: app-secrets
  envs:
  - secrets.env
```

### Kustomize Patch Types

| Type | Format | Best For |
|------|--------|----------|
| Strategic Merge | Partial YAML matching structure | Adding/modifying fields |
| JSON Patch | Array of operations | Precise field operations |
| Inline patch | In kustomization.yaml | Small one-off changes |

Strategic merge patch:

```yaml
# resource-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            memory: 1Gi
```

JSON patch:

```yaml
# json-patch.yaml
- op: replace
  path: /spec/replicas
  value: 5
- op: add
  path: /spec/template/spec/containers/0/env/-
  value:
    name: NEW_VAR
    value: "hello"
```

### Kustomize Generators

ConfigMap and Secret generators create resources with content hashes in the name, triggering pod restarts on config changes.

```yaml
configMapGenerator:
- name: app-config
  files:
  - config.json
  literals:
  - KEY=value

secretGenerator:
- name: app-secrets
  files:
  - tls.crt
  - tls.key
  type: kubernetes.io/tls
```

## Helm vs Kustomize Decision

| Factor | Helm | Kustomize |
|--------|------|-----------|
| Third-party packages | Charts from Artifact Hub | Must convert to base manifests |
| Templating logic | Go templates (if/else, range, functions) | None -- pure patching |
| Distribution | Chart registry (OCI, HTTP) | Git repository |
| Release management | Built-in (history, rollback) | External (ArgoCD, Flux) |
| Learning curve | Moderate (Go templates) | Low (YAML only) |
| Complexity ceiling | High (supports complex charts) | Medium (patches only) |
| Validation | `helm lint`, `helm template` | `kubectl kustomize --dry-run` |

### Hybrid Approach (Common in Production)

Use Helm for third-party dependencies (databases, monitoring stacks) and Kustomize for in-house application manifests:

```
infrastructure/
  charts/                     # Helm for third-party
    prometheus/
    postgresql/
apps/
  base/                       # Kustomize for in-house apps
    deployment.yaml
    service.yaml
  overlays/
    dev/
    production/
```

ArgoCD and Flux natively support both Helm and Kustomize sources.
