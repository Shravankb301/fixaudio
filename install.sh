#!/bin/bash
# fixaudio installer.
#
#   curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/install.sh | bash
#
# or, from a clone:  ./install.sh

set -euo pipefail

REPO="${FIXAUDIO_REPO:-shravankb301/willitddc}"
BRANCH="${FIXAUDIO_BRANCH:-main}"
BIN_DIR="${FIXAUDIO_BIN_DIR:-$HOME/.local/bin}"
HS_DIR="$HOME/.hammerspoon"

bold=$(tput bold 2>/dev/null || true)
dim=$(tput dim 2>/dev/null || true)
red=$(tput setaf 1 2>/dev/null || true)
green=$(tput setaf 2 2>/dev/null || true)
yellow=$(tput setaf 3 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

say()  { echo "${bold}==>${reset} $*"; }
ok()   { echo "  ${green}✓${reset} $*"; }
warn() { echo "  ${yellow}!${reset} $*"; }
die()  { echo "${red}error:${reset} $*" >&2; exit 1; }

# --- preflight ---------------------------------------------------------------

[[ "$(uname -s)" == "Darwin" ]] || die "fixaudio is macOS only."

if [[ "$(uname -m)" != "arm64" ]]; then
  warn "This Mac is Intel. fixaudio uses m1ddc, which is Apple Silicon only."
  warn "Intel Macs need a different DDC backend (e.g. ddcctl) - not supported yet."
  die "unsupported architecture: $(uname -m)"
fi

command -v brew >/dev/null 2>&1 || die \
  "Homebrew is required. Install it from https://brew.sh and re-run."

# --- source ------------------------------------------------------------------

SRC=""
self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"
if [[ -n "$self_dir" && -f "$self_dir/bin/ddcvol" ]]; then
  SRC="$self_dir"
  say "Installing from $SRC"
else
  say "Downloading fixaudio ($REPO@$BRANCH)"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$BRANCH" \
    | tar -xz -C "$TMP" --strip-components=1 \
    || die "download failed. Check that $REPO exists and is public."
  SRC="$TMP"
  ok "downloaded"
fi

# --- dependencies ------------------------------------------------------------

say "Installing dependencies"
for formula in m1ddc switchaudio-osx; do
  if brew list --formula "$formula" >/dev/null 2>&1; then
    ok "$formula already installed"
  else
    brew install "$formula" >/dev/null && ok "installed $formula"
  fi
done

if [[ -d /Applications/Hammerspoon.app ]]; then
  ok "Hammerspoon already installed"
else
  brew install --cask hammerspoon >/dev/null && ok "installed Hammerspoon"
fi

# --- CLI ---------------------------------------------------------------------

say "Installing CLI to $BIN_DIR"
mkdir -p "$BIN_DIR"
for tool in ddcvol audioout; do
  install -m 0755 "$SRC/bin/$tool" "$BIN_DIR/$tool"
  ok "$tool"
done

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    warn "$BIN_DIR is not on your PATH. Add this to your shell profile:"
    echo "      export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac

# --- Hammerspoon config ------------------------------------------------------

say "Installing Hammerspoon module"
mkdir -p "$HS_DIR/fixaudio"
cp "$SRC/hammerspoon/fixaudio/"*.lua "$HS_DIR/fixaudio/"
ok "$HS_DIR/fixaudio/"

# Never clobber an existing config: append one line if it isn't already there.
LOADER='require("fixaudio").start()'
if [[ -f "$HS_DIR/init.lua" ]]; then
  if grep -q 'require("fixaudio")' "$HS_DIR/init.lua"; then
    ok "init.lua already loads fixaudio"
  else
    cp "$HS_DIR/init.lua" "$HS_DIR/init.lua.pre-fixaudio"
    printf '\n-- fixaudio\n%s\n' "$LOADER" >> "$HS_DIR/init.lua"
    ok "appended loader to init.lua (backup: init.lua.pre-fixaudio)"
  fi
else
  printf -- '-- fixaudio\n%s\n' "$LOADER" > "$HS_DIR/init.lua"
  ok "created init.lua"
fi

# --- launch ------------------------------------------------------------------

say "Starting Hammerspoon"
if pgrep -x Hammerspoon >/dev/null; then
  # A restart, not a reload: Lua caches loaded modules, and the URL/AppleScript
  # reload hooks aren't enabled by default, so an in-place reload can silently
  # leave the old code running.
  osascript -e 'quit app "Hammerspoon"' >/dev/null 2>&1 || true
  sleep 2
fi
open -a Hammerspoon
sleep 4
ok "running"

# --- report ------------------------------------------------------------------

echo
say "Checking your hardware"
"$BIN_DIR/ddcvol" doctor || true

echo
echo "${bold}Done.${reset}"
echo
echo "  ${dim}Next steps:${reset}"
echo "  1. Grant Hammerspoon Accessibility access when prompted"
echo "     ${dim}System Settings → Privacy & Security → Accessibility${reset}"
echo "  2. Switch audio output to your monitor, then press the volume keys."
echo "  3. ${bold}⌘⌥⌃A${reset} cycles output devices; the 🔈 menubar item picks one."
echo
echo "  ${dim}If the volume keys do nothing, run:  ddcvol doctor${reset}"
