# Tailscale Troubleshooting

Sources: Tailscale official documentation (2025-2026), community support patterns

## Master Failure Map

Start here. Match the symptom, confirm the likely cause, apply the quick fix.

| Symptom | Likely Cause | Quick Fix |
|---------|-------------|-----------|
| Device shows offline in admin console | `tailscaled` not running | Start daemon; re-run `tailscale up` |
| Auth URL printed on every `tailscale up` | Key expired or revoked | Re-authenticate; check key expiry in admin console |
| Ping succeeds but no TCP/UDP traffic | ACL denying the port | Add ACL rule; run policy test in admin console |
| All traffic goes through DERP relay | UDP blocked or symmetric NAT | Open UDP 41641; check `tailscale netcheck` |
| High latency to peer | Relay routing via distant DERP region | Verify direct path; check firewall for UDP |
| Intermittent drops every few minutes | Aggressive NAT or MTU mismatch | Lower MTU to 1280; check NAT keepalive |
| MagicDNS names not resolving | MagicDNS disabled or OS DNS conflict | Enable MagicDNS; fix resolver order |
| Split DNS not working on Linux | systemd-resolved not configured | Configure resolved stub listener |
| Subnet routes not reachable | Routes not approved or `--accept-routes` missing | Approve in admin console; re-run `tailscale up --accept-routes` |
| Exit node set but traffic leaks | Exit node not accepted on client | Run `tailscale up --exit-node=<IP>` |
| LAN unreachable while on exit node | Default behavior blocks LAN | Add `--exit-node-allow-lan-access` |
| `tailscale ping` succeeds but `ping` fails | OS firewall blocking ICMP | Allow ICMP on host firewall |
| macOS extension prompt never appeared | System extension blocked by MDM | Approve in System Settings > Privacy & Security |
| Linux: `tailscaled` fails to start | Missing `/dev/net/tun` or iptables conflict | Load `tun` module; check iptables rules |

---

## Connection Issues

### Daemon Not Running

`tailscale status` returns `failed to connect to local tailscaled` when the daemon is not running.

**Linux:**
```
sudo systemctl status tailscaled
sudo systemctl enable --now tailscaled
```

If the service fails to start, check `journalctl -u tailscaled -n 50` for the root cause. Common reasons: missing `/dev/net/tun`, conflicting VPN software holding the tun device, or iptables rules blocking the daemon's self-configuration.

**macOS:** The daemon runs as a system extension. If the Tailscale menu bar icon is absent, relaunch the app. If the extension is blocked, navigate to System Settings > Privacy & Security > Network Extensions and approve Tailscale.

**Windows:** Open Services (`services.msc`) and verify the Tailscale service is running. If it fails, check Event Viewer > Application for errors from `tailscale-ipn`.

### Authentication Expired or Revoked

Tailscale keys expire by default. When a key expires, the device disconnects and `tailscale up` prints a new auth URL.

Diagnosis: `tailscale status` shows `NeedsLogin`. The admin console shows the device as expired.

Fix: Run `tailscale up` and complete the auth flow. To prevent recurrence, enable key expiry disabled on the device in the admin console, or use an auth key with a longer lifetime for headless nodes.

For automated nodes, use pre-auth keys with `tailscale up --auth-key=<key>`. Rotate keys before expiry using the Tailscale API.

### Firewall Blocking UDP

Tailscale requires outbound UDP to establish direct connections. When UDP is blocked, all traffic routes through DERP relays, which increases latency and reduces throughput.

**Diagnosis:** Run `tailscale netcheck`. Look for:
- `UDP: false` — outbound UDP is completely blocked
- All DERP latencies present but no direct path in `tailscale status`
- `MappingVariesByDestIP: true` — symmetric NAT, harder to traverse

**Fix:** Open outbound UDP on port 41641 (or any UDP if the firewall is restrictive). Tailscale also uses UDP 3478 for STUN. If the firewall is stateful and allows return traffic, outbound-only rules suffice.

On corporate networks where UDP is blocked by policy, Tailscale falls back to DERP over HTTPS (TCP 443). This works but is slower. There is no workaround for environments that block all outbound traffic except HTTP/HTTPS.

### Relay-Only Connections

When `tailscale status` shows `relay` for a peer, the direct path failed. Causes:

| Cause | Indicator | Resolution |
|-------|-----------|------------|
| UDP blocked on one side | `netcheck` shows no UDP | Open UDP 41641 outbound |
| Symmetric NAT on both sides | `MappingVariesByDestIP: true` on both | Use a subnet router or relay is unavoidable |
| CGNAT (carrier-grade NAT) | Private IP in `100.x.x.x` range on WAN | Enable UPnP/PMP on router; or accept relay |
| Firewall blocking inbound | Direct path works one-way only | Open inbound UDP 41641 on the receiving side |

Symmetric NAT on both endpoints prevents direct connection regardless of firewall rules. In this case, relay is the only option unless one endpoint is moved to a network with full-cone or port-restricted NAT.

### High Latency

Direct connections should have latency close to the underlying network path. Relay connections add the round-trip to the DERP server.

**Diagnosis:**
1. `tailscale ping <peer>` — shows whether the path is direct or via relay, and which DERP region
2. `tailscale netcheck` — shows latency to each DERP region
3. Compare `tailscale ping` latency to `ping` latency on the same path

If the connection is direct but latency is high, the issue is geographic distance or the underlying network. If the connection is via relay, see the relay-only section above.

### Intermittent Drops

Connections that drop periodically and recover suggest NAT timeout or MTU issues.

**NAT timeout:** Aggressive NAT devices expire UDP mappings after 30–60 seconds of inactivity. Tailscale sends keepalives, but some NAT devices ignore them. Symptoms: drops during idle periods, recovery after a few seconds of traffic.

Fix: Reduce the NAT timeout on the router if accessible. Tailscale's keepalive interval is not user-configurable, but running periodic traffic (e.g., a ping loop) keeps the mapping alive.

**MTU mismatch:** WireGuard adds overhead to each packet. If the path MTU is 1500 and WireGuard overhead pushes packets over the limit, fragmentation or drops occur. Symptoms: large transfers fail or stall; small packets (ping) work fine.

Fix: Lower the MTU on the Tailscale interface. On Linux:
```
sudo ip link set tailscale0 mtu 1280
```
On macOS and Windows, Tailscale sets MTU automatically, but some VPN stacks interfere. 1280 is the safe minimum (IPv6 minimum MTU).

**Sleep/wake cycles:** On laptops, the WireGuard session must re-handshake after sleep. This takes 1–5 seconds. If applications time out during this window, configure them with longer connection timeouts or use TCP keepalives.

---

## DNS Issues

### MagicDNS Not Resolving

MagicDNS provides `<hostname>.<tailnet>.ts.net` resolution. If names do not resolve:

1. Verify MagicDNS is enabled in the admin console under DNS settings.
2. Run `tailscale status` and confirm the device is connected.
3. Check `tailscale dns status` (where available) to see the configured resolvers.
4. Test with `dig @100.100.100.100 <hostname>.<tailnet>.ts.net` — this queries the Tailscale DNS proxy directly. If this works but system resolution fails, the OS DNS configuration is the problem.

### Split DNS Conflicts

Split DNS routes specific domains to designated resolvers while leaving other traffic to the default resolver. Conflicts arise when the OS DNS stack does not support per-domain routing.

**Linux with systemd-resolved:**

