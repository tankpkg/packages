# Tailscale Integrations

Sources: Tailscale official documentation (2025-2026), community deployment patterns

---

## Docker Integration

### Official Image and Environment Variables

Tailscale publishes `tailscale/tailscale` on Docker Hub. The image runs `tailscaled`
in userspace networking mode by default, requiring no host kernel modules.

| Variable | Purpose | Example |
|----------|---------|---------|
| `TS_AUTHKEY` | Auth key for unattended login | `tskey-auth-...` |
| `TS_HOSTNAME` | Override device hostname in tailnet | `web-server-prod` |
| `TS_STATE_DIR` | Directory for persistent state | `/var/lib/tailscale` |
| `TS_EXTRA_ARGS` | Additional `tailscale up` flags | `--advertise-exit-node` |
| `TS_ROUTES` | Subnet routes to advertise | `10.0.0.0/8` |
| `TS_DEST_IP` | Forward all traffic to this IP (proxy mode) | `192.168.1.10` |
| `TS_USERSPACE` | Force userspace networking | `true` |

Use `TS_AUTHKEY` with an ephemeral, pre-authorized key for containers that should
not persist in the tailnet after shutdown.

### Sidecar Pattern

Run a Tailscale container alongside an application container, sharing the network
namespace. The application becomes reachable on the tailnet without modifying its
image.

```yaml
services:
  tailscale:
    image: tailscale/tailscale:latest
    network_mode: service:app
    environment:
      - TS_AUTHKEY=tskey-auth-...
      - TS_HOSTNAME=my-app
      - TS_STATE_DIR=/var/lib/tailscale
    volumes:
      - tailscale-state:/var/lib/tailscale
    cap_add:
      - NET_ADMIN

  app:
    image: nginx:alpine

volumes:
  tailscale-state:
```

With `network_mode: service:app`, traffic arriving on the tailnet IP reaches the
application directly. Mount `/dev/net/tun` and add `NET_ADMIN` to enable kernel-mode
networking; without these, the container falls back to userspace automatically.

### Userspace vs Kernel Networking

| Mode | Requirement | Use Case |
|------|-------------|----------|
| Kernel | `/dev/net/tun`, `NET_ADMIN` cap | Subnet routing, exit nodes, higher throughput |
| Userspace | None | Restricted environments, rootless containers |

Always mount a named volume at `TS_STATE_DIR`. Without persistence, the container
re-authenticates on every restart and creates a new device entry in the tailnet.

---

## Kubernetes Integration

### Tailscale Kubernetes Operator

The Tailscale Kubernetes Operator reached general availability in April 2025. It
manages Tailscale resources as Kubernetes-native objects and provisions node keys
automatically via an OAuth client.

```bash
helm repo add tailscale https://pkgs.tailscale.com/helmcharts
helm repo update
helm upgrade --install tailscale-operator tailscale/tailscale-operator \
  --namespace tailscale \
  --create-namespace \
  --set-string oauth.clientId=<CLIENT_ID> \
  --set-string oauth.clientSecret=<CLIENT_SECRET>
```

Create an OAuth client in the admin console (Settings > OAuth clients) with
`devices:write` scope.

### Exposing Services to the Tailnet (Ingress)

Annotate a `LoadBalancer` service to expose it on the tailnet:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    tailscale.com/expose: "true"
    tailscale.com/hostname: "my-app-k8s"
    tailscale.com/tags: "tag:k8s-service"
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
  type: LoadBalancer
```

The operator provisions a proxy pod that joins the tailnet as `my-app-k8s` and
forwards traffic to the service. For HTTPS with MagicDNS, use an `Ingress` resource
with `ingressClassName: tailscale`.

### Connector CRD for Subnet Routing

The `Connector` CRD configures subnet routers without a dedicated VM:

```yaml
apiVersion: tailscale.com/v1alpha1
kind: Connector
metadata:
  name: cluster-subnet-router
spec:
  hostname: k8s-subnet-router
  subnetRouter:
    advertiseRoutes:
      - 10.96.0.0/12    # cluster service CIDR
      - 10.244.0.0/16   # pod CIDR
  tags:
    - tag:k8s-connector
