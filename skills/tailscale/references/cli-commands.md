# Tailscale CLI Commands

Sources: Tailscale official documentation (2025-2026)

## Platform CLI Locations

| Platform | Binary |
|----------|--------|
| Linux | `/usr/bin/tailscale` (client), `/usr/sbin/tailscaled` (daemon) |
| macOS (App Store) | `/Applications/Tailscale.app/Contents/MacOS/Tailscale` |
| macOS (Homebrew) | `/opt/homebrew/bin/tailscale` |
| Windows | `C:\Program Files\Tailscale\tailscale.exe` |

On macOS, alias the binary: `alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"`.
All commands require `tailscaled` running. On Linux: `sudo systemctl enable --now tailscaled`.

---

## Connectivity

### `tailscale up`

Connect to the tailnet. Prints an auth URL on first run; reconnects from stored
state on subsequent runs.

```
tailscale up [flags]
```

| Flag | Purpose |
|------|---------|
| `--auth-key` | Authenticate non-interactively with a pre-generated key |
| `--hostname` | Override the device name in the admin console |
| `--advertise-routes` | Announce subnet routes (comma-separated CIDRs) |
| `--advertise-exit-node` | Offer this device as a tailnet exit node |
| `--accept-routes` | Accept subnet routes advertised by other devices |
| `--accept-dns` | Use MagicDNS resolvers from the coordination server |
| `--exit-node` | Route all internet traffic through the named exit node |
| `--exit-node-allow-lan-access` | Allow LAN access while an exit node is active |
| `--ssh` | Enable Tailscale SSH server on this device |
| `--shields-up` | Block all incoming connections (outbound-only mode) |
| `--stateful-filtering` | Allow return traffic for outbound connections without explicit reverse ACLs |
| `--force-reauth` | Force re-authentication even if already logged in |
| `--login-server` | Connect to a custom control server (e.g. Headscale) |
| `--operator` | Linux user allowed to run `tailscale` without sudo |
| `--reset` | Reset all preferences to defaults before applying flags |

**`tailscale up` vs `tailscale set` vs `tailscale login`:**

| Command | When to Use | Triggers Re-auth? |
|---------|-------------|-------------------|
| `tailscale up` | Initial connection or when changing `--login-server` | Sometimes |
| `tailscale set` | Modify preferences on an already-connected device | Never |
| `tailscale login` | Switch accounts or force a fresh authentication flow | Always |

Prefer `tailscale set` for runtime changes on connected devices. Use `tailscale up`
when first connecting. Use `tailscale login` to switch accounts or recover from
key expiry.

### `tailscale down`

Disconnect from the tailnet without logging out. The device stays registered
and reconnects on the next `tailscale up`.

### `tailscale login`

Authenticate with the coordination server. Opens a browser or prints a URL.

```
tailscale login [--auth-key=<key>] [--hostname=<name>] [--login-server=<url>]
```

### `tailscale logout`

Log out and deregister the device. Removes it from the admin console.
Re-authentication is required to reconnect.

### `tailscale switch`

Switch between multiple tailnet accounts without logging out.

```
tailscale switch [account]
tailscale switch --list
```

### `tailscale set`

Modify device preferences on a connected device without re-authentication.
Accepts the same flags as `tailscale up` (except `--auth-key`, `--force-reauth`,
`--login-server`).

```bash
tailscale set --ssh                                    # Enable SSH server
tailscale set --advertise-routes=192.168.1.0/24       # Advertise subnet
tailscale set --exit-node=exit-node-hostname           # Activate exit node
tailscale set --exit-node=                             # Deactivate exit node
tailscale set --shields-up                             # Block incoming connections
tailscale set --accept-dns=false                       # Disable MagicDNS
tailscale set --stateful-filtering=false               # Disable stateful filtering
```

---

## Status & Diagnostics

### `tailscale status`

Display connection state, peer list, and IP addresses.

```
tailscale status [--json] [--active] [--peers=false] [--self=false]
```

