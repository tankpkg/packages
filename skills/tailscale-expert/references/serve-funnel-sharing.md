# Tailscale Services and Sharing

Sources: Tailscale official documentation (2025-2026)

## Feature Overview

| Feature | Audience | Protocol | Port Restrictions |
|---------|----------|----------|-------------------|
| Serve | Tailnet devices only | HTTP, HTTPS, TCP | None |
| Funnel | Public internet | HTTPS only | 443, 8443, 10000 |
| Taildrop | Tailnet devices only | Peer-to-peer | None |
| Drive | Tailnet devices only | WebDAV via SMB | None |
| Node Sharing | External tailnet members | All Tailscale traffic | None |

---

## Tailscale Serve

Serve exposes a local service to other devices on your tailnet. Traffic never
leaves the WireGuard mesh. Tailscale handles TLS termination automatically
using a Let's Encrypt certificate tied to the node's
`<hostname>.<tailnet>.ts.net` MagicDNS name.

Use Serve when sharing a development server with teammates, running an internal
dashboard, proxying a plain-HTTP service over HTTPS, or exposing a TCP service
(database, custom protocol) within the tailnet. Serve does not make services
reachable from the public internet — use Funnel for that.

### Syntax

```
tailscale serve [flags] <target>
```

| Flag | Description |
|------|-------------|
| `--bg` | Run in background (persists across terminal sessions) |
| `--https=<port>` | Serve on HTTPS at the specified port (default: 443) |
| `--http=<port>` | Serve on plain HTTP at the specified port |
| `--tcp=<port>` | Forward raw TCP connections to the target |
| `--tls-terminated-tcp=<port>` | Accept TLS, terminate it, forward plain TCP to target |
| `--set-path=<path>` | Mount the target at a specific URL path |
| `--yes` | Skip confirmation prompts |

### Target Types

```bash
# HTTP proxy — forward to a local HTTP server
tailscale serve http://localhost:3000

# HTTPS proxy — forward to a local HTTPS server (Tailscale re-encrypts)
tailscale serve https://localhost:8443

# Static file directory
tailscale serve /home/user/public/

# Text response (useful for health checks)
tailscale serve text:ok

# Raw TCP forwarding
tailscale serve --tcp=5432 tcp://localhost:5432

# TLS-terminated TCP — accept TLS on tailnet side, forward plain TCP
tailscale serve --tls-terminated-tcp=5432 tcp://localhost:5432
```

### TLS Termination

Tailscale terminates TLS at the node and provisions a Let's Encrypt certificate
automatically. The connection from Tailscale to the local target is unencrypted
(plain HTTP or TCP) unless you proxy to an HTTPS target. This is intentional:
the WireGuard tunnel already encrypts traffic between tailnet peers.

Inspect the certificate in use:

```bash
tailscale cert <hostname>.<tailnet>.ts.net
```

### Foreground vs Background Mode

Without `--bg`, Serve exits when the terminal session ends. With `--bg`, the
configuration persists as `tailscaled` state and survives reboots:

```bash
tailscale serve http://localhost:3000          # foreground
tailscale serve --bg http://localhost:3000     # background, persistent
```

### Multiple Simultaneous Configurations

```bash
# Mount two services at different paths on port 443
tailscale serve --set-path=/api http://localhost:8080
tailscale serve --set-path=/app http://localhost:3000

# Serve on multiple ports simultaneously
tailscale serve --https=443 http://localhost:3000
tailscale serve --https=8443 http://localhost:4000
```

Each `--set-path` mount is independent. Requests to `/api/*` route to port
8080; requests to `/app/*` route to port 3000.

### Status and Reset

```bash
tailscale serve status                  # list active handlers
tailscale serve --https=443 off         # remove a specific handler
tailscale serve --set-path=/api off     # remove a path-mounted handler
tailscale serve reset                   # remove all serve configurations
```

---

## Tailscale Funnel

Funnel extends Serve to make services reachable from the public internet. Any
device with an internet connection can reach a Funnel endpoint — no Tailscale
client required. Traffic is proxied through Tailscale's infrastructure and
delivered to the node over the WireGuard tunnel.

