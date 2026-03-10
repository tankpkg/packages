#!/usr/bin/env bash
# check-tools.sh — Detect installed compression tools and suggest missing ones.
# Usage: bash scripts/check-tools.sh [--json] [--install]

set -euo pipefail

JSON_MODE=false
INSTALL_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --install) INSTALL_MODE=true ;;
  esac
done

detect_os() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "macos"
  elif [[ -f /etc/debian_version ]]; then
    echo "debian"
  elif [[ -f /etc/redhat-release ]]; then
    echo "redhat"
  else
    echo "unknown"
  fi
}

OS=$(detect_os)

# Tool definitions: name|check_command|brew_package|apt_package|category
TOOLS=(
  "ffmpeg|ffmpeg -version|ffmpeg|ffmpeg|required"
  "ghostscript|gs --version|ghostscript|ghostscript|required"
  "cwebp|cwebp -version|webp|webp|recommended"
  "avifenc|avifenc --version|libavif|libavif-bin|recommended"
  "pngquant|pngquant --version|pngquant|pngquant|recommended"
  "oxipng|oxipng --version|oxipng|cargo:oxipng|recommended"
  "jpegoptim|jpegoptim --version|jpegoptim|jpegoptim|recommended"
  "zstd|zstd --version|zstd|zstd|recommended"
  "gifsicle|gifsicle --version|gifsicle|gifsicle|optional"
  "optipng|optipng --version|optipng|optipng|optional"
  "pigz|pigz --version|pigz|pigz|optional"
  "pbzip2|pbzip2 --version|pbzip2|pbzip2|optional"
  "brotli|brotli --version|brotli|brotli|optional"
  "7z|7z i|p7zip|p7zip-full|optional"
  "qpdf|qpdf --version|qpdf|qpdf|optional"
)

installed=0
missing=0
missing_required=0
missing_tools=()
json_entries=()

for entry in "${TOOLS[@]}"; do
  IFS='|' read -r name check_cmd brew_pkg apt_pkg category <<< "$entry"

  if command -v "$name" &>/dev/null; then
    version=$($check_cmd 2>&1 | head -1 | sed 's/^[^0-9]*//' | cut -d' ' -f1 | head -c 40)
    ((installed++))
    if $JSON_MODE; then
      json_entries+=("{\"name\":\"$name\",\"installed\":true,\"version\":\"$version\",\"category\":\"$category\"}")
    else
      printf "  %-12s %-12s %s\n" "$name" "$category" "$version"
    fi
  else
    ((missing++))
    if [[ "$category" == "required" ]]; then
      ((missing_required++))
    fi
    missing_tools+=("$name|$brew_pkg|$apt_pkg|$category")
    if $JSON_MODE; then
      json_entries+=("{\"name\":\"$name\",\"installed\":false,\"category\":\"$category\"}")
    else
      printf "  %-12s %-12s %s\n" "$name" "$category" "(not installed)"
    fi
  fi
done

if $JSON_MODE; then
  echo "{"
  echo "  \"os\": \"$OS\","
  echo "  \"installed\": $installed,"
  echo "  \"missing\": $missing,"
  echo "  \"missing_required\": $missing_required,"
  printf '  "tools": [%s]\n' "$(IFS=,; echo "${json_entries[*]}")"
  echo "}"
  exit 0
fi

echo ""
echo "Summary: $installed installed, $missing missing ($missing_required required)"

if [[ ${#missing_tools[@]} -gt 0 ]]; then
  echo ""
  echo "Install missing tools:"

  if [[ "$OS" == "macos" ]]; then
    brew_pkgs=()
    for entry in "${missing_tools[@]}"; do
      IFS='|' read -r name brew_pkg apt_pkg category <<< "$entry"
      [[ -n "$brew_pkg" ]] && brew_pkgs+=("$brew_pkg")
    done
    if [[ ${#brew_pkgs[@]} -gt 0 ]]; then
      echo "  brew install ${brew_pkgs[*]}"
    fi
  elif [[ "$OS" == "debian" ]]; then
    apt_pkgs=()
    cargo_pkgs=()
    for entry in "${missing_tools[@]}"; do
      IFS='|' read -r name brew_pkg apt_pkg category <<< "$entry"
      if [[ "$apt_pkg" == cargo:* ]]; then
        cargo_pkgs+=("${apt_pkg#cargo:}")
      elif [[ -n "$apt_pkg" ]]; then
        apt_pkgs+=("$apt_pkg")
      fi
    done
    if [[ ${#apt_pkgs[@]} -gt 0 ]]; then
      echo "  sudo apt install ${apt_pkgs[*]}"
    fi
    if [[ ${#cargo_pkgs[@]} -gt 0 ]]; then
      echo "  cargo install ${cargo_pkgs[*]}"
    fi
  fi

  if $INSTALL_MODE; then
    echo ""
    echo "Installing..."
    if [[ "$OS" == "macos" ]] && [[ ${#brew_pkgs[@]} -gt 0 ]]; then
      brew install "${brew_pkgs[@]}"
    elif [[ "$OS" == "debian" ]] && [[ ${#apt_pkgs[@]} -gt 0 ]]; then
      sudo apt install -y "${apt_pkgs[@]}"
    fi
  fi
fi

if [[ $missing_required -gt 0 ]]; then
  exit 1
fi
exit 0