Output columns: IP, hostname, OS, relay/direct status, last seen.
A `*` next to a peer indicates a direct (non-relayed) connection.

### `tailscale ping`

Send a Tailscale-layer ping to a peer. Reports path type (direct/relay) and latency.

```
tailscale ping [flags] <hostname-or-ip>
```

| Flag | Purpose |
|------|---------|
| `--c` | Number of pings (default: 10) |
| `--until-direct` | Keep pinging until a direct path is established |
| `--verbose` | Show detailed path information |
| `--icmp` | Send ICMP pings through the WireGuard tunnel |

### `tailscale netcheck`

Probe the network environment: NAT type, DERP relay latency, UDP/TCP reachability.

```
tailscale netcheck [--format=json] [--every=5s] [--verbose]
```

| Output Field | Meaning |
|-------------|---------|
| `MappingVariesByDestIP` | Symmetric NAT; direct connections unlikely |
| `HairPinning` | Router supports hairpin NAT |
| `UPnP` / `PMP` / `PCP` | Port mapping protocol availability |
| `PreferredDERP` | Lowest-latency DERP region |
| `RegionLatency` | Round-trip to each DERP region |

### `tailscale bugreport`

Generate a bug report token linked to a server-side log snapshot. Share the
printed token with Tailscale support.

```
tailscale bugreport [--diagnose] [--record]
```

### `tailscale ip`

Print the Tailscale IP address of the current device or a named peer.

```
tailscale ip [--4] [--6] [--1] [peer]
```

### `tailscale whois`

Look up owner, device name, OS, tags, and capabilities for a Tailscale IP or hostname.

```
tailscale whois [--json] <ip-or-hostname>
```

### `tailscale metrics`

Expose Prometheus-compatible metrics from the local daemon.

```
tailscale metrics print          # Print metrics to stdout
tailscale metrics write <file>   # Write for node exporter textfile collector
```

---

## Networking

### `tailscale dns`

Inspect MagicDNS configuration and perform DNS lookups through the Tailscale resolver.

```
tailscale dns status
tailscale dns query <name> [type]
```

### `tailscale exit-node`

List and suggest exit nodes available in the tailnet.

```
tailscale exit-node list
tailscale exit-node suggest
```

Activate with `tailscale set --exit-node=<hostname>`. Deactivate with `tailscale set --exit-node=`.

### `tailscale configure`

Apply platform-specific configuration.

```
tailscale configure kubeconfig   # Configure kubectl to use Tailscale for cluster access
```

---

## Services

### `tailscale serve`

Expose a local service to tailnet peers only (not the public internet).

```
tailscale serve [flags] <target>
tailscale serve status
tailscale serve reset
```

| Flag | Purpose |
|------|---------|
| `--bg` | Persist across sessions (background mode) |
| `--set-path` | Mount at a specific URL path |
| `--https` | Serve over HTTPS (port 443) |
| `--http` | Serve over HTTP on a specific port |
| `--tcp` | Proxy raw TCP traffic |
| `--tls-terminated-tcp` | Proxy TCP with TLS termination |

```bash
tailscale serve http://localhost:3000              # Expose local HTTP server
tailscale serve --set-path=/api http://localhost:8080
tailscale serve /path/to/directory                # Serve static files
tailscale serve tcp:2222 tcp://localhost:22       # TCP proxy
```

### `tailscale funnel`

Expose a local service to the public internet via Tailscale's infrastructure.
Supports ports 443, 8443, and 10000 only. Requires Funnel enabled in the admin console.

```
tailscale funnel [flags] <target>
tailscale funnel status
tailscale funnel reset
```

Public URL format: `https://<device>.<tailnet>.ts.net`. Accepts the same flags as `serve`.

```bash
tailscale funnel http://localhost:3000
tailscale funnel --https=8443 http://localhost:3000
```

### `tailscale file`

Transfer files between tailnet devices using Taildrop.

```
tailscale file cp <source> <target-device>:<destination>
tailscale file get [--conflict=overwrite] [--wait] <destination-dir>
```