```

Approve routes in the admin console or via ACL `autoApprovers`.

### Egress and Deployment Modes

For egress (cluster pods accessing tailnet resources), use the `ProxyGroup` CRD
(operator v1.60+) for high-availability egress with multiple proxy replicas.

| Mode | How | When to Use |
|------|-----|-------------|
| Operator-managed proxy | Separate pod per service | Exposing services, egress |
| Sidecar | Tailscale container in same pod | Per-pod isolation, no operator |
| DaemonSet | One Tailscale pod per node | Node-level subnet routing |

The Helm chart creates the necessary `ClusterRole` and `ClusterRoleBinding`
automatically. For namespace-scoped deployments, restrict the operator's watch
namespace via the `--namespace` flag.

---

## Cloud-Init Integration

Automate Tailscale installation on cloud VMs at boot:

```yaml
#cloud-config
runcmd:
  - curl -fsSL https://tailscale.com/install.sh | sh
  - tailscale up --authkey=tskey-auth-... --hostname=$(hostname) --ssh
  - systemctl enable --now tailscaled
```

For subnet routers, enable IP forwarding before advertising routes:

```yaml
#cloud-config
runcmd:
  - curl -fsSL https://tailscale.com/install.sh | sh
  - echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.d/99-tailscale.conf
  - sysctl -p /etc/sysctl.d/99-tailscale.conf
  - tailscale up --authkey=tskey-auth-... --advertise-routes=10.0.0.0/24
```

Store auth keys in cloud provider secret managers (AWS Secrets Manager, GCP Secret
Manager, Azure Key Vault) and retrieve them at boot rather than embedding in templates.

---

## NAS Integration

### Synology and QNAP

Install Tailscale from the Synology Package Center or QNAP App Center. After
installation, authenticate via the admin console link shown in the package UI.
Enable subnet routing in the package UI to advertise the NAS's local network.

ACL consideration: define rules targeting the NAS's tailnet IP rather than relying
on hostname resolution for port-specific access control, as NAS services run on
non-standard ports.

### TrueNAS

TrueNAS SCALE includes Tailscale as a community application in the TrueCharts
catalog. TrueNAS CORE users install via the FreeBSD package manager:

```sh
pkg install tailscale
sysrc tailscaled_enable="YES"
service tailscaled start
tailscale up --authkey=tskey-auth-...
```

Configure the app to use a persistent data path (e.g., `/mnt/pool/tailscale`) to
survive app updates.

---

## Router Integration

### OpenWrt

```sh
opkg update && opkg install tailscale
/etc/init.d/tailscale enable && /etc/init.d/tailscale start
tailscale up --authkey=tskey-auth-... --advertise-routes=192.168.1.0/24
```

Enable IP forwarding in `/etc/sysctl.conf` and add a firewall zone for `tailscale0`
with forwarding to `lan` (via LuCI: Network > Firewall).

### pfSense and OPNsense

pfSense lacks an official Tailscale package. The recommended approach is a dedicated
Linux VM acting as a subnet router, with pfSense routing the tailnet CIDR
(`100.64.0.0/10`) to that VM.

OPNsense provides the `os-tailscale` plugin. After installation, configure via
Services > Tailscale in the OPNsense UI and approve routes in the admin console.

---

## CI/CD Integration

### GitHub Actions

Use `tailscale/github-action` to connect a runner to the tailnet for the duration
of a workflow job:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Connect to Tailscale
        uses: tailscale/github-action@v2
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
          tags: tag:ci-runner

      - name: Deploy to private server
        run: ssh deploy@my-server.tailnet-name.ts.net './deploy.sh'
```

Use OAuth clients rather than auth keys for CI — they support automatic key
rotation and do not expire. The action tears down the connection at job end.

### Ephemeral Keys and Tagging

Generate ephemeral auth keys for CI runners so disconnected nodes are removed
from the tailnet automatically. Tag CI runners with a dedicated tag (e.g.,
`tag:ci`) and write ACL rules granting access only to the specific hosts and
ports the pipeline requires.

For GitLab CI, install Tailscale in `before_script` and call `tailscale logout`
in `after_script`. Pass `--hostname=gitlab-runner-$CI_JOB_ID` to distinguish
concurrent runners.