systemd-resolved supports per-interface DNS with domain routing. Tailscale configures this automatically when `systemd-resolved` is the active resolver. Verify:
```
resolvectl status tailscale0
```
The output should show the Tailscale DNS server (`100.100.100.100`) and the tailnet domain. If it does not, ensure `systemd-resolved` is running and that `/etc/resolv.conf` is a symlink to the stub resolver:
```
ls -la /etc/resolv.conf
# Should point to /run/systemd/resolve/stub-resolv.conf
```
If it points elsewhere, Tailscale cannot configure split DNS. Fix:
```
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

**Linux with NetworkManager:**

NetworkManager can conflict with systemd-resolved. Check whether NetworkManager is managing DNS:
```
cat /etc/NetworkManager/NetworkManager.conf | grep dns
```
If `dns=default`, NetworkManager overwrites `/etc/resolv.conf`. Set `dns=systemd-resolved` and restart NetworkManager.

**macOS:**

macOS uses a per-interface DNS resolver system. Tailscale injects resolvers via the system configuration. Conflicts arise when third-party VPNs or DNS tools (e.g., dnsmasq, Little Snitch) intercept DNS before Tailscale's resolver.

Check active resolvers: `scutil --dns`. The Tailscale resolver should appear for the tailnet domain. If another resolver appears first for the same domain, it takes precedence.

**Windows:**

Windows DNS resolution follows interface metric order. Tailscale sets a low metric on its interface to take priority. If another VPN or network adapter has a lower metric, it wins. Check with `Get-NetIPInterface` in PowerShell and compare interface metrics.

### DNS64 on IPv6-Only Networks

Some mobile networks and cloud environments provide IPv6-only connectivity with DNS64/NAT64 for IPv4 access. Tailscale operates over IPv6 in these environments, but DNS64 can interfere with MagicDNS if the synthesized AAAA records conflict with Tailscale's `100.x.x.x` addresses.

Symptom: MagicDNS resolves names to synthesized IPv6 addresses instead of Tailscale IPs, causing connection failures.

Fix: Ensure the Tailscale DNS proxy (`100.100.100.100`) is queried before the network's DNS64 resolver for tailnet domains. On iOS and Android, Tailscale handles this automatically. On Linux, configure systemd-resolved to route the tailnet domain to `100.100.100.100` explicitly.

---

## Subnet Routing Issues

### Routes Advertised but Not Approved

Advertising a subnet route with `--advertise-routes` does not make it active. An admin must approve the route in the admin console under the device's settings.

Diagnosis: `tailscale status` on the advertising node shows the routes as advertised. Peers cannot reach the subnet. The admin console shows the device with unapproved routes.

Fix: Log into the admin console, navigate to the device, and approve the advertised routes. Routes take effect within seconds of approval.

### Routes Approved but Clients Not Accepting

Even after approval, clients must opt in to use subnet routes.

Diagnosis: `tailscale status` on the client does not show the subnet in the routing table. `tailscale ip -4` shows the Tailscale IP but `ip route` (Linux) or `route print` (Windows) does not show the subnet.

Fix: Re-run `tailscale up` with `--accept-routes`:
```
tailscale up --accept-routes
```
This flag persists across reconnects. Verify with `tailscale status` — the subnet router should appear with the routes listed.

### Overlapping Subnets

If the advertised subnet overlaps with the client's local network, the client cannot use the route because the local route takes precedence.

Example: Advertising `192.168.1.0/24` to a client that is also on `192.168.1.0/24` locally. The client's kernel routes local traffic directly and never sends it through Tailscale.

Diagnosis: Traffic to the subnet reaches local devices instead of the remote subnet. `ip route get <subnet-IP>` shows the local interface, not `tailscale0`.

Fix: There is no automatic resolution. Options:
1. Re-number one of the networks to eliminate the overlap.
2. Use a more specific route on the client side (not possible with Tailscale's route acceptance model).
3. Use a jump host within the remote subnet to access resources.

### SNAT Behavior

By default, subnet routers perform source NAT (SNAT), replacing the client's Tailscale IP with the router's local IP before forwarding to the subnet. This means devices on the subnet see traffic originating from the router, not the Tailscale client.

Consequences:
- Firewall rules on subnet devices based on source IP will not match Tailscale client IPs.
- Return traffic routes correctly because the router handles the NAT translation.
- Logging on subnet devices shows the router's IP, not the originating client.

To disable SNAT and preserve source IPs, the subnet's default gateway must route `100.64.0.0/10` back through the Tailscale subnet router. This requires modifying the subnet's routing infrastructure and is only practical in controlled environments.

---

## Exit Node Issues

### Traffic Not Routing Through Exit Node

Setting an exit node routes all non-Tailscale traffic through that node. If traffic still exits locally:

1. Verify the exit node is configured: `tailscale status` should show the exit node with `(exit node)`.
2. Confirm the exit node has `--advertise-exit-node` set and the route is approved in the admin console.
3. Check that the client ran `tailscale up --exit-node=<IP or hostname>`.
4. Verify with `curl https://ifconfig.me` — the returned IP should be the exit node's public IP.

If the exit node is set but traffic still leaks, check for split-tunnel VPNs or browser-level proxies that bypass the system routing table.

### DNS Leaks When Using Exit Node

When an exit node is active, DNS queries should also route through the exit node to prevent leaking the user's browsing intent to the local network's DNS resolver.

Tailscale routes DNS through the exit node automatically when MagicDNS is enabled. If MagicDNS is disabled, the OS uses its configured DNS servers, which may be local.

Verify: Use a DNS leak test service. If queries appear from the local ISP rather than the exit node's network, enable MagicDNS or configure the OS to use a DNS server reachable only through the exit node.

### LAN Access While on Exit Node

By default, enabling an exit node blocks access to the local LAN. This prevents split-tunneling that could expose the local network.

Fix: Add `--exit-node-allow-lan-access` when setting the exit node:
```
tailscale up --exit-node=<IP> --exit-node-allow-lan-access
```
This allows traffic to RFC 1918 addresses on the local interface while routing all other traffic through the exit node.