```bash
tailscale file cp report.pdf laptop:              # Send to device root
tailscale file cp archive.tar.gz server:/tmp/     # Send to specific path
tailscale file get .                              # Accept pending files
```

### `tailscale drive`

Manage Tailscale Drive shares (WebDAV-based network drives).

```
tailscale drive share <name> <path>
tailscale drive unshare <name>
tailscale drive list
```

### `tailscale cert`

Obtain a Let's Encrypt TLS certificate for the device's MagicDNS hostname
(`<hostname>.<tailnet>.ts.net`) via Tailscale's ACME proxy.

```
tailscale cert [--cert-file=<path>] [--key-file=<path>] [domain]
```

```bash
tailscale cert                                    # Write to default paths
tailscale cert --cert-file=/etc/ssl/ts.crt --key-file=/etc/ssl/ts.key
```

Certificates renew automatically. Run from a cron job or systemd timer.

---

## Security

### `tailscale lock`

Manage Tailnet Lock: cryptographic signing of device additions by designated
key custodians. Once enabled, no device joins without a valid signature.

```
tailscale lock [subcommand]
```

| Subcommand | Purpose |
|------------|---------|
| `init` | Initialize Tailnet Lock; current device becomes a signing key custodian |
| `status` | Show lock status and trusted keys |
| `add` | Add a trusted signing key |
| `remove` | Remove a trusted signing key |
| `sign <node-key>` | Sign a pending device to authorize it |
| `disable` | Disable Tailnet Lock (requires disablement secret) |
| `log` | Show the Tailnet Lock audit log |
| `local-disable` | Emergency local disable (recovery only) |

Store disablement secrets offline. Losing all signing keys without a
disablement secret permanently locks the tailnet.

---

## System

### `tailscale version`

```
tailscale version [--daemon] [--json]
```

### `tailscale update`

```
tailscale update [--yes] [--track=stable|unstable] [--version=<ver>] [--dry-run]
```

### `tailscale completion`

Generate shell completion scripts.

```bash
tailscale completion bash > /etc/bash_completion.d/tailscale
tailscale completion zsh  > "${fpath[1]}/_tailscale"
tailscale completion fish > ~/.config/fish/completions/tailscale.fish
```

---

## tailscaled Daemon Configuration

Configure via `/etc/default/tailscaled` (Debian/Ubuntu) or
`/etc/sysconfig/tailscaled` (RHEL/Fedora), then restart:
`sudo systemctl restart tailscaled`.

| Flag | Default | Purpose |
|------|---------|---------|
| `--socket` | `/run/tailscale/tailscaled.sock` | Unix socket for CLI communication |
| `--statedir` | `/var/lib/tailscale` | State and certificate directory |
| `--port` | `41641` | UDP port for WireGuard traffic (0 = random) |
| `--tun` | `tailscale0` | TUN interface name |
| `--verbose` | `0` | Log verbosity (0-2) |
| `--no-logs-no-support` | false | Disable log upload to Tailscale |

### Userspace networking (no root / no TUN)

```bash
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
tailscale up --auth-key=tskey-auth-...
# Configure applications to use SOCKS5 at localhost:1055
```

---

## Common Patterns

### Subnet Router

```bash
# Linux: enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# Advertise routes
sudo tailscale up --advertise-routes=10.0.0.0/24,192.168.1.0/24

# On client devices
sudo tailscale up --accept-routes
```

Approve routes in the admin console: Machines > device > Edit route settings.

### Exit Node

```bash
# On the exit node
sudo tailscale up --advertise-exit-node

# On client devices
tailscale set --exit-node=exit-node-hostname
tailscale set --exit-node=exit-node-hostname --exit-node-allow-lan-access
```

### CI/CD Automation

```bash
tailscale up \
  --auth-key=tskey-auth-<key> \
  --hostname=ci-runner-$(date +%s) \
  --accept-routes

# Ephemeral nodes auto-remove on disconnect
tailscale down
```

### Headscale (Self-Hosted)

```bash
tailscale up --login-server=https://headscale.example.com --auth-key=<key>
```
