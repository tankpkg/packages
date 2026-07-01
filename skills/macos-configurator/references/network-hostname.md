# Network and Hostname Configuration

Sources: Apple networksetup(8) man page, Apple scutil(8) man page, mathiasbynens/dotfiles

This file covers network configuration and hostname management. Network diagnostics
(ping, traceroute, interface health) are handled by @tank/macos-maintenance.

---

## 1. Network Services

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# List logical services, hardware ports, and service order
networksetup -listallnetworkservices
networksetup -listallhardwareports        # shows device names: en0, en1, etc.
networksetup -listnetworkserviceorder

# Get full info for a service (IP, subnet, router, DNS)
networksetup -getinfo "Wi-Fi"

# Enable or disable a service
$SUDO networksetup -setnetworkserviceenabled "Bluetooth PAN" off

# Reorder services (first active wins for routing)
$SUDO networksetup -ordernetworkservices "Ethernet" "Wi-Fi" "Bluetooth PAN"
```

---

## 2. DNS Configuration

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# Set DNS servers for a service
$SUDO networksetup -setdnsservers "Wi-Fi" 1.1.1.1 1.0.0.1
$SUDO networksetup -setdnsservers "Ethernet" 8.8.8.8 8.8.4.4

# Read current DNS
networksetup -getdnsservers "Wi-Fi"

# Reset to DHCP-assigned DNS
$SUDO networksetup -setdnsservers "Wi-Fi" "Empty"

# Set search domains
$SUDO networksetup -setsearchdomains "Wi-Fi" local.example.com example.com
$SUDO networksetup -setsearchdomains "Wi-Fi" "Empty"   # clear

# Flush DNS cache
$SUDO dscacheutil -flushcache && $SUDO killall -HUP mDNSResponder

# Verify resolver configuration
scutil --dns
```

### Common DNS Providers

| Provider   | Primary          | Secondary         | Notes                        |
|------------|------------------|-------------------|------------------------------|
| Cloudflare | 1.1.1.1          | 1.0.0.1           | Fastest globally, privacy-focused |
| Google     | 8.8.8.8          | 8.8.4.4           | Reliable, widely supported   |
| Quad9      | 9.9.9.9          | 149.112.112.112   | Blocks malicious domains     |
| OpenDNS    | 208.67.222.222   | 208.67.220.220    | Parental controls available  |

---

## 3. Proxy Configuration

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# HTTP proxy
$SUDO networksetup -setwebproxy "Wi-Fi" proxy.example.com 8080
$SUDO networksetup -setwebproxystate "Wi-Fi" on
$SUDO networksetup -setwebproxystate "Wi-Fi" off
networksetup -getwebproxy "Wi-Fi"

# HTTPS proxy
$SUDO networksetup -setsecurewebproxy "Wi-Fi" proxy.example.com 8080
$SUDO networksetup -setsecurewebproxystate "Wi-Fi" on
$SUDO networksetup -setsecurewebproxystate "Wi-Fi" off

# Auto-proxy (PAC file)
$SUDO networksetup -setautoproxyurl "Wi-Fi" http://proxy.example.com/proxy.pac
$SUDO networksetup -setautoproxystate "Wi-Fi" on

# SOCKS proxy (e.g., SSH tunnel on localhost)
$SUDO networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 1080
$SUDO networksetup -setsocksfirewallproxystate "Wi-Fi" on
$SUDO networksetup -setsocksfirewallproxystate "Wi-Fi" off

# Bypass domains
$SUDO networksetup -setproxybypassdomains "Wi-Fi" localhost 127.0.0.1 "*.local" "*.example.com"
networksetup -getproxybypassdomains "Wi-Fi"
```

---

## 4. IP Configuration

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# Static IP
$SUDO networksetup -setmanual "Ethernet" 192.168.1.100 255.255.255.0 192.168.1.1

# Switch back to DHCP
$SUDO networksetup -setdhcp "Wi-Fi"

# Renew DHCP lease
$SUDO ipconfig set en0 DHCP

# IPv6
$SUDO networksetup -setv6automatic "Wi-Fi"
$SUDO networksetup -setv6off "Wi-Fi"
$SUDO networksetup -setv6manual "Wi-Fi" 2001:db8::1 64 2001:db8::1
```

---

## 5. Wi-Fi

```bash
# Current network and power state
networksetup -getairportnetwork en0
networksetup -getairportpower en0

# Connect to a network
networksetup -setairportnetwork en0 "NetworkName" "password"

# Turn Wi-Fi on/off
networksetup -setairportpower en0 on
networksetup -setairportpower en0 off

# Preferred networks
networksetup -listpreferredwirelessnetworks en0
networksetup -addpreferredwirelessnetworkatindex en0 "NetworkName" 0 WPA2 "password"
networksetup -removepreferredwirelessnetwork en0 "NetworkName"
networksetup -removeallpreferredwirelessnetworks en0
```

The `airport` CLI is deprecated as of macOS Sonoma. Use `wdutil` instead:

```bash
SUDO="${SUDO:-$(command -v sudo)}"
$SUDO wdutil scan    # scan for available networks
$SUDO wdutil info    # show current Wi-Fi details
```

---

## 6. Hostname

macOS maintains three distinct name identifiers:

