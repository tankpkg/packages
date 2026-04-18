# Tailscale Networking and Routing

Sources: Tailscale official documentation (2025-2026), WireGuard protocol specification

## WireGuard Fundamentals

Tailscale builds on WireGuard, a modern VPN protocol operating at the kernel level
(or in userspace on platforms without kernel support).

**Peer-to-peer encrypted tunnels.** WireGuard creates a virtual network interface
(`utun` on macOS, `tailscale0` on Linux) and encrypts traffic between peers using
Curve25519 key exchange and ChaCha20-Poly1305 symmetric encryption. Each device
holds a private key; the corresponding public key is shared with peers.

**Key pairs.** Every Tailscale device generates a WireGuard key pair on enrollment.
The public key is registered with the coordination server. Tailscale rotates keys
periodically (default: 180 days) to limit exposure from key compromise.

**UDP transport.** WireGuard sends all encrypted packets over UDP. UDP avoids
TCP-over-TCP performance collapse when tunneling TCP traffic, and it enables the
NAT traversal techniques Tailscale relies on. Tailscale uses port 41641 by default
and can operate on any available UDP port.

**Stateless handshake.** WireGuard initiates a handshake only when there is traffic
to send. Tailscale sets persistent-keepalive intervals automatically based on NAT type.

### What Tailscale Adds to WireGuard

WireGuard alone requires manual key distribution and static peer configuration.
Tailscale adds automatic key distribution, dynamic peer discovery, NAT traversal,
DERP relay fallback, ACL enforcement, and identity-based authentication via SSO.

---

## IP Addressing

### Tailscale IP Range (CGNAT)

Every device receives a stable IPv4 address in `100.64.0.0/10` (Carrier-Grade NAT,
RFC 6598). These addresses are globally unique within your tailnet, not routable on
the public internet, and stable across reconnections — the same device always gets
the same address.

### IPv6 Addresses

Each device also receives an IPv6 address in the `fd7a:115c:a1e0::/48` prefix
(Unique Local Address range). Tailscale uses IPv6 for direct connectivity on
dual-stack networks and some NAT traversal paths.

### Address Stability

Tailscale IPs are tied to device identity, not network interface or physical location.
A laptop connecting from any network always presents the same `100.x.y.z` address.
This makes Tailscale IPs safe to use in configuration, though MagicDNS hostnames
are preferred for resilience.

---

## NAT Traversal

Most devices sit behind NAT routers that block unsolicited inbound connections.
Tailscale uses several techniques to establish direct peer-to-peer connections.

### STUN

When a device connects, it contacts Tailscale's STUN servers to discover its public
IP address and the external UDP port the NAT router has assigned. This information
is shared via the coordination server with peers that need to connect.

### UDP Hole Punching

For two devices behind NAT, Tailscale orchestrates simultaneous UDP packet exchange:

1. Both devices learn each other's public IP:port via the coordination server
2. Both send UDP packets to each other simultaneously
3. Each NAT router creates a mapping allowing the inbound reply
4. Subsequent packets flow directly peer-to-peer

| NAT Type | Direct Connection | Notes |
|----------|------------------|-------|
| Full cone | Yes | Any external host can reach the mapped port |
| Address-restricted | Yes | Hole punching succeeds |
| Port-restricted | Yes | Simultaneous send required |
| Symmetric | No | Falls back to DERP relay |
| Firewall blocks UDP | No | Falls back to DERP relay |

Run `tailscale netcheck` to see your NAT type and direct connection likelihood.

---

## DERP Relay System

When direct connections fail, Tailscale routes traffic through DERP (Designated
Encrypted Relay for Packets) servers. DERP is a fallback, not the primary path.

### How DERP Works

DERP servers forward encrypted packets but cannot decrypt them — all WireGuard
encryption is end-to-end between devices. The DERP server identifies the destination
by WireGuard public key, not IP address.

Tailscale continuously attempts to upgrade relay connections to direct connections.
Once a direct path is established, traffic migrates off DERP automatically.

### When DERP Is Used

- Symmetric NAT on either side prevents hole punching
- Corporate firewalls block UDP entirely
- During initial connection setup before hole punching completes

