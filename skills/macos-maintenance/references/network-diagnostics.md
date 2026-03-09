# Network Diagnostics

Commands and workflows for diagnosing network issues on macOS.

## Quick Connectivity Test

```bash
# Internet connectivity
ping -c 3 8.8.8.8

# DNS resolution
ping -c 3 google.com

# If ping works but DNS doesn't → DNS issue
# If neither works → connectivity issue
```

## Network Interface Info

```bash
# List all interfaces
networksetup -listallhardwareports

# Current Wi-Fi network
networksetup -getairportnetwork en0 2>/dev/null

# IP address
ipconfig getifaddr en0

# Full IP configuration
ifconfig en0

# Default gateway
netstat -nr | grep default

# DNS servers in use
scutil --dns | grep "nameserver" | head -5

# All network services and their order
networksetup -listnetworkserviceorder
```

## DNS Diagnostics

```bash
# Resolve a domain
dscacheutil -q host -a name google.com

# Detailed DNS lookup
nslookup google.com

# Trace DNS resolution path
dig +trace google.com

# Check which DNS server is responding
dig google.com | grep "SERVER"

# Flush DNS cache
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

# Check /etc/hosts for overrides
cat /etc/hosts | grep -v "^#" | grep -v "^$"

# Check configured DNS servers
networksetup -getdnsservers Wi-Fi
```

**Common DNS fixes:**
- Flush cache (see above)
- Switch to public DNS: `networksetup -setdnsservers Wi-Fi 1.1.1.1 8.8.8.8`
- Reset to DHCP DNS: `networksetup -setdnsservers Wi-Fi empty`

## Wi-Fi Diagnostics

```bash
# Wi-Fi signal strength and channel
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I

# Key values:
#   agrCtlRSSI: signal strength (dBm, higher/closer to 0 = better)
#     -30 to -50: excellent
#     -50 to -60: good
#     -60 to -70: fair
#     -70 to -80: weak
#     below -80: very weak / unreliable
#   agrCtlNoise: background noise (more negative = less noise)
#   channel: current channel
#   lastTxRate: current connection speed

# Scan available networks
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s

# Wi-Fi interface details
system_profiler SPAirPortDataType

# Generate a Wi-Fi diagnostics report (saves to /var/tmp)
sudo /usr/bin/wdutil diagnose
```

**Wi-Fi troubleshooting steps:**
1. Check signal strength (RSSI above -60 is good)
2. Check for channel congestion (scan nearby networks)
3. Forget and re-join network
4. Renew DHCP lease: `sudo ipconfig set en0 DHCP`
5. Reset Wi-Fi: turn off, wait 10 seconds, turn on
6. Delete preferences: `sudo rm /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist` then restart
7. Create new network location: `networksetup -createlocation "Fresh" populate`

## Port & Firewall Testing

```bash
# Check if a port is open locally
lsof -i :8080

# Check if a remote port is reachable
nc -z -w 5 google.com 443 && echo "Open" || echo "Closed"

# List all listening ports
lsof -iTCP -sTCP:LISTEN -P -n

# Check firewall rules
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

## VPN Status

```bash
# List VPN configurations
scutil --nc list

# Check active VPN connections
ifconfig | grep -A1 "utun"

# Or check for common VPN processes
ps aux | grep -E "(openvpn|wireguard|tailscaled)" | grep -v grep
```

## Network Performance

```bash
# Bandwidth test (requires speedtest-cli)
# brew install speedtest-cli
speedtest-cli --simple 2>/dev/null

# Or use networkQuality (built-in macOS Monterey+)
networkQuality

# Route to a destination
traceroute google.com

# Packet loss test (30 pings)
ping -c 30 google.com | tail -3
# Look at packet loss percentage — any loss above 1% is concerning
```

## Proxy Settings

```bash
# Check proxy configuration
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
networksetup -getautoproxyurl Wi-Fi

# System-wide proxy environment
echo $http_proxy $https_proxy $no_proxy

# Disable all proxies
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off
networksetup -setautoproxystate Wi-Fi off
```

## Network Reset (Nuclear Option)

If all else fails, reset all network configuration:

```bash
# Remove all network preferences (requires restart)
sudo rm -rf /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist
sudo rm -rf /Library/Preferences/SystemConfiguration/com.apple.network.identification.plist
sudo rm -rf /Library/Preferences/SystemConfiguration/NetworkInterfaces.plist
sudo rm -rf /Library/Preferences/SystemConfiguration/preferences.plist

# Then restart
sudo shutdown -r now
```

This removes all saved Wi-Fi networks, custom DNS, proxy settings, and
network locations. The Mac will behave like a fresh setup for networking.
Only do this as a last resort.

## Common Network Issues Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No internet, Wi-Fi connected | DNS issue | Flush DNS, try 8.8.8.8 |
| Slow browsing | DNS or congestion | Switch DNS, check bandwidth |
| Can't connect to Wi-Fi | Auth/password | Forget network, re-join |
| VPN connected, no internet | Split tunnel config | Check VPN routing |
| Port not reachable | Firewall blocking | Check `socketfilterfw` rules |
| Intermittent drops | Weak signal or interference | Check RSSI, change channel |
| Works on Wi-Fi, not ethernet | Interface priority | Check service order |
| Captive portal not loading | DNS or proxy | Try `http://captive.apple.com` |
