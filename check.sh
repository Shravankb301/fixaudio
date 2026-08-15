#!/bin/bash
# Will It DDC? -- find out whether your monitor can be controlled from your Mac.
#
#   curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash
#
# Changes no display settings. Installs m1ddc (a small CLI) only if missing.

set -uo pipefail

bold=$(tput bold 2>/dev/null || true)
dim=$(tput dim 2>/dev/null || true)
green=$(tput setaf 2 2>/dev/null || true)
yellow=$(tput setaf 3 2>/dev/null || true)
red=$(tput setaf 1 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

SUBMIT="https://github.com/shravankb301/willitddc/issues/new?template=report.yml"

echo
echo "${bold}Will It DDC?${reset}  ${dim}checking this Mac and its displays${reset}"
echo

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "${red}This only works on macOS.${reset}"; exit 1
fi

MAC_MODEL="$(sysctl -n hw.model 2>/dev/null || echo unknown)"
CHIP="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
MACOS="$(sw_vers -productVersion 2>/dev/null || echo unknown)"

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "  Mac:   $MAC_MODEL ($CHIP)"
  echo
  echo "${yellow}This check uses m1ddc, which is Apple Silicon only.${reset}"
  echo "Intel Macs can still do DDC via other tools, but this script can't test it."
  exit 1
fi

# --- m1ddc ------------------------------------------------------------------

M1DDC="$(command -v m1ddc || true)"
[[ -z "$M1DDC" && -x /opt/homebrew/bin/m1ddc ]] && M1DDC=/opt/homebrew/bin/m1ddc

if [[ -z "$M1DDC" ]]; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "${red}Needs Homebrew${reset} to install m1ddc. See https://brew.sh"
    exit 1
  fi
  echo "  ${dim}installing m1ddc (small CLI, ~80KB)…${reset}"
  brew install m1ddc >/dev/null 2>&1 || { echo "${red}m1ddc install failed${reset}"; exit 1; }
  M1DDC="$(command -v m1ddc || echo /opt/homebrew/bin/m1ddc)"
fi

# --- probe ------------------------------------------------------------------

DISPLAYS="$("$M1DDC" display list 2>/dev/null | sed -n 's/^\[[0-9]*\] \(.*\) (.*)$/\1/p')"

echo "  Mac:   $MAC_MODEL ($CHIP)"
echo "  macOS: $MACOS"
echo

if [[ -z "$DISPLAYS" ]]; then
  echo "${yellow}No DDC-capable display found.${reset}"
  echo
  echo "That usually means the port, not the monitor. Macs with built-in HDMI"
  echo "convert DisplayPort with a chip whose I2C channel Apple disables in"
  echo "firmware, so DDC often dies there. Try USB-C or DisplayPort instead."
  echo
  echo "Worth reporting anyway - a confirmed 'no' is useful data:"
  echo "  ${bold}$SUBMIT${reset}"
  echo
  cat <<EOF
--- will-it-ddc report ---
mac_model:   $MAC_MODEL
chip:        $CHIP
macos:       $MACOS
display:     none detected
ddc_visible: no
--- end report ---
EOF
  exit 0
fi

echo "${green}DDC-capable display(s) found:${reset}"
echo "$DISPLAYS" | sed 's/^/  • /'
echo

idx=0
while IFS= read -r name; do
  idx=$((idx + 1))
  [[ -z "$name" ]] && continue

  v="$("$M1DDC" display "$idx" get volume 2>/dev/null || echo err)"
  c="$("$M1DDC" display "$idx" get contrast 2>/dev/null || echo err)"
  r="$("$M1DDC" display "$idx" get red 2>/dev/null || echo err)"

  if [[ "$v" == "$c" && "$c" == "$r" ]]; then
    reads="broken"
    verdict="${yellow}reads unreliable${reset} - normal, and fixable with a write-only tool"
  else
    reads="ok"
    verdict="${green}reads look healthy${reset}"
  fi

  echo "${bold}$name${reset}"
  echo "  read channel: $verdict"
  echo "  ${dim}(volume=$v contrast=$c red=$r)${reset}"
  echo

  cat <<EOF
--- will-it-ddc report ---
mac_model:   $MAC_MODEL
chip:        $CHIP
macos:       $MACOS
display:     $name
ddc_visible: yes
reads:       $reads   (volume=$v contrast=$c red=$r)
--- end report ---
EOF
  echo
done < <(echo "$DISPLAYS")

cat <<EOF
${bold}One more step to know for sure.${reset}
Reads being broken doesn't tell us whether writes work - and writes are what
actually matters. Set your Mac's sound output to the monitor, then run:

  ${bold}m1ddc set volume 20${reset}     ${dim}# listen${reset}
  ${bold}m1ddc set volume 70${reset}     ${dim}# louder?${reset}

If the volume changed, your monitor is controllable.

${bold}Please post your result:${reset}
  $SUBMIT

It takes a minute and it's the only way the next person with your monitor
gets an answer.
EOF
echo
