# Maintenance Tasks

Periodic maintenance operations that keep macOS running smoothly. Includes
tasks macOS handles automatically and tasks that need manual intervention.

## macOS Built-in Periodic Scripts

macOS runs three maintenance scripts automatically:
- **daily** — rotates system logs, removes old temp files
- **weekly** — rebuilds `locate` and `whatis` databases
- **monthly** — rotates additional logs, cleans up old accounting data

```bash
# Check when they last ran
ls -la /var/log/*.out 2>/dev/null
# daily.out, weekly.out, monthly.out
# Compare dates — if laptop sleeps through scheduled times, they get skipped

# Force-run all periodic scripts (safe, takes 1-2 minutes)
sudo periodic daily weekly monthly

# Run individually
sudo periodic daily
sudo periodic weekly
sudo periodic monthly
```

**When to force-run:**
- If the Mac was sleeping/off at scheduled run times
- After extended travel (laptop closed for days)
- If `daily.out` is more than 3 days old
- Monthly scripts haven't run in 30+ days

These scripts are safe and idempotent — running them extra times causes no harm.

## DNS Cache Flush

```bash
# Flush DNS cache (useful when DNS is stale or domains don't resolve)
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

# Verify
dscacheutil -q host -a name google.com
```

**When to flush:**
- After changing DNS servers
- After VPN connect/disconnect issues
- When websites fail to load but internet works
- After editing `/etc/hosts`

## Rebuild Launch Services Database

The Launch Services database maps file types to applications. Corruption
causes "Open With" to show duplicates or wrong apps.

```bash
# Rebuild Launch Services database
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user

# Then restart Finder
killall Finder
```

**When to rebuild:**
- Duplicate entries in "Open With" context menu
- Wrong app opens for a file type
- App icons showing as generic white document

## Rebuild Spotlight Index

```bash
# Disable then re-enable to force full re-index
sudo mdutil -E /

# Check progress
mdutil -s /

# Alternatively, add then remove from Privacy list
# System Settings → Spotlight → Privacy → add "/" → remove "/"
```

**When to rebuild:**
- Search returns no/wrong results
- `mds_stores` process using high CPU for extended periods
- After OS upgrade or migration

Rebuilding takes 10-60 minutes depending on disk size. Mac may feel
sluggish during indexing.

## Reset NVRAM/PRAM

**Intel Macs:**
Restart and hold Cmd+Option+P+R for 20 seconds.

**Apple Silicon:**
NVRAM resets automatically during a normal restart. No manual reset needed.

NVRAM stores: display resolution, startup disk, time zone, volume, kernel
panic info. Reset when display/sound/startup issues occur.

## Reset SMC

**Intel Macs:**
1. Shut down
2. Hold Control+Shift+Option+Power for 10 seconds
3. Release and power on

**Apple Silicon:**
No SMC — shut down for 30 seconds and restart.

SMC controls: fans, thermal management, battery charging, LED indicators,
power button behavior. Reset when fans run high, battery doesn't charge,
or sleep/wake fails.

## Launch Daemon/Agent Audit

```bash
# All non-Apple launch agents (user)
ls ~/Library/LaunchAgents/ 2>/dev/null | grep -v "com.apple"

# All non-Apple launch agents (system)
ls /Library/LaunchAgents/ 2>/dev/null | grep -v "com.apple"

# All non-Apple launch daemons
ls /Library/LaunchDaemons/ 2>/dev/null | grep -v "com.apple"

# Check if a specific agent/daemon is loaded
launchctl list | grep "com.example"

# Get details about a launchd job
launchctl print system/com.example.daemon

# Disable a launch agent (persists across restarts)
launchctl disable user/$(id -u)/com.example.agent

# Unload immediately
launchctl bootout gui/$(id -u)/com.example.agent
```

**Common safe-to-remove items** (if you don't use the app):
- `com.adobe.AdobeCreativeCloud` — Creative Cloud auto-launcher
- `com.spotify.webhelper` — Spotify web player helper
- `com.google.keystone.*` — Google updater
- `com.microsoft.update.*` — Microsoft AutoUpdate

**Never remove:**
- Anything starting with `com.apple.`
- Items you're not sure about — research first

## Kernel Extension Audit (Intel/Transition)

```bash
# List loaded kexts
kextstat | grep -v com.apple

# System Extensions (modern replacement for kexts)
systemextensionsctl list
```

On Apple Silicon, third-party kernel extensions are largely deprecated.
System Extensions are the modern replacement and run in user space.

**Common legitimate non-Apple kexts:**
- VirtualBox, VMware, Parallels — virtualization
- Little Snitch — network firewall
- Wireshark — packet capture

## App Update Checks

```bash
# macOS software updates
softwareupdate -l

# Homebrew outdated packages
brew outdated

# Homebrew cask (GUI app) updates
brew outdated --cask

# npm global packages
npm outdated -g 2>/dev/null

# pip packages
pip list --outdated 2>/dev/null
```

## Recommended Maintenance Schedule

### Weekly
- Check for macOS updates (`softwareupdate -l`)
- Run `brew update && brew upgrade && brew cleanup`
- Empty Trash if large

### Monthly
- Force periodic scripts (`sudo periodic daily weekly monthly`)
- Check disk space (`df -h /`)
- Review login items
- Check battery health (laptops)
- Run `brew autoremove`

### Quarterly
- Full security audit (run the security scorecard)
- Check SMART disk status
- Review launch agents/daemons for cruft
- Check Time Machine backup health
- Review large files and disk usage
- Update dev tool caches (consider cleanup)

### Annually
- Full system backup before OS upgrade
- Review system extensions
- Audit installed applications (remove unused)
- Check FileVault recovery key is accessible

## Troubleshooting Common Issues

### Mac Running Slow

1. Check memory pressure: `memory_pressure`
2. Check CPU: `top -l 1 -o cpu -n 5`
3. Check disk space: `df -h /` (needs >10% free)
4. Check swap: `sysctl vm.swapusage`
5. Check uptime: `uptime` (restart if >30 days)
6. Check for runaway processes: `ps aux | awk '$3 > 50'`
7. Check Spotlight indexing: `mdutil -s /`
8. Consider restart (fixes most transient issues)

### Fan Running Loud

1. Check CPU usage: `top -l 1 -o cpu -n 5`
2. Kill runaway process if found
3. Check thermal state: `sudo powermetrics --samplers smc -i 1 -n 1`
4. Reset SMC (Intel) or restart (Apple Silicon)
5. Clean vents with compressed air
6. Check ambient temperature

### Wi-Fi Issues

See `references/network-diagnostics.md` for detailed Wi-Fi troubleshooting.

Quick fixes:
1. Turn Wi-Fi off and on
2. Forget and re-join network
3. Flush DNS: `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`
4. Renew DHCP: `sudo ipconfig set en0 DHCP`
5. Reset network preferences: delete `/Library/Preferences/SystemConfiguration/` files (sudo, then restart)

### Battery Draining Fast

1. Check Activity Monitor → Energy tab
2. `pmset -g assertions` — what's preventing sleep?
3. Check for runaway processes: `top -l 1 -o cpu -n 5`
4. Disable Bluetooth if not in use
5. Reduce display brightness
6. Check battery health: `system_profiler SPPowerDataType | grep Condition`