---

## Headscale: Self-Hosted Control Server

Headscale is an open-source implementation of the Tailscale control server,
providing coordination without relying on Tailscale's hosted infrastructure.

```sh
tailscale up --login-server=https://headscale.example.com
```

All standard Tailscale clients support `--login-server`.

| Feature | Headscale Support |
|---------|------------------|
| MagicDNS | Supported |
| ACLs (HuJSON) | Supported |
| Tailscale SSH | Supported |
| Tailscale Serve/Funnel | Not supported |
| Kubernetes Operator | Not supported |
| iOS/Android clients | Supported |

Run Headscale behind a reverse proxy with TLS termination. For production, deploy
a self-hosted DERP server to avoid reliance on Tailscale's relay infrastructure.
Headscale suits air-gapped environments or strict data-residency requirements;
expect reduced feature parity compared to the hosted control plane.

---

## tsnet: Embedding Tailscale in Go Applications

`tsnet` embeds a Tailscale node directly into a Go process. The application joins
the tailnet as a first-class device without a system-level Tailscale installation.

```go
import "tailscale.com/tsnet"

func main() {
    srv := &tsnet.Server{
        Hostname: "my-tool",
        AuthKey:  os.Getenv("TS_AUTHKEY"),
        Dir:      "/var/lib/my-tool/tailscale",
    }
    defer srv.Close()

    ln, err := srv.Listen("tcp", ":8080")
    if err != nil {
        log.Fatal(err)
    }
    http.Serve(ln, myHandler())
}
```

`srv.Listen` returns a `net.Listener` bound to the tailnet IP. The application is
reachable on the tailnet without any external daemon.

| Aspect | tsnet | System Tailscale |
|--------|-------|-----------------|
| Installation | Library dependency only | Package install required |
| Isolation | Per-process tailnet identity | Shared system identity |
| Subnet routing | Not supported | Supported |
| State | Application-managed directory | `/var/lib/tailscale` |

Use tsnet when distributing a Go binary that needs tailnet access without requiring
users to install or configure Tailscale separately. Common use cases: internal CLI
tools, custom proxies, edge devices, and integration test harnesses.

---

## VS Code Remote SSH

Connect VS Code to a remote machine over Tailscale SSH:

1. Enable Tailscale SSH on the remote: `tailscale up --ssh`
2. Add to `~/.ssh/config`:

```
Host my-server
    HostName my-server.tailnet-name.ts.net
    User ubuntu
    ProxyCommand tailscale ssh --nc %h %p
```

3. Use Remote-SSH: Connect to Host in VS Code and select `my-server`.

Tailscale SSH handles authentication via tailnet identity — no SSH key management
required. ACL rules control which users can SSH to which machines.

---

## Integration Selection Guide

| Scenario | Recommended Approach |
|----------|---------------------|
| Containerized app on a single host | Docker sidecar with shared network namespace |
| Kubernetes service exposure | Operator ingress annotation |
| Kubernetes cluster subnet routing | Operator `Connector` CRD |
| Cloud VM provisioning at scale | cloud-init with OAuth client or ephemeral key |
| NAS remote access | Native package (Synology/QNAP) or manual (TrueNAS) |
| Home network remote access | Router integration (OpenWrt/OPNsense) |
| CI/CD private infrastructure access | `tailscale/github-action` with OAuth client |
| Air-gapped or data-residency requirement | Headscale self-hosted control server |
| Go application needing tailnet identity | tsnet library |
| Remote development on private server | VS Code Remote SSH over Tailscale SSH |

**Use the Kubernetes Operator** when running workloads in Kubernetes — it eliminates
manual key management and integrates with native Kubernetes resource types.

**Use Docker sidecars** for single-host container deployments where the operator
is unavailable or the deployment is too small to justify it.

**Use cloud-init** for immutable infrastructure where nodes are provisioned and
destroyed frequently — pair with ephemeral keys or OAuth clients.

**Use Headscale** only when the hosted control plane is unacceptable due to
compliance, air-gap, or cost requirements. Expect reduced feature parity.

**Use tsnet** when building Go tools that need tailnet connectivity as a library
dependency rather than a system service.