### Built-in DERP Servers

Tailscale operates a global network of DERP servers. Devices connect to the nearest
server based on latency. The full list is at `https://login.tailscale.com/derpmap/default`.

### Custom DERP Servers

Organizations with data residency requirements or air-gapped networks can run their
own DERP servers using the open-source `derper` binary. Requirements:

- TLS on TCP port 443 (HTTPS upgrade to WebSocket)
- Optionally UDP port 3478 (STUN)
- Add to tailnet DERP map via admin console or policy file
- Optionally disable built-in Tailscale DERP servers for the tailnet

---

## Coordination Server Role

The coordination server (`controlplane.tailscale.com`) manages the control plane
only. It does not handle any data plane traffic.

**Responsibilities:** authenticating devices via SSO, distributing WireGuard public
keys to peers, distributing ACL policy, assigning Tailscale IPs, coordinating NAT
traversal, and managing DERP server maps.

**Not responsible for:** forwarding, inspecting, or logging data plane traffic.
All application data flows directly between devices (or via DERP), never through
the coordination server.

---

## Network Topology

### Mesh (Default)

Every device communicates directly with every other device subject to ACL policy.
No central gateway; no single point of failure.

```
Device A ----direct WireGuard tunnel---- Device B
    |                                        |
    +----------direct tunnel-----------Device C
```

### Hub-and-Spoke via Subnet Routers

When connecting non-Tailscale devices, a subnet router acts as a gateway. Only
the router needs Tailscale installed; all other LAN devices are reachable transparently.

```
Tailnet Device A ----> Subnet Router ----> 192.168.1.0/24 LAN
Tailnet Device B ----> Subnet Router ----> 10.0.0.0/8 Corporate Network
```

---

## Subnet Routers

A subnet router advertises IP prefixes to the tailnet, making non-Tailscale devices
on those networks reachable from anywhere in the tailnet.

### Setup

On the subnet router device, enable IP forwarding and advertise routes:

```
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
sudo tailscale up --advertise-routes=192.168.1.0/24,10.0.0.0/8
```

### Approval

Advertised routes require explicit approval in the admin console or via
`autoApprovers` in the policy file:

```json
"autoApprovers": {
  "routes": {
    "192.168.1.0/24": ["group:network-admins"],
    "10.0.0.0/8":     ["tag:subnet-router"]
  }
}
```

### Client Configuration

Clients must opt in to use advertised routes:

```
sudo tailscale set --accept-routes
```

Without `--accept-routes`, the client ignores advertised subnet routes even if
they are approved in the admin console.

### High Availability (HA) Subnet Routers

Multiple devices can advertise the same subnet prefix. Tailscale automatically
load-balances and fails over between them — no additional configuration required.

```
Router A: --advertise-routes=10.0.0.0/8   (active)
Router B: --advertise-routes=10.0.0.0/8   (standby, auto-failover)
```

Tailscale selects the router with the best connectivity from the client's perspective.
If the primary goes offline, traffic shifts to the secondary within seconds.

### SNAT Behavior

By default, subnet routers perform source NAT: traffic from tailnet devices appears
to originate from the router's LAN IP. This simplifies LAN routing (return traffic
goes back to the router, not to an unknown Tailscale IP).

To disable SNAT when LAN devices have routes back to the Tailscale range:

```
sudo tailscale up --advertise-routes=10.0.0.0/8 --snat-subnet-routes=false
```

Disabling SNAT requires LAN devices to have a route for `100.64.0.0/10` pointing
to the subnet router, otherwise return traffic is dropped.

---

## Exit Nodes

An exit node routes all internet-bound traffic from a client through itself.
The client's public IP becomes the exit node's IP.

### Setup

```
sudo tailscale up --advertise-exit-node
```

Approve in the admin console or via `autoApprovers`:

```json
"autoApprovers": {
  "exitNode": ["tag:exit-node"]
}
```

### Client Usage

```
sudo tailscale set --exit-node=hostname
sudo tailscale set --exit-node=          # disable exit node
```

### LAN Access While Using an Exit Node

