#!/bin/bash
# Removes fixaudio. Leaves Homebrew dependencies and Hammerspoon alone, since
# you may be using them for other things.

set -euo pipefail

BIN_DIR="${FIXAUDIO_BIN_DIR:-$HOME/.local/bin}"
HS_DIR="$HOME/.hammerspoon"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/fixaudio"

for tool in ddcvol audioout; do
  for dir in "$BIN_DIR" /usr/local/bin /opt/homebrew/bin; do
    [[ -e "$dir/$tool" ]] && rm -f "$dir/$tool" && echo "removed $dir/$tool"
  done
done

rm -rf "$HS_DIR/fixaudio" && echo "removed $HS_DIR/fixaudio"
rm -rf "$STATE_DIR" && echo "removed $STATE_DIR"

if [[ -f "$HS_DIR/init.lua" ]] && grep -q 'require("fixaudio")' "$HS_DIR/init.lua"; then
  echo
  echo "One manual step: remove this line from $HS_DIR/init.lua"
  echo '    require("fixaudio").start()'
fi

echo
echo "Dependencies left installed. To remove them too:"
echo "    brew uninstall m1ddc switchaudio-osx"
echo "    brew uninstall --cask hammerspoon"
