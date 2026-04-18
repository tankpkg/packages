---
name: "@tank/tailscale-expert"
description: |
  Tailscale mesh VPN configuration, administration, and troubleshooting.
  Covers the complete CLI (up, down, status, set, serve, funnel, lock, cert,
  file, drive, dns, ping, netcheck, bugreport, exit-node), tailnet policy
  file authoring (HuJSON ACLs, grants, groups, tags, autoApprovers, SSH
  rules, tests), networking (subnet routers, exit nodes, app connectors,
  MagicDNS, DERP relays, NAT traversal), security (Tailnet Lock, HTTPS
  certificates, Tailscale SSH, auth keys, key expiry, ephemeral nodes),
  service exposure (Serve, Funnel, Taildrop, Drive), and integrations
  (Docker, Kubernetes operator, cloud-init, Headscale, NAS, CI/CD, tsnet).
  Synthesizes Tailscale official documentation (2025-2026), WireGuard
  protocol specification, and production deployment patterns.

  Trigger phrases: "tailscale", "tailscale up", "tailscale down",
  "tailscale status", "tailscale set", "tailscale serve", "tailscale funnel",
  "tailscale lock", "tailscale cert", "tailscale ssh", "tailscale dns",
  "tailscale ping", "tailscale netcheck", "tailscale file", "tailscale drive",
  "tailnet", "tailnet policy", "tailscale ACL", "tailscale grants",
  "tailscale subnet router", "tailscale exit node", "MagicDNS",
  "DERP relay", "tailscale docker", "tailscale kubernetes",
  "tailscale k8s operator", "headscale", "taildrop", "tailscale VPN",
  "tailscale troubleshooting", "wireguard mesh", "tailscale auth key",
  "tailnet lock", "tailscale HTTPS", "app connector",
  "tailscale CI/CD", "tailscale GitHub Actions"
---

# Tailscale Expert

Configure, administer, and troubleshoot Tailscale mesh VPN networks. Covers
the complete lifecycle from device enrollment through production hardening,
access control, service exposure, and debugging connectivity issues.

## Core Philosophy

1. **Verify connectivity first** -- Run `tailscale status` and `tailscale
   netcheck` before any configuration change to establish a baseline.
2. **Deny-by-default** -- Tailscale ACLs deny all traffic unless explicitly
   allowed. Start restrictive, open selectively. Use `tests` in your policy
   file to validate rules before applying.
3. **Tags for machines, groups for humans** -- Tag server-class devices
   (`tag:prod`, `tag:k8s`) and organize users into groups (`group:devops`).
   ACLs reference tags/groups, never individual IPs or usernames.
4. **Prefer grants over legacy ACLs** -- Grants are the next-generation
   access control syntax. They support application-layer permissions and all
   legacy ACL functionality. Use grants for new policies.
5. **Auth keys for automation, interactive login for humans** -- Use
   `--auth-key` with ephemeral, pre-authorized keys for CI/CD and containers.
   Reserve interactive SSO login for human-operated devices.

## Quick-Start

### "I want to connect a device to my tailnet"

| Step | Action |
|------|--------|
| 1 | Install: `curl -fsSL https://tailscale.com/install.sh \| sh` |
| 2 | Start: `sudo tailscale up` |
| 3 | Authenticate via the URL printed to terminal |
| 4 | Verify: `tailscale status` |
-> See `references/cli-commands.md`

### "I need to write access control policies"

| Step | Action |
|------|--------|
| 1 | Open admin console: Access Controls page |
| 2 | Define groups and tags in policy file |
| 3 | Write grants (preferred) or ACLs |
| 4 | Add `tests` section to validate rules |
| 5 | Preview changes before saving |
-> See `references/access-control.md`

### "I want to expose a local service"

| Need | Tool | Command |
|------|------|---------|
| Within tailnet only | Serve | `tailscale serve http://localhost:3000` |
| To the public internet | Funnel | `tailscale funnel http://localhost:3000` |
| Share files between devices | Taildrop | `tailscale file cp file.txt targethost:` |
-> See `references/serve-funnel-sharing.md`

### "Something isn't connecting"

