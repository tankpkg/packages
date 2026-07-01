#!/usr/bin/env bash
# read-config.sh — Read current macOS configuration across major preference domains.
# Part of @tank/macos-configurator skill.
#
# Usage:
#   bash read-config.sh              # Human-readable report
#   bash read-config.sh --json       # JSON output
#   bash read-config.sh --domain dock  # Single domain
#   bash read-config.sh --diff saved.json  # Compare to saved config
#
# Domains: keyboard, trackpad, dock, finder, screenshots, network,
#          power, display, sound, security, apps

set -euo pipefail

# --- Argument parsing ---
OUTPUT_FORMAT="text"
SINGLE_DOMAIN=""
DIFF_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) OUTPUT_FORMAT="json"; shift ;;
        --domain) SINGLE_DOMAIN="$2"; shift 2 ;;
        --diff) DIFF_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: read-config.sh [--json] [--domain <name>] [--diff <file>]"
            echo ""
            echo "Domains: keyboard, trackpad, dock, finder, screenshots,"
            echo "         network, power, display, sound, security, apps"
            echo ""
            echo "Flags:"
            echo "  --json          Output as JSON"
            echo "  --domain NAME   Read only one domain"
            echo "  --diff FILE     Compare current config to saved JSON file"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Helpers ---
read_default() {
    local domain="$1" key="$2"
    defaults read "$domain" "$key" 2>/dev/null || echo "(not set)"
}

read_global() {
    local key="$1"
    defaults read NSGlobalDomain "$key" 2>/dev/null || echo "(not set)"
}

read_current_host() {
    local key="$1"
    defaults -currentHost read NSGlobalDomain "$key" 2>/dev/null || echo "(not set)"
}

section_header() {
    if [[ "$OUTPUT_FORMAT" == "text" ]]; then
        echo ""
        echo "═══════════════════════════════════════════════════"
        echo "  $1"
        echo "═══════════════════════════════════════════════════"
    fi
}

print_setting() {
    local label="$1" value="$2"
    if [[ "$OUTPUT_FORMAT" == "text" ]]; then
        printf "  %-40s %s\n" "$label:" "$value"
    fi
}

# --- JSON accumulator ---
declare -a JSON_ENTRIES=()
json_add() {
    local domain="$1" key="$2" value="$3"
    # Escape quotes in value
    value="${value//\"/\\\"}"
    JSON_ENTRIES+=("\"${domain}.${key}\": \"${value}\"")
}

# --- Domain readers ---
read_keyboard() {
    section_header "KEYBOARD"
    local v
    v=$(read_global "ApplePressAndHoldEnabled"); print_setting "Press and hold (accent picker)" "$v"; json_add "keyboard" "press_and_hold" "$v"
    v=$(read_global "KeyRepeat"); print_setting "Key repeat rate (lower=faster)" "$v"; json_add "keyboard" "key_repeat" "$v"
    v=$(read_global "InitialKeyRepeat"); print_setting "Key repeat delay (lower=shorter)" "$v"; json_add "keyboard" "initial_key_repeat" "$v"
    v=$(read_global "NSAutomaticSpellingCorrectionEnabled"); print_setting "Auto-correct" "$v"; json_add "keyboard" "auto_correct" "$v"
    v=$(read_global "NSAutomaticQuoteSubstitutionEnabled"); print_setting "Smart quotes" "$v"; json_add "keyboard" "smart_quotes" "$v"
    v=$(read_global "NSAutomaticDashSubstitutionEnabled"); print_setting "Smart dashes" "$v"; json_add "keyboard" "smart_dashes" "$v"
    v=$(read_global "NSAutomaticCapitalizationEnabled"); print_setting "Auto-capitalize" "$v"; json_add "keyboard" "auto_capitalize" "$v"
    v=$(read_global "NSAutomaticPeriodSubstitutionEnabled"); print_setting "Period with double space" "$v"; json_add "keyboard" "period_substitution" "$v"
    v=$(read_global "AppleKeyboardUIMode"); print_setting "Full keyboard access" "$v"; json_add "keyboard" "keyboard_ui_mode" "$v"
    v=$(read_global "com.apple.keyboard.fnState"); print_setting "Fn keys as standard function keys" "$v"; json_add "keyboard" "fn_state" "$v"
}