---

## ACL and Policy Issues

### Traffic Denied Unexpectedly

Tailscale's default policy (when no ACLs are defined) allows all traffic between all devices. Once any ACL rule is added, the policy becomes deny-by-default for traffic not explicitly permitted.

Diagnosis:
1. `tailscale ping <peer>` — if this succeeds, the WireGuard tunnel is up. If TCP/UDP traffic fails, ACLs are the likely cause.
2. Use the policy test tool in the admin console: enter source, destination, and port to see which rule applies.
3. Check `tailscale status` to confirm both devices are in the same tailnet and not isolated by tags.

Common mistakes:
- Forgetting to allow traffic in both directions (ACLs are directional by default unless using `grants`).
- Tag-based rules that do not match because the device lacks the expected tag.
- Rules that allow a port but not the protocol (TCP vs UDP).

### Grants vs ACLs

`grants` (introduced in newer policy syntax) are bidirectional and attach capabilities to the connection rather than just permitting traffic. Conflicts arise when both `acls` and `grants` blocks exist in the same policy file.

If a `grants` block permits traffic but an `acls` block denies it (or vice versa), the more restrictive rule applies. Audit the policy file for both blocks and ensure they are consistent.

---

## Interpreting `tailscale netcheck` Output

`tailscale netcheck` probes the network environment and reports connectivity capabilities. Run it when diagnosing connection or relay issues.

| Field | Meaning | Action if Problematic |
|-------|---------|----------------------|
| `UDP: true/false` | Whether outbound UDP works | If false, open UDP 41641 outbound |
| `IPv4: yes (x.x.x.x:port)` | Public IPv4 address and port | Note if port changes between runs (symmetric NAT) |
| `IPv6: yes/no` | IPv6 connectivity | No action needed; Tailscale works over IPv4 |
| `MappingVariesByDestIP: true` | Symmetric NAT detected | Direct connections to other symmetric NAT peers will fail |
| `PortMapping: UPnP/PMP/PCP` | Router supports port mapping | Tailscale uses this to improve direct connectivity |
| DERP latency table | Latency to each relay region | High latency to all regions suggests network issues |
| `PreferredDERP` | The relay region Tailscale will use | Should be geographically close |

**Symmetric NAT (`MappingVariesByDestIP: true`):** The NAT device assigns a different external port for each destination. This prevents the STUN-based hole-punching that Tailscale uses for direct connections. If both peers are behind symmetric NAT, all traffic routes through DERP. Moving one peer to a network with a less restrictive NAT resolves this.

**No DERP latency data:** If all DERP regions show no latency, outbound HTTPS (TCP 443) may be blocked. DERP fallback requires TCP 443 to Tailscale's relay servers.

---

## Bug Reports and Support

When escalating to Tailscale support or filing a bug report, collect the following:

1. **Bug report:** `tailscale bugreport` generates a report ID. Share this ID with support — it includes logs, network state, and configuration without exposing private keys or traffic content.

2. **Status output:** `tailscale status --json` provides machine-readable peer state.

3. **Netcheck output:** `tailscale netcheck` shows the network environment at the time of the issue.

4. **Platform logs:** See the log locations section below.

5. **Reproduction steps:** Exact commands run, expected behavior, actual behavior, and timestamps.

Do not share the contents of `/var/lib/tailscale/` or equivalent state directories — these contain private keys.

---

## Log File Locations

| Platform | Log Location |
|----------|-------------|
| Linux (systemd) | `journalctl -u tailscaled` |
| Linux (non-systemd) | `/var/log/tailscaled.log` (if configured) |
| macOS | `log show --predicate 'process == "tailscaled"' --last 1h` |
| macOS (app log) | `~/Library/Logs/Tailscale/` |
| Windows | Event Viewer > Applications and Services Logs > Tailscale |
| Windows (file) | `%LOCALAPPDATA%\Tailscale\tailscale-ipn.log` |
| iOS | Settings > Privacy > Analytics > Analytics Data > Tailscale |
| Android | `adb logcat -s Tailscale` |

For Linux, increase log verbosity by adding `--verbose=1` to the `tailscaled` invocation in the systemd unit file, then restart the service.

---

## Platform-Specific Issues

### macOS

**System extension not approved:** Tailscale requires a system extension (network extension) to create the VPN interface. On first install, macOS prompts for approval. If the prompt was dismissed or blocked by MDM, navigate to System Settings > Privacy & Security > Network Extensions and approve Tailscale manually.

