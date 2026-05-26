# Tailscale Security Features

Sources: Tailscale official documentation (2025-2026), WireGuard protocol specification

## Security Model

Tailscale separates the coordination plane from the data plane. The coordination
server distributes public keys and policy; it never sees traffic content. All
device-to-device traffic travels over WireGuard tunnels encrypted end-to-end.

| Plane | What Tailscale Sees | Encrypted By |
|-------|---------------------|--------------|
| Coordination | Public keys, device metadata, policy | TLS (HTTPS) |
| Data | Nothing — traffic bypasses Tailscale servers | WireGuard (ChaCha20-Poly1305) |
| DERP relay | Encrypted blobs only | WireGuard (relay cannot decrypt) |

WireGuard uses Curve25519 for key exchange, ChaCha20-Poly1305 for authenticated
encryption, and BLAKE2s for hashing. Each device generates its own private key
locally; it never leaves the device.

---

## Tailnet Lock

Tailnet Lock prevents the coordination server from introducing unauthorized
devices. Without it, a compromised coordination server could theoretically add
rogue nodes. With it, every node's WireGuard public key must be cryptographically
signed by a trusted signing key before other nodes accept it.

### Initialization

```
tailscale lock init --gen-disablement-secrets=3
```

`--gen-disablement-secrets` generates recovery codes. Store them offline in
separate secure locations. Losing all disablement secrets permanently locks the
tailnet with no recovery path.

### Signing and Managing Keys

```
tailscale lock status                      # list nodes awaiting signature and trusted keys
tailscale lock sign <node-key>             # sign a specific node
tailscale lock add <signing-key-public>    # add a trusted signing key
tailscale lock remove <signing-key-public> # remove a compromised signing key
tailscale lock disable <disablement-secret>
```

Automate signing in CI/CD by running `tailscale lock sign` from a trusted host
after device enrollment. Rotate signing keys when a device holding one is
decommissioned; remove the old key before wiping the device.

| Scenario | Recommendation |
|----------|---------------|
| High-security tailnet (finance, healthcare) | Enable Tailnet Lock |
| Small team, low threat model | Optional; adds operational overhead |
| Automated device enrollment at scale | Plan signing automation before enabling |
| Headscale (self-hosted) | Not supported |

---

## HTTPS Certificates

Tailscale issues valid TLS certificates for devices via Let's Encrypt, using the
device's MagicDNS hostname (e.g., `myhost.tailnet-name.ts.net`). Certificates
are provisioned on demand and renewed automatically by the daemon.

### Requirements

- MagicDNS enabled on the tailnet.
- HTTPS enabled in admin console (Settings > General > HTTPS).
- Device authenticated and connected.

### Provisioning

```
tailscale cert                                    # issue/renew for current device
tailscale cert myhost.tailnet-name.ts.net         # explicit hostname
tailscale cert --cert-file /etc/ssl/ts.crt --key-file /etc/ssl/ts.key
```

The daemon renews certificates automatically before expiry. Applications that
read certificates at startup must be restarted or configured to reload on change.

### Caddy Integration

Caddy integrates with Tailscale's certificate provisioning via the
`get_certificate tailscale` directive. Caddy fetches and renews certificates
through the Tailscale daemon socket — no ACME configuration required:

```
myhost.tailnet-name.ts.net {
    tls { get_certificate tailscale }
    reverse_proxy localhost:3000
}
```

### Certificate Renewal

Certificates expire after 90 days. For devices frequently offline, force renewal
via cron:

```
0 3 * * * tailscale cert --cert-file /etc/ssl/ts.crt --key-file /etc/ssl/ts.key && systemctl reload nginx
```

---

## Tailscale SSH

Tailscale SSH replaces traditional SSH key management. Authentication uses the
device's Tailscale identity; no SSH keys or `authorized_keys` files are required.
The daemon intercepts SSH connections, authenticates against the tailnet policy,
and runs the session inside the WireGuard tunnel. Port 22 is never exposed.

```
tailscale set --ssh
```

### ACL-Based SSH Rules

SSH access is defined in the policy file under the `ssh` key. Key fields:

| Field | Purpose |
|-------|---------|
| `action` | `accept` or `check` |
| `src` | Who can connect (users, groups, tags) |
| `dst` | Target devices (tags, groups, `autogroup:self`) |
| `users` | OS usernames allowed on the target |

Example — allow engineers to SSH into production servers as `ubuntu`:

```json
"ssh": [
  {
    "action": "accept",
    "src": ["group:engineering"],
    "dst": ["tag:prod"],
    "users": ["ubuntu"]
  }
]
```

### Check Mode

`"action": "check"` requires re-authentication via SSO before the session is
established. Use for privileged access to sensitive systems. `checkPeriod` sets
how long the re-authentication remains valid:

```json
{
  "action": "check",
  "src": ["group:engineering"],
  "dst": ["tag:prod-db"],
  "users": ["root"],
  "checkPeriod": "12h"
}
```

### Session Recording

Configure recording to a designated recorder node. `enforceRecorder: true`
denies the session if the recorder is unreachable:

```json
{
  "action": "accept",
  "src": ["group:engineering"],
  "dst": ["tag:prod"],
  "users": ["ubuntu"],
  "recorder": ["tag:recorder"],
  "enforceRecorder": true
}
```

### Platform Support

| Platform | Support |
|----------|---------|
| Linux | Full (server and client) |
| macOS | Full (server and client) |
| Windows | Supported as SSH server |
| iOS / Android | Client only |

---

## Auth Keys

Auth keys authenticate devices to the tailnet without interactive SSO login.

### Key Types

| Type | Reusable | Ephemeral | Pre-authorized | Use Case |
|------|----------|-----------|----------------|----------|
| One-time | No | No | No | Single enrollment |
| Reusable | Yes | No | Optional | Batch provisioning |
| Ephemeral | Yes | Yes | Yes | CI/CD, containers |
| Tagged | Yes | Optional | Optional | Automated servers |

- **Ephemeral**: Devices are automatically removed from the tailnet on disconnect.
- **Pre-authorized**: Devices skip admin approval on enrollment.
- **Tagged**: Assigns tags to enrolled devices; tags must exist in `tagOwners`.

### Creating Auth Keys via API

```bash
curl -s -X POST https://api.tailscale.com/api/v2/tailnet/-/keys \
  -H "Authorization: Bearer $TS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": {
      "devices": {
        "create": {
          "reusable": true,
          "ephemeral": true,
          "preauthorized": true,
          "tags": ["tag:ci"]
        }
      }
    },
    "expirySeconds": 86400
  }'
```

### Using Auth Keys

```bash
tailscale up --auth-key=tskey-auth-<key>
```

Pass via environment variable in containers: `TS_AUTHKEY=tskey-auth-<key>`.

### Rotation Best Practices

- Set expiry to the shortest acceptable window (24h for CI/CD, 90 days for servers).
- Store keys in a secrets manager; never commit to source control.
- Use tagged keys so enrolled devices inherit the correct ACL posture automatically.
- Audit and revoke unused keys periodically.

When an auth key expires, existing enrolled devices are unaffected. The key can
no longer enroll new devices.

---

## OAuth Clients

OAuth clients provide API access and automated device registration without
per-user credentials. They are the preferred method for service accounts and
infrastructure automation.

Create in admin console: Settings > OAuth clients > Generate OAuth client.

| Scope | Purpose |
|-------|---------|
| `devices:read` | List and inspect devices |
| `devices:write` | Approve, delete, modify devices |
| `keys:write` | Create and revoke auth keys |
| `acl:write` | Modify tailnet policy |

OAuth clients can generate auth keys programmatically for automated enrollment:

```bash
TOKEN=$(curl -s -X POST https://api.tailscale.com/api/v2/oauth/token \
  -d "client_id=$TS_OAUTH_CLIENT_ID&client_secret=$TS_OAUTH_CLIENT_SECRET&grant_type=client_credentials" \
  | jq -r .access_token)
curl -s -X POST https://api.tailscale.com/api/v2/tailnet/-/keys \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"capabilities":{"devices":{"create":{"ephemeral":true,"preauthorized":true,"tags":["tag:ci"]}}}}'
```

OAuth client secrets do not expire by default. Rotate on a schedule or when
exposure is suspected.

---

## Key Expiry

Device key expiry controls how long a device remains authenticated to the tailnet
without re-authentication. The default is 180 days.

When a device's key expires, it loses tailnet connectivity until the user
re-authenticates or re-enrolls. The device remains visible in the admin console
until manually removed.

### Disabling Key Expiry for Servers

```bash
tailscale set --key-expiry=off

# Via API
curl -s -X POST "https://api.tailscale.com/api/v2/device/$DEVICE_ID/key" \
  -H "Authorization: Bearer $TS_API_KEY" \
  -d '{"keyExpiryDisabled": true}'
```

Disable key expiry for infrastructure nodes to prevent unexpected connectivity
loss. Keep expiry enabled for user devices to enforce periodic re-authentication.

---

## Ephemeral Nodes

Ephemeral nodes are enrolled with ephemeral auth keys and automatically removed
from the tailnet on disconnect. No manual cleanup is required.

| Use Case | Why Ephemeral |
|----------|--------------|
| CI/CD runners | Each job gets a fresh identity; no stale nodes accumulate |
| Docker containers | Container lifecycle matches tailnet membership |
| Kubernetes pods | Pod restarts create new ephemeral identities |
| Temporary access | Time-limited access without manual cleanup |