read_trackpad() {
    section_header "TRACKPAD"
    local v
    v=$(read_default "com.apple.AppleMultitouchTrackpad" "Clicking"); print_setting "Tap to click" "$v"; json_add "trackpad" "tap_to_click" "$v"
    v=$(read_default "com.apple.AppleMultitouchTrackpad" "TrackpadRightClick"); print_setting "Two-finger right-click" "$v"; json_add "trackpad" "right_click" "$v"
    v=$(read_default "com.apple.AppleMultitouchTrackpad" "TrackpadThreeFingerDrag"); print_setting "Three-finger drag" "$v"; json_add "trackpad" "three_finger_drag" "$v"
    v=$(read_global "com.apple.swipescrolldirection"); print_setting "Natural scrolling" "$v"; json_add "trackpad" "natural_scrolling" "$v"
    v=$(read_default "com.apple.AppleMultitouchTrackpad" "FirstClickThreshold"); print_setting "Click pressure (0=light)" "$v"; json_add "trackpad" "click_pressure" "$v"
    v=$(defaults read com.apple.trackpad.scaling 2>/dev/null || echo "(not set)"); print_setting "Tracking speed" "$v"; json_add "trackpad" "tracking_speed" "$v"
}

read_dock() {
    section_header "DOCK"
    local v
    v=$(read_default "com.apple.dock" "tilesize"); print_setting "Icon size (px)" "$v"; json_add "dock" "tile_size" "$v"
    v=$(read_default "com.apple.dock" "autohide"); print_setting "Auto-hide" "$v"; json_add "dock" "autohide" "$v"
    v=$(read_default "com.apple.dock" "autohide-delay"); print_setting "Auto-hide delay" "$v"; json_add "dock" "autohide_delay" "$v"
    v=$(read_default "com.apple.dock" "autohide-time-modifier"); print_setting "Auto-hide animation speed" "$v"; json_add "dock" "autohide_animation" "$v"
    v=$(read_default "com.apple.dock" "orientation"); print_setting "Position" "$v"; json_add "dock" "orientation" "$v"
    v=$(read_default "com.apple.dock" "mineffect"); print_setting "Minimize effect" "$v"; json_add "dock" "minimize_effect" "$v"
    v=$(read_default "com.apple.dock" "show-recents"); print_setting "Show recent apps" "$v"; json_add "dock" "show_recents" "$v"
    v=$(read_default "com.apple.dock" "launchanim"); print_setting "Launch animation" "$v"; json_add "dock" "launch_animation" "$v"
    v=$(read_default "com.apple.dock" "mru-spaces"); print_setting "Auto-rearrange Spaces" "$v"; json_add "dock" "mru_spaces" "$v"

    # Hot corners
    for corner in tl tr bl br; do
        v=$(read_default "com.apple.dock" "wvous-${corner}-corner")
        print_setting "Hot corner ${corner}" "$v"
        json_add "dock" "hot_corner_${corner}" "$v"
    done
}

read_finder() {
    section_header "FINDER"
    local v
    v=$(read_global "AppleShowAllExtensions"); print_setting "Show all extensions" "$v"; json_add "finder" "show_extensions" "$v"
    v=$(read_default "com.apple.finder" "AppleShowAllFiles"); print_setting "Show hidden files" "$v"; json_add "finder" "show_hidden" "$v"
    v=$(read_default "com.apple.finder" "ShowPathbar"); print_setting "Show path bar" "$v"; json_add "finder" "path_bar" "$v"
    v=$(read_default "com.apple.finder" "ShowStatusBar"); print_setting "Show status bar" "$v"; json_add "finder" "status_bar" "$v"
    v=$(read_default "com.apple.finder" "FXPreferredViewStyle"); print_setting "Default view style" "$v"; json_add "finder" "view_style" "$v"
    v=$(read_default "com.apple.finder" "FXDefaultSearchScope"); print_setting "Search scope" "$v"; json_add "finder" "search_scope" "$v"
    v=$(read_default "com.apple.finder" "_FXSortFoldersFirst"); print_setting "Folders on top" "$v"; json_add "finder" "folders_first" "$v"
    v=$(read_default "com.apple.finder" "FXEnableExtensionChangeWarning"); print_setting "Extension change warning" "$v"; json_add "finder" "extension_warning" "$v"
    v=$(read_default "com.apple.desktopservices" "DSDontWriteNetworkStores"); print_setting "No .DS_Store on network" "$v"; json_add "finder" "no_ds_store_network" "$v"
    v=$(read_global "NSDocumentSaveNewDocumentsToCloud"); print_setting "Save to iCloud by default" "$v"; json_add "finder" "save_to_icloud" "$v"
}

read_screenshots() {
    section_header "SCREENSHOTS"
    local v
    v=$(read_default "com.apple.screencapture" "type"); print_setting "Format" "$v"; json_add "screenshots" "format" "$v"
    v=$(read_default "com.apple.screencapture" "location"); print_setting "Location" "$v"; json_add "screenshots" "location" "$v"
    v=$(read_default "com.apple.screencapture" "disable-shadow"); print_setting "Shadow disabled" "$v"; json_add "screenshots" "shadow_disabled" "$v"
    v=$(read_default "com.apple.screencapture" "show-thumbnail"); print_setting "Show thumbnail" "$v"; json_add "screenshots" "show_thumbnail" "$v"
    v=$(read_default "com.apple.screencapture" "include-date"); print_setting "Include date" "$v"; json_add "screenshots" "include_date" "$v"
}