**App Store vs standalone:** The App Store version and the standalone (Homebrew or direct download) version cannot coexist. If both are installed, remove one. The App Store version uses a different bundle ID and may have different entitlements.

**VPN conflicts:** macOS allows only one VPN configuration to be active at a time in some configurations. If another VPN (Cisco AnyConnect, GlobalProtect, etc.) is active, it may conflict with Tailscale's network extension. Check System Settings > VPN for conflicting configurations.

**CLI not in PATH:** The App Store version installs the CLI inside the app bundle. Add it to PATH or create an alias:
```
alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
```

### Windows

**Windows Firewall blocking traffic:** Windows Firewall may block inbound connections on the Tailscale interface. Tailscale adds firewall rules during installation, but these can be removed by security software or group policy. Verify with:
```
netsh advfirewall firewall show rule name="Tailscale"
```
If rules are missing, reinstall Tailscale or add rules manually for the `tailscale0` interface.

**Admin privileges:** Some Tailscale operations require elevation. If `tailscale up` fails with a permissions error, run the command prompt as Administrator.

**Antivirus interference:** Some antivirus products intercept network traffic and interfere with WireGuard's UDP packets. Add Tailscale's binary and the `tailscale0` interface to the antivirus exclusion list if drops or failures occur after antivirus installation.

### Linux

**`/dev/net/tun` missing:** Tailscale requires the TUN kernel module. If it is not loaded:
```
sudo modprobe tun
echo tun | sudo tee /etc/modules-load.d/tun.conf  # persist across reboots
```
In containers, the host must pass through `/dev/net/tun` or grant `NET_ADMIN` capability.

**iptables conflicts:** Tailscale manages its own iptables rules. If another tool (Docker, firewalld, ufw) manages iptables aggressively, rules may conflict. Check for rules that drop or reject traffic on the `tailscale0` interface:
```
sudo iptables -L -n -v | grep tailscale
```
If firewalld is active, add `tailscale0` to the trusted zone:
```
sudo firewall-cmd --zone=trusted --add-interface=tailscale0 --permanent
sudo firewall-cmd --reload
```

**Kernel version:** WireGuard is built into the Linux kernel from 5.6 onward. On older kernels, Tailscale uses a userspace WireGuard implementation, which is slower. Upgrade the kernel or install the WireGuard DKMS module for better performance.

### iOS and Android

**Background restrictions:** Mobile operating systems aggressively suspend background apps. Tailscale may disconnect when the device is idle. On iOS, ensure Background App Refresh is enabled for Tailscale. On Android, disable battery optimization for Tailscale in Settings > Battery > Battery Optimization.

**Android battery optimization:** Even with battery optimization disabled, some Android OEM skins (MIUI, One UI) have additional background process restrictions. Check the manufacturer's documentation for disabling these restrictions for specific apps.

**iOS VPN profile:** Tailscale installs a VPN profile on iOS. If the profile is deleted from Settings > VPN & Device Management, Tailscale loses connectivity. Re-enable Tailscale from the app to reinstall the profile.

---

## Performance Diagnostics

### Measuring Throughput

Use `iperf3` to measure throughput over the Tailscale tunnel:

On the server (receiver):
```
iperf3 -s
```
On the client:
```
iperf3 -c <tailscale-ip-of-server>
```

Compare results over the Tailscale tunnel vs the direct network path. A significant gap indicates encryption overhead, relay routing, or MTU issues.

For UDP throughput (relevant for media or real-time applications):
```
iperf3 -c <tailscale-ip> -u -b 100M
```

### CPU Usage from tailscaled

WireGuard encryption is CPU-intensive on platforms without hardware acceleration. On older or low-power devices (Raspberry Pi, embedded routers), `tailscaled` may consume significant CPU during high-throughput transfers.

Check CPU usage:
```
top -p $(pgrep tailscaled)
```

If CPU is the bottleneck, reduce throughput expectations or upgrade hardware. On Linux with kernel WireGuard (5.6+), the kernel handles encryption more efficiently than userspace.

### MTU Optimization

The default MTU for Tailscale is 1280 bytes (conservative). On paths where the underlying MTU is known to be 1500, increasing the Tailscale MTU improves throughput by reducing packet overhead.

Test path MTU:
```
ping -M do -s 1400 <tailscale-ip>
```
Increase the size until packets are fragmented or dropped. Set the Tailscale interface MTU to the largest working size minus WireGuard overhead (approximately 80 bytes):
```
sudo ip link set tailscale0 mtu 1420
```
Tailscale sets this automatically on most platforms, but manual adjustment may be needed when the path MTU is non-standard.