| Name          | scutil key       | Purpose                                        |
|---------------|------------------|------------------------------------------------|
| ComputerName  | `ComputerName`   | Friendly display name in Finder and Sharing    |
| HostName      | `HostName`       | BSD/UNIX hostname, shown in shell prompt       |
| LocalHostName | `LocalHostName`  | Bonjour `.local` mDNS name — no spaces allowed |

Set all three for consistency:

```bash
SUDO="${SUDO:-$(command -v sudo)}"
$SUDO scutil --set ComputerName "My MacBook Pro"
$SUDO scutil --set HostName "my-macbook-pro"
$SUDO scutil --set LocalHostName "my-macbook-pro"

# Also available via networksetup (syncs ComputerName)
$SUDO networksetup -setcomputername "My MacBook Pro"

# Read current values
scutil --get ComputerName
scutil --get HostName
scutil --get LocalHostName
```

`LocalHostName` must contain only letters, digits, and hyphens. Changes take effect
immediately; a restart ensures all services pick up the new name.

---

## 7. Firewall

### Application Firewall (socketfilterfw)

```bash
SUDO="${SUDO:-$(command -v sudo)}"
FIREWALL=/usr/libexec/ApplicationFirewall/socketfilterfw

# State
$SUDO $FIREWALL --getglobalstate
$SUDO $FIREWALL --setglobalstate on
$SUDO $FIREWALL --setglobalstate off

# Stealth mode (no response to ICMP or port probes)
$SUDO $FIREWALL --setstealthmode on
$SUDO $FIREWALL --setstealthmode off

# Block all incoming connections
$SUDO $FIREWALL --setblockall on
$SUDO $FIREWALL --setblockall off

# Per-application rules
$SUDO $FIREWALL --listapps
$SUDO $FIREWALL --add /Applications/MyApp.app
$SUDO $FIREWALL --blockapp /Applications/MyApp.app
$SUDO $FIREWALL --unblockapp /Applications/MyApp.app
$SUDO $FIREWALL --remove /Applications/MyApp.app

# Logging
$SUDO $FIREWALL --setloggingmode on
```

### Packet Filter (pfctl)

```bash
SUDO="${SUDO:-$(command -v sudo)}"
$SUDO pfctl -s info          # status
$SUDO pfctl -s rules         # show rules
$SUDO pfctl -e               # enable pf
$SUDO pfctl -d               # disable pf
$SUDO pfctl -f /etc/pf.conf  # load rules file
$SUDO pfctl -n -f /etc/pf.conf  # test without loading
$SUDO pfctl -F all           # flush all rules
```

Minimal rule to block an inbound port — add to `/etc/pf.conf`, then reload:

```
block in proto tcp from any to any port 23
```

---

## 8. VPN

VPN connections configured in System Settings are managed via `scutil --nc`:

```bash
# List all VPN connections
scutil --nc list

# Status of a connection
scutil --nc status "My VPN"

# Start / stop
scutil --nc start "My VPN"
scutil --nc start "My VPN" --user username --password "secret"
scutil --nc stop "My VPN"

# Extended status (server address, assigned IP)
scutil --nc show "My VPN"
```

The connection name must match exactly as shown in `scutil --nc list`.
IKEv2, L2TP, and Cisco IPSec connections are all accessible via this interface.

---

## 9. AirDrop

```bash
# Allow AirDrop from Everyone (not just Contacts)
defaults write com.apple.NetworkBrowser BrowseAllInterfaces -bool true
killall Finder

# Revert to Contacts only
defaults delete com.apple.NetworkBrowser BrowseAllInterfaces
killall Finder
```

AirDrop requires both Wi-Fi and Bluetooth to be active.

---

## 10. Network Time

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# Check and toggle network time sync
$SUDO systemsetup -getusingnetworktime
$SUDO systemsetup -setusingnetworktime on
$SUDO systemsetup -setusingnetworktime off

# Read and set NTP server
$SUDO systemsetup -getnetworktimeserver
$SUDO systemsetup -setnetworktimeserver time.apple.com
$SUDO systemsetup -setnetworktimeserver pool.ntp.org

# Force immediate sync
$SUDO sntp -sS time.apple.com
```

Common NTP servers: `time.apple.com` (default), `time.google.com`, `pool.ntp.org`,
`time.cloudflare.com`.

Note: `systemsetup` may silently fail on Apple Silicon with SIP enabled. Verify
each change with the corresponding `-get` command.

---

## Quick Reference

```bash
SUDO="${SUDO:-$(command -v sudo)}"
# Full network reset for a service
$SUDO networksetup -setdhcp "Wi-Fi"
$SUDO networksetup -setdnsservers "Wi-Fi" 1.1.1.1 1.0.0.1
$SUDO networksetup -setsearchdomains "Wi-Fi" "Empty"
$SUDO networksetup -setwebproxystate "Wi-Fi" off
$SUDO networksetup -setsecurewebproxystate "Wi-Fi" off
$SUDO networksetup -setsocksfirewallproxystate "Wi-Fi" off
$SUDO dscacheutil -flushcache && $SUDO killall -HUP mDNSResponder

# Set hostname consistently
$SUDO scutil --set ComputerName "mymac"
$SUDO scutil --set HostName "mymac"
$SUDO scutil --set LocalHostName "mymac"

# Enable firewall with stealth mode
FIREWALL=/usr/libexec/ApplicationFirewall/socketfilterfw
$SUDO $FIREWALL --setglobalstate on
$SUDO $FIREWALL --setstealthmode on
```
