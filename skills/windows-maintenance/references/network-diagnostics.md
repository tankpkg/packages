# Windows Network Diagnostics

Commands and workflows for diagnosing network issues on Windows 10/11.
All PowerShell.

## Quick Connectivity Test

```powershell
# Internet connectivity
Test-NetConnection -ComputerName 8.8.8.8

# DNS resolution
Test-NetConnection -ComputerName google.com

# If ping works but DNS doesn't — DNS issue
# If neither works — connectivity issue
```

## Network Interface Info

```powershell
# All adapters with status
Get-NetAdapter | Select-Object Name, Status, LinkSpeed, MacAddress

# IP configuration
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } |
  Select-Object InterfaceAlias, IPAddress, PrefixLength

# Default gateway
Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object NextHop, InterfaceAlias

# DNS servers
Get-DnsClientServerAddress -AddressFamily IPv4 |
  Where-Object { $_.ServerAddresses } |
  Select-Object InterfaceAlias, ServerAddresses
```

## DNS Diagnostics

```powershell
# Resolve a domain
Resolve-DnsName google.com

# Specific DNS server
Resolve-DnsName google.com -Server 8.8.8.8

# Flush DNS cache
Clear-DnsClientCache

# View DNS cache
Get-DnsClientCache | Select-Object -First 20 Entry, RecordName, Data

# Check hosts file
Get-Content "$env:SystemRoot\System32\drivers\etc\hosts" |
  Where-Object { $_ -and $_ -notmatch '^\s*#' }

# Set DNS servers (Admin)
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses @("1.1.1.1","8.8.8.8")

# Reset to DHCP DNS
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ResetServerAddresses
```

## Wi-Fi Diagnostics

```powershell
# Current Wi-Fi connection
netsh wlan show interfaces

# Key values:
#   Signal: percentage (>70% good, <50% weak)
#   Channel: current channel
#   Receive/Transmit rate: connection speed

# Available networks
netsh wlan show networks mode=bssid

# Generate Wi-Fi report (Admin, saves HTML)
netsh wlan show wlanreport
# Report at: C:\ProgramData\Microsoft\Windows\WlanReport\wlan-report-latest.html

# Wi-Fi driver info
netsh wlan show drivers
```

**Signal strength thresholds:**
- >70% — excellent
- 50-70% — good
- 30-50% — fair (may drop)
- <30% — poor

## Port & Firewall Testing

```powershell
# Check if a remote port is reachable
Test-NetConnection -ComputerName google.com -Port 443

# List all listening ports
Get-NetTCPConnection -State Listen | Select-Object LocalPort, OwningProcess,
  @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} |
  Sort-Object LocalPort

# Check if a specific port is in use
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue

# Firewall rules for a program
Get-NetFirewallRule | Where-Object { $_.DisplayName -match 'Chrome' } |
  Select-Object DisplayName, Direction, Action, Enabled
```

## Network Performance

```powershell
# Latency test
Test-NetConnection -ComputerName google.com -TraceRoute |
  Select-Object ComputerName, RemotePort, PingSucceeded,
    @{N='LatencyMS';E={$_.PingReplyDetails.RoundtripTime}}

# Continuous ping (Ctrl+C to stop)
Test-Connection google.com -Count 30 |
  Select-Object ResponseTime, StatusCode

# Packet loss check
$results = Test-Connection google.com -Count 30
$lost = ($results | Where-Object { $_.StatusCode -ne 0 }).Count
"Packet loss: {0}%" -f [math]::Round($lost/30*100,1)
```

## VPN Status

```powershell
# Built-in VPN connections
Get-VpnConnection | Select-Object Name, ServerAddress, ConnectionStatus

# Active VPN interfaces
Get-NetAdapter | Where-Object { $_.InterfaceDescription -match 'VPN|TAP|TUN|WireGuard' } |
  Select-Object Name, Status, InterfaceDescription
```

## Network Reset (Nuclear Option)

```powershell
# Full network reset (Admin, requires restart)
netsh int ip reset
netsh winsock reset
ipconfig /flushdns
ipconfig /release
ipconfig /renew

# Or via Settings:
# Settings > Network & Internet > Advanced network settings > Network reset
```

Removes all network adapters and reinstalls them. All Wi-Fi passwords,
VPN configs, and custom settings are lost.

## Common Network Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No internet, connected | DNS issue | Flush DNS, try 8.8.8.8 |
| Slow browsing | DNS or congestion | Switch DNS servers |
| Can't connect to Wi-Fi | Driver or password | Forget + re-join |
| VPN breaks internet | Routing table | Check VPN split tunnel |
| Port not reachable | Firewall | Check `Get-NetFirewallRule` |
| Intermittent drops | Weak signal | Check signal %, move closer |
| "No internet" icon | NCSI probe failing | `netsh int ip reset` |