```bash
tailscale up --auth-key=tskey-auth-<ephemeral-key>
```

When an ephemeral node disconnects, Tailscale removes it within a few minutes.
Its Tailscale IP is released and it disappears from `tailscale status` on other
devices.

---

## Shields-Up Mode

Shields-up blocks all incoming connections from other tailnet devices. The device
can initiate outbound connections but cannot receive them.

```bash
tailscale set --shields-up
```

| Scenario | Benefit |
|----------|---------|
| Personal laptop on shared tailnet | Prevents colleagues from connecting |
| Mobile device | Reduces attack surface on untrusted networks |
| Developer workstation | Access tailnet resources without running services |

Shields-up does not affect Tailscale SSH initiated from the device, Taildrop
sends, or Serve/Funnel (handled by the daemon, not the OS firewall).

---

## Stateful Filtering

Subnet routers and exit nodes apply stateful packet filtering to traffic passing
through them. Stateful filtering tracks connection state and allows return traffic
for established connections without explicit rules.

Traffic entering the tailnet from a subnet router is subject to tailnet ACLs.
Traffic leaving toward the subnet is filtered by the subnet router's OS firewall.
Configure the OS firewall to restrict which tailnet IPs can reach which subnet
resources, providing defense in depth beyond tailnet ACLs.

Exit nodes route all internet-bound traffic from client devices. Apply egress
filtering on the exit node to restrict destinations:

```bash
# Linux exit node: block specific destinations
iptables -I FORWARD -s 100.64.0.0/10 -d 192.0.2.0/24 -j DROP
```

Tailscale does not manage OS-level firewall rules on exit nodes.

---

## Device Approval

Device approval controls whether new devices join automatically or require
administrator approval.

Approve via API:

```bash
curl -s -X POST "https://api.tailscale.com/api/v2/device/$DEVICE_ID/authorized" \
  -H "Authorization: Bearer $TS_API_KEY" \
  -d '{"authorized": true}'
```

Use `autoApprovers` in the tailnet policy file to approve devices automatically
based on tags. See `references/access-control.md` for syntax.

| Device Type | Recommended Approach |
|-------------|---------------------|
| Human-operated workstations | Manual approval |
| Tagged servers via automation | Pre-authorized key + autoApprovers |
| CI/CD runners | Pre-authorized ephemeral key |
| Contractor devices | Manual approval with expiry set |

---

## Identity Providers

Tailscale delegates user authentication to an external identity provider via
OIDC. Users authenticate to the IdP; Tailscale receives a verified identity claim.

| Provider | Notes |
|----------|-------|
| Google Workspace | Default; supports domain restriction |
| Microsoft Azure AD / Entra ID | Group sync available |
| Okta | Full SAML and OIDC; group sync available |
| GitHub | Organization and team restrictions |
| Custom OIDC | Any OIDC-compliant provider (Business/Enterprise plans) |

Configure in admin console: Settings > Identity Provider. Required: OIDC
discovery endpoint, client ID, client secret, and authorized redirect URI
(`https://login.tailscale.com/a/oauth_response`).

Azure AD and Okta support syncing IdP groups to Tailscale groups. Synced groups
appear in the policy file as `group:<name>` and update automatically when IdP
membership changes, eliminating manual group management.

---

## Security Hardening Checklist

**Access Control**

- [ ] No `*:*` rules in ACLs or grants.
- [ ] Server devices use tags; ACL rules do not reference individual usernames.
- [ ] `tests` section in policy file covers all critical access paths.
- [ ] Tailscale SSH enabled on servers; OS-level port 22 firewalled.
- [ ] SSH check mode enabled for privileged users on sensitive systems.

**Device Management**

- [ ] Key expiry disabled for infrastructure nodes; enabled for user devices.
- [ ] Ephemeral keys used for CI/CD and containers.
- [ ] Auth keys stored in a secrets manager; not in source control.
- [ ] Auth key expiry set to the minimum viable window.
- [ ] Device approval required for new enrollments.

**Network Security**

- [ ] Shields-up enabled on personal devices that do not serve traffic.
- [ ] Subnet router OS firewall restricts tailnet IP access to subnets.
- [ ] Exit node egress filtering applied where exit nodes are in use.
- [ ] Applications reference MagicDNS hostnames, not Tailscale IPs.

**Advanced**

- [ ] Tailnet Lock enabled for high-security tailnets; disablement secrets stored
      offline in separate locations.
- [ ] OAuth clients used for API automation; per-user API keys avoided for
      service accounts.
- [ ] Session recording enabled for privileged SSH with `enforceRecorder: true`.
- [ ] IdP group sync configured to eliminate manual group management.
- [ ] Audit log reviewed periodically (admin console > Logs).