read_network() {
    section_header "NETWORK"
    # Computer names
    local v
    v=$(scutil --get ComputerName 2>/dev/null || echo "(not set)"); print_setting "Computer Name" "$v"; json_add "network" "computer_name" "$v"
    v=$(scutil --get HostName 2>/dev/null || echo "(not set)"); print_setting "Host Name" "$v"; json_add "network" "host_name" "$v"
    v=$(scutil --get LocalHostName 2>/dev/null || echo "(not set)"); print_setting "Local Host Name (Bonjour)" "$v"; json_add "network" "local_host_name" "$v"

    # DNS for primary service
    local primary_service
    primary_service=$(networksetup -listallnetworkservices 2>/dev/null | grep -v "^An asterisk" | head -2 | tail -1 || echo "Wi-Fi")
    v=$(networksetup -getdnsservers "$primary_service" 2>/dev/null | tr '\n' ', ' | sed 's/,$//' || echo "(not set)")
    print_setting "DNS ($primary_service)" "$v"; json_add "network" "dns" "$v"

    # Firewall
    v=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | awk '{print $NF}' || echo "(unknown)")
    print_setting "Firewall" "$v"; json_add "network" "firewall" "$v"
}

read_power() {
    section_header "POWER MANAGEMENT"
    local v
    v=$(pmset -g 2>/dev/null | grep " sleep " | awk '{print $2}' || echo "(unknown)"); print_setting "Computer sleep (min)" "$v"; json_add "power" "computer_sleep" "$v"
    v=$(pmset -g 2>/dev/null | grep "displaysleep" | awk '{print $2}' || echo "(unknown)"); print_setting "Display sleep (min)" "$v"; json_add "power" "display_sleep" "$v"
    v=$(pmset -g 2>/dev/null | grep "disksleep" | awk '{print $2}' || echo "(unknown)"); print_setting "Disk sleep (min)" "$v"; json_add "power" "disk_sleep" "$v"
    v=$(pmset -g 2>/dev/null | grep "hibernatemode" | awk '{print $2}' || echo "(unknown)"); print_setting "Hibernate mode" "$v"; json_add "power" "hibernate_mode" "$v"
    v=$(pmset -g 2>/dev/null | grep "womp " | awk '{print $2}' || echo "(unknown)"); print_setting "Wake on network" "$v"; json_add "power" "wake_on_network" "$v"
    v=$(pmset -g 2>/dev/null | grep "lidwake" | awk '{print $2}' || echo "(unknown)"); print_setting "Lid wake" "$v"; json_add "power" "lid_wake" "$v"
}

read_display() {
    section_header "DISPLAY & APPEARANCE"
    local v
    v=$(read_global "AppleInterfaceStyle"); print_setting "Interface style" "$v"; json_add "display" "interface_style" "$v"
    v=$(read_global "AppleAccentColor"); print_setting "Accent color" "$v"; json_add "display" "accent_color" "$v"
    v=$(read_global "AppleFontSmoothing"); print_setting "Font smoothing" "$v"; json_add "display" "font_smoothing" "$v"
    v=$(read_global "AppleShowScrollBars"); print_setting "Show scroll bars" "$v"; json_add "display" "scroll_bars" "$v"
    v=$(read_default "com.apple.universalaccess" "reduceTransparency"); print_setting "Reduce transparency" "$v"; json_add "display" "reduce_transparency" "$v"
    v=$(read_default "com.apple.universalaccess" "reduceMotion"); print_setting "Reduce motion" "$v"; json_add "display" "reduce_motion" "$v"
}

read_sound() {
    section_header "SOUND"
    local v
    v=$(read_global "com.apple.sound.beep.feedback"); print_setting "Volume change feedback" "$v"; json_add "sound" "beep_feedback" "$v"
    v=$(read_global "com.apple.sound.uiaudio.enabled"); print_setting "UI sounds" "$v"; json_add "sound" "ui_sounds" "$v"
    v=$(nvram StartupMute 2>/dev/null | awk '{print $2}' || echo "(unknown)"); print_setting "Startup chime muted" "$v"; json_add "sound" "startup_mute" "$v"
}