Funnel is designed for development, testing, and low-traffic internal tools.
Tailscale does not provide rate limiting, DDoS protection, or SLA guarantees
for Funnel traffic.

### Prerequisites

1. **MagicDNS must be enabled** in the admin console (DNS settings).
2. **HTTPS must be enabled** in the admin console (DNS settings).
3. **Funnel must be permitted in the policy file** via `nodeAttrs`:

```json
"nodeAttrs": [
  {
    "target": ["tag:servers"],
    "attr": ["funnel"]
  }
]
```

Without the `funnel` attribute in `nodeAttrs`, the command fails with a
permission error even for admin users.

### Port Restrictions

Funnel only accepts traffic on three ports. All Funnel traffic is HTTPS —
plain HTTP is not supported on the public endpoint.

| Port | Common Use |
|------|-----------|
| 443 | Standard HTTPS |
| 8443 | Alternate HTTPS |
| 10000 | Custom applications |

### Syntax

```
tailscale funnel [flags] <target>
```

| Flag | Description |
|------|-------------|
| `--bg` | Run in background |
| `--https=<port>` | Expose on the specified port (443, 8443, or 10000) |
| `--tcp=<port>` | Forward raw TCP (port must be 443, 8443, or 10000) |
| `--tls-terminated-tcp=<port>` | TLS-terminated TCP forwarding |

```bash
tailscale funnel http://localhost:3000              # port 443, foreground
tailscale funnel --https=8443 http://localhost:3000 # alternate port
tailscale funnel --bg http://localhost:3000         # background, persistent
tailscale funnel ./public/                          # static files
```

The public URL is `https://<hostname>.<tailnet>.ts.net` (port appended for
non-443 ports).

### PROXY Protocol Support

For TCP Funnel handlers, Tailscale prepends PROXY protocol v1 headers to
forwarded connections, allowing the backend to recover the original client IP:

```bash
tailscale funnel --tcp=443 tcp://localhost:8080
```

Enable PROXY protocol parsing on the backend to read the
`PROXY TCP4 <client-ip> ...` header prepended to each connection.

### Security Implications

- **No authentication by default** — implement auth at the application layer.
- **No rate limiting** — add application-level rate limiting for any endpoint
  that accepts user input.
- **Hostname is publicly discoverable** — the public URL reveals your tailnet
  domain (`<tailnet>.ts.net`).
- **Audit regularly** — run `tailscale funnel status` and remove endpoints that
  are no longer needed.

### Status and Reset

```bash
tailscale funnel status             # list active Funnel configurations
tailscale funnel --https=443 off    # remove a specific handler
tailscale funnel reset              # remove all Funnel configurations
```

---

## Taildrop

Taildrop transfers files directly between tailnet devices over the WireGuard
tunnel. No cloud storage intermediary is involved.

### Sending Files

```bash
tailscale file cp <file> [<file>...] <target>:
```

The target is a MagicDNS hostname followed by a colon (the colon is required).

```bash
tailscale file cp report.pdf laptop:
tailscale file cp *.log server-01:
tailscale file cp backup.tar.gz myserver.tailnet-name.ts.net:
```

Taildrop does not support sending directories directly. Archive with `tar` or
`zip` first.

### Receiving Files

Files land in the Taildrop inbox on the receiving device. Retrieve them with:

```bash
tailscale file get <destination-directory>
tailscale file get .                                    # current directory
tailscale file get ~/Downloads/
```

`tailscale file get` moves files out of the inbox; the inbox clears as files
are retrieved.

### Conflict Handling and Loop Mode

| Flag | Behavior |
|------|----------|
| (default) | Rename incoming file with a numeric suffix (`file (1).pdf`) |
| `--conflict=skip` | Skip the file, leave existing untouched |
| `--conflict=overwrite` | Overwrite the existing file |
| `--conflict=rename` | Rename incoming file (explicit default) |

For continuous receiving on servers or shared devices:

```bash
tailscale file get --loop ~/incoming/
```

Loop mode blocks and processes files as they arrive. Use with a process
supervisor or `nohup` for persistent operation.