| Symptom | First Step |
|---------|------------|
| Can't reach any device | `tailscale status` -- check if connected |
| Relay-only connection (slow) | `tailscale ping <host>` -- check if direct path exists |
| DNS not resolving | `tailscale dns status` -- check MagicDNS config |
| Subnet route not working | Verify route is advertised AND approved in admin |
| Firewall blocking | `tailscale netcheck` -- check UDP/41641 and DERP |
-> See `references/troubleshooting.md`

## Decision Trees

### Routing Strategy

| Need | Feature | Reference |
|------|---------|-----------|
| Access remote LAN from tailnet | Subnet router | `references/networking-routing.md` |
| Route all internet traffic through a node | Exit node | `references/networking-routing.md` |
| Route specific domains through tailnet | App connector | `references/networking-routing.md` |
| Custom DNS for tailnet devices | MagicDNS + split DNS | `references/networking-routing.md` |

### Authentication Method

| Scenario | Method |
|----------|--------|
| Human on personal device | Interactive SSO login (`tailscale up`) |
| Server/VM in automation | Auth key (`--auth-key=tskey-auth-...`) |
| Docker container | Auth key or OAuth client secret via env var |
| Kubernetes pod | Kubernetes operator with OAuth client |
| CI/CD runner | Ephemeral auth key (auto-cleanup on disconnect) |
| Headscale (self-hosted) | `--login-server=https://your-headscale.example.com` |
-> See `references/security-features.md`

### Service Exposure

| Audience | Feature | Port Requirement |
|----------|---------|-----------------|
| Tailnet devices only | `tailscale serve` | None (WireGuard handles it) |
| Public internet | `tailscale funnel` | Ports 443, 8443, 10000 only |
| File transfer | `tailscale file cp` | None |
| Network drive sharing | `tailscale drive share` | WebDAV via SMB |
-> See `references/serve-funnel-sharing.md`

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Use `*:*` in ACLs permanently | Define specific ports and protocols | Defeats zero-trust; hard to audit |
| Hardcode Tailscale IPs in config | Use MagicDNS hostnames | IPs change; DNS names are stable |
| Skip `tests` in policy file | Write test assertions for every ACL rule | Prevents accidental lockouts |
| Use reusable auth keys for servers | Use ephemeral + pre-authorized keys | Ephemeral nodes auto-cleanup on disconnect |
| Run `tailscale up` with flags repeatedly | Use `tailscale set` for runtime changes | `set` modifies without re-auth; `up` may force re-auth |
| Approve subnet routes without ACLs | Restrict who can reach advertised routes | Approved routes are visible to everyone by default |
| Expose services via Funnel without rate limiting | Add application-level auth or rate limits | Funnel is public; Tailscale doesn't rate-limit for you |

## Reference Files

| File | Contents |
|------|----------|
| `references/cli-commands.md` | All CLI commands organized by category (connectivity, networking, services, diagnostics, administration), key flags for each, common usage patterns, tailscaled daemon configuration |
| `references/access-control.md` | Tailnet policy file syntax (HuJSON), ACLs vs grants comparison, groups, tags, tagOwners, autoApprovers, SSH rules, hosts, tests, postures, ipsets, nodeAttrs, GitOps workflow |
| `references/networking-routing.md` | Subnet routers (setup, HA, split DNS), exit nodes (config, Mullvad), app connectors, MagicDNS, DNS configuration, DERP relay system, NAT traversal, WireGuard fundamentals |
| `references/security-features.md` | Tailnet Lock (init, sign, manage), HTTPS certificates (Let's Encrypt via tailscale cert), Tailscale SSH (ACL rules, session recording), auth keys (types, rotation), key expiry, ephemeral nodes, shields-up |
| `references/serve-funnel-sharing.md` | Tailscale Serve (HTTP/HTTPS/TCP proxy, TLS termination), Funnel (public exposure, port restrictions), Taildrop (file transfer), Tailscale Drive (WebDAV shares), node sharing |
| `references/integrations.md` | Docker (sidecar, userspace, compose), Kubernetes operator (ingress, egress, Connector CRD), cloud-init, NAS (Synology, QNAP), routers (OpenWrt, pfSense), CI/CD (GitHub Actions), Headscale, tsnet (Go library) |
| `references/troubleshooting.md` | Failure map (symptom -> cause -> fix), netcheck output interpretation, bugreport usage, DERP relay debugging, platform-specific issues (macOS, Windows, Linux, mobile), log locations, performance diagnostics |