read_security() {
    section_header "SECURITY"
    local v
    v=$(read_default "com.apple.screensaver" "askForPassword"); print_setting "Password after sleep" "$v"; json_add "security" "ask_password" "$v"
    v=$(read_default "com.apple.screensaver" "askForPasswordDelay"); print_setting "Password delay (sec)" "$v"; json_add "security" "password_delay" "$v"
    v=$(read_default "com.apple.LaunchServices" "LSQuarantine"); print_setting "Quarantine dialog" "$v"; json_add "security" "quarantine" "$v"
    v=$(fdesetup status 2>/dev/null || echo "(unknown)"); print_setting "FileVault" "$v"; json_add "security" "filevault" "$v"
    v=$(spctl --status 2>/dev/null || echo "(unknown)"); print_setting "Gatekeeper" "$v"; json_add "security" "gatekeeper" "$v"
}

read_apps() {
    section_header "APP SETTINGS"
    local v
    v=$(read_default "com.apple.Safari" "IncludeDevelopMenu"); print_setting "Safari Develop menu" "$v"; json_add "apps" "safari_develop" "$v"
    v=$(read_default "com.apple.Safari" "ShowFullURLInSmartSearchField"); print_setting "Safari full URL" "$v"; json_add "apps" "safari_full_url" "$v"
    v=$(read_default "com.apple.terminal" "SecureKeyboardEntry"); print_setting "Terminal secure keyboard" "$v"; json_add "apps" "terminal_secure" "$v"
    v=$(read_default "com.apple.TextEdit" "RichText"); print_setting "TextEdit rich text" "$v"; json_add "apps" "textedit_rich" "$v"
    v=$(read_default "com.apple.ActivityMonitor" "IconType"); print_setting "Activity Monitor icon type" "$v"; json_add "apps" "actmon_icon" "$v"
    v=$(read_default "com.apple.TimeMachine" "DoNotOfferNewDisksForBackup"); print_setting "TM new disk prompts" "$v"; json_add "apps" "tm_new_disk" "$v"
}

# --- Main ---
DOMAINS_TO_READ=("keyboard" "trackpad" "dock" "finder" "screenshots" "network" "power" "display" "sound" "security" "apps")

if [[ -n "$SINGLE_DOMAIN" ]]; then
    DOMAINS_TO_READ=("$SINGLE_DOMAIN")
fi

if [[ "$OUTPUT_FORMAT" == "text" ]]; then
    echo "macOS Configuration Report"
    echo "Generated: $(date)"
    echo "macOS: $(sw_vers -productVersion) ($(sw_vers -buildVersion))"
    echo "Hardware: $(sysctl -n hw.model 2>/dev/null || echo unknown)"
fi

for domain in "${DOMAINS_TO_READ[@]}"; do
    case "$domain" in
        keyboard) read_keyboard ;;
        trackpad) read_trackpad ;;
        dock) read_dock ;;
        finder) read_finder ;;
        screenshots) read_screenshots ;;
        network) read_network ;;
        power) read_power ;;
        display) read_display ;;
        sound) read_sound ;;
        security) read_security ;;
        apps) read_apps ;;
        *) echo "Unknown domain: $domain. Valid: keyboard, trackpad, dock, finder, screenshots, network, power, display, sound, security, apps"; exit 1 ;;
    esac
done

# --- JSON output ---
if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    echo "{"
    echo "  \"_generated\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"_macos_version\": \"$(sw_vers -productVersion)\","
    echo "  \"_hardware\": \"$(sysctl -n hw.model 2>/dev/null || echo unknown)\","
    local count=${#JSON_ENTRIES[@]}
    for i in "${!JSON_ENTRIES[@]}"; do
        if [[ $i -lt $((count - 1)) ]]; then
            echo "  ${JSON_ENTRIES[$i]},"
        else
            echo "  ${JSON_ENTRIES[$i]}"
        fi
    done
    echo "}"
fi

# --- Diff mode ---
if [[ -n "$DIFF_FILE" ]]; then
    if [[ ! -f "$DIFF_FILE" ]]; then
        echo "Error: diff file not found: $DIFF_FILE" >&2
        exit 1
    fi
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "  DIFFERENCES from $DIFF_FILE"
    echo "═══════════════════════════════════════════════════"

    # Generate current JSON to temp, diff with saved
    CURRENT_JSON=$(mktemp)
    OUTPUT_FORMAT="json" SINGLE_DOMAIN="" bash "$0" --json > "$CURRENT_JSON" 2>/dev/null
    diff --unified=0 "$DIFF_FILE" "$CURRENT_JSON" | grep "^[+-]" | grep -v "^[+-][+-][+-]" | grep -v "_generated" || echo "  No differences found."
    rm -f "$CURRENT_JSON"
fi

if [[ "$OUTPUT_FORMAT" == "text" ]]; then
    echo ""
    echo "Done. Use --json for machine-readable output."
fi