On macOS and iOS, Taildrop integrates with the system share sheet. On Linux
and Windows, use the CLI commands above.

---

## Tailscale Drive

Tailscale Drive exposes a local directory as a network share accessible to
tailnet members. The share is served over WebDAV and accessed via SMB on
client devices.

### Subcommands

```bash
tailscale drive share <name> <path>         # create a share
tailscale drive list                        # list active shares on this device
tailscale drive rename <old-name> <new-name>
tailscale drive unshare <name>              # remove a share
```

`<name>` is the share label visible to other tailnet members. `<path>` is the
absolute path to the directory being shared.

### Accessing Shares from Client Devices

The SMB path pattern is:

```
smb://<hostname>.<tailnet>.ts.net/<share-name>
```

- **macOS**: Finder > Go > Connect to Server, enter the SMB URL.
- **Windows**: Map Network Drive, enter `\\<hostname>.<tailnet>.ts.net\<share-name>`.
- **Linux**: mount with `cifs` or use a file manager that supports SMB.

Drive shares are accessible to all tailnet members who can reach the sharing
device per the tailnet ACL policy. There is no per-share access control within
Drive itself — restrict access at the ACL level.

---

## Node Sharing

Node sharing allows a tailnet member to share an individual device with users
in a different tailnet. The shared device appears in the recipient's tailnet
as an external node.

### How It Works

1. The device owner initiates sharing from the admin console (Machines > Share)
   or via the Tailscale app.
2. The recipient receives an invitation link and accepts it.
3. The shared device appears in the recipient's device list with an indicator
   that it belongs to an external tailnet.
4. The recipient reaches the device using its MagicDNS name or Tailscale IP.

### Limitations

- Shared nodes are governed by the ACL policy of the sharing tailnet, not the
  recipient's tailnet.
- The recipient cannot further share the node with others.
- Sharing is per-device, not per-service — the recipient can reach any port
  the sharing tailnet's ACLs permit.
- Revoke sharing at any time from the admin console (Machines > Shared).

---

## Tailscale Services (Service Discovery)

Tailscale Services enables automatic endpoint collection and discovery within
a tailnet. When a node runs `tailscale serve` or `tailscale funnel`, the
exposed endpoints are registered in the tailnet's service registry. Other
nodes can discover these endpoints without prior knowledge of the serving
node's address.

```bash
tailscale services list                     # list all advertised services
tailscale services list --filter=<name>     # filter by name
```

Service discovery is useful in dynamic environments (containers, ephemeral
VMs) where consumers need to locate services by name rather than by IP.

---

## Serve vs Funnel Decision Guide

| Question | Serve | Funnel |
|----------|-------|--------|
| Who needs access? | Tailnet members only | Anyone on the internet |
| Tailscale client required? | Yes | No |
| Available ports | Any | 443, 8443, 10000 |
| TLS automatic? | Yes (MagicDNS cert) | Yes (MagicDNS cert) |
| Traffic encrypted in transit? | Yes (WireGuard) | Yes (HTTPS + WireGuard) |
| Tailscale rate-limits traffic? | No | No |
| Requires `nodeAttrs` in policy? | No | Yes (`funnel` attribute) |
| Suitable for production? | Internal tools, yes | Development/testing preferred |

## Common Patterns

**Webhook receiver during development:**

```bash
tailscale funnel --bg http://localhost:8080
# Point the external service to: https://<hostname>.<tailnet>.ts.net/webhook
```

**Internal dashboard for the team:**

```bash
tailscale serve --bg http://localhost:3000
# Team members access: https://<hostname>.<tailnet>.ts.net
```

**Database accessible within tailnet:**

```bash
tailscale serve --bg --tcp=5432 tcp://localhost:5432
# psql -h <hostname>.<tailnet>.ts.net -p 5432 -U user dbname
```

**Batch file transfer to a server:**

```bash
tailscale file cp ./logs/*.gz logserver:
# On logserver:
tailscale file get --conflict=overwrite /var/log/incoming/
```

**Persistent network share:**

```bash
tailscale drive share docs /home/user/shared-docs
# macOS client: smb://sharing-host.tailnet-name.ts.net/docs
```
