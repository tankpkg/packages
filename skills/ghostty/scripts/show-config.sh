#!/usr/bin/env bash
set -euo pipefail

GHOSTTY="${GHOSTTY_BIN:-ghostty}"

usage() {
    cat <<EOF
Usage: $(basename "$0") <command> [options]

Commands:
  config          Show effective merged config (all sources combined)
  defaults        Show all options with documentation and default values
  fonts           List fonts Ghostty can render
  themes          List all available themes (built-in + custom)
  keybinds        Show current keybind mappings
  keybinds-default  Show default keybind mappings before user overrides
  diff <file>     Compare current config against a saved config file
  search <term>   Search config options by keyword
  version         Show Ghostty version and platform info
  help            Show this message

Examples:
  bash show-config.sh config
  bash show-config.sh themes | grep -i "catppuccin"
  bash show-config.sh defaults | grep -A5 "font-size"
  bash show-config.sh search opacity
  bash show-config.sh diff ~/dotfiles/ghostty-config
EOF
}

check_ghostty() {
    if ! command -v "$GHOSTTY" &>/dev/null; then
        echo "Error: ghostty not found. Set GHOSTTY_BIN env var if installed elsewhere." >&2
        exit 1
    fi
}

cmd_config() {
    echo "# Effective Ghostty config (merged from all config-file sources)"
    echo "# Generated: $(date)"
    echo ""
    "$GHOSTTY" +show-config
}

cmd_defaults() {
    echo "# All Ghostty config options with documentation"
    echo "# Use: ghostty +show-config --default --docs"
    echo ""
    "$GHOSTTY" +show-config --default --docs
}

cmd_fonts() {
    echo "# Fonts available to Ghostty"
    "$GHOSTTY" +list-fonts
}

cmd_themes() {
    echo "# Available themes (built-in + ~/.config/ghostty/themes/)"
    "$GHOSTTY" +list-themes
}

cmd_keybinds() {
    echo "# Current keybind mappings (after user overrides)"
    "$GHOSTTY" +list-keybinds
}

cmd_keybinds_default() {
    echo "# Default keybind mappings (before user config)"
    "$GHOSTTY" +list-keybinds --default
}

cmd_diff() {
    local saved_config="${1:-}"
    if [[ -z "$saved_config" ]]; then
        echo "Usage: $(basename "$0") diff <saved-config-file>" >&2
        exit 1
    fi
    if [[ ! -f "$saved_config" ]]; then
        echo "Error: file not found: $saved_config" >&2
        exit 1
    fi

    echo "# Diff: saved config vs current effective config"
    echo "# Left (<): $saved_config"
    echo "# Right (>): ghostty +show-config"
    echo ""
    diff "$saved_config" <("$GHOSTTY" +show-config) || true
}

cmd_search() {
    local term="${1:-}"
    if [[ -z "$term" ]]; then
        echo "Usage: $(basename "$0") search <term>" >&2
        exit 1
    fi

    echo "# Searching config options for: $term"
    echo ""
    "$GHOSTTY" +show-config --default --docs | grep -i -A3 "$term" || echo "No matches found."
}

cmd_version() {
    "$GHOSTTY" +version
}

main() {
    local cmd="${1:-help}"
    shift || true

    check_ghostty

    case "$cmd" in
        config)           cmd_config ;;
        defaults)         cmd_defaults ;;
        fonts)            cmd_fonts ;;
        themes)           cmd_themes ;;
        keybinds)         cmd_keybinds ;;
        keybinds-default) cmd_keybinds_default ;;
        diff)             cmd_diff "$@" ;;
        search)           cmd_search "$@" ;;
        version)          cmd_version ;;
        help|-h|--help)   usage ;;
        *)
            echo "Unknown command: $cmd" >&2
            usage >&2
            exit 1
            ;;
    esac
}

main "$@"