By default, all traffic (including LAN) routes through the exit node. To retain
access to local LAN resources:

```
sudo tailscale set --exit-node-allow-lan-access
```

This exempts RFC 1918 addresses from the exit node tunnel.

### Mullvad Exit Nodes

Tailscale integrates with Mullvad VPN to provide exit nodes in 30+ countries.
Link a Mullvad account in the admin console, then select by country or city:

```
sudo tailscale set --exit-node=mullvad.se
sudo tailscale set --exit-node=mullvad.us-nyc
```

### Auto Exit Node Suggestion

```
tailscale exit-node suggest
```

Evaluates latency to available exit nodes and recommends the optimal choice.
Useful in scripts that need to select an exit node without hardcoding a host.

---

## App Connectors

App connectors route traffic to specific domains through a tailnet device without
advertising full subnet routes. Use when you need domain-based access to internal
services rather than exposing an entire IP range.

### How It Works

The app connector advertises specific domains (not IP ranges). Tailscale routes
DNS queries and TCP connections for those domains through the connector, which
resolves and proxies them on the target network. No `--advertise-routes` or IP
forwarding required.

### Configuration

```json
"appConnectors": [
  {
    "name": "corp-apps",
    "connectors": ["tag:app-connector"],
    "domains": ["internal-app.corp.example.com", "*.corp.example.com"]
  }
]
```

---

## MagicDNS

MagicDNS provides automatic DNS resolution for all tailnet devices without manual
client configuration.

### How It Works

Tailscale installs a local DNS resolver on each device. This resolver handles
queries for tailnet hostnames and forwards everything else to configured upstream
resolvers.

### Hostname Format

| Format | Example | Scope |
|--------|---------|-------|
| Short hostname | `my-laptop` | Works within tailnet when unambiguous |
| Fully qualified | `my-laptop.tailnet-name.ts.net` | Always unambiguous |

The `tailnet-name` is visible in the admin console under DNS settings.

### Enabling and Disabling

Enable MagicDNS in the admin console under DNS -> Enable MagicDNS. To disable
on a specific device without affecting others:

```
sudo tailscale set --accept-dns=false
```

---

## DNS Configuration

### Global Nameservers

Global nameservers apply to all DNS queries from tailnet devices. Configure in
the admin console under DNS -> Nameservers -> Global nameservers. Common use:
route all DNS through a Pi-hole or internal resolver for ad blocking or logging.

### Split DNS

Split DNS routes queries for specific domains to designated resolvers; all other
queries go to the global nameserver.

| Domain | Resolver | Use Case |
|--------|----------|----------|
| `corp.example.com` | `10.0.0.53` | Internal corporate DNS |
| `*.svc.cluster.local` | `10.96.0.10` | Kubernetes cluster DNS |

Configure under DNS -> Nameservers -> Add nameserver -> Restrict to domain.

### DNS over HTTPS

Tailscale supports DoH for global nameservers. Enter the DoH URL instead of an IP:

```
https://dns.cloudflare.com/dns-query
https://dns.google/dns-query
```

### Query Resolution Order

When MagicDNS and custom nameservers are both configured:

1. Queries for `*.ts.net` and tailnet hostnames resolve via MagicDNS
2. Queries matching split DNS domains go to the restricted nameserver
3. All other queries go to the global nameserver
4. If no global nameserver is set, queries fall through to the OS resolver

---

## Reference: Networking Decision Guide

| Scenario | Recommended Approach |
|----------|---------------------|
| Access a remote LAN | Subnet router with `--advertise-routes` |
| Access multiple LANs with failover | HA subnet routers (same prefix, multiple devices) |
| Route all internet traffic through a fixed IP | Exit node |
| Route internet traffic through a commercial VPN | Mullvad exit node |
| Access specific internal domains only | App connector |
| Resolve internal hostnames across tailnet | MagicDNS + split DNS |
| Devices behind symmetric NAT | DERP relay (automatic fallback) |
| Air-gapped network, no external DERP | Custom DERP server |
| Non-Tailscale devices need tailnet access | Subnet router (no Tailscale install on LAN devices) |
