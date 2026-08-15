#!/bin/bash
# Will It DDC? -- find out whether your monitor can be controlled from your Mac.
#
#   curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash
#
# Detects DDC support, checks whether the monitor's read channel is honest, and
# -- with your permission -- actually tests whether writes land, because that's
# the part that decides the answer and nothing else measures it for you.

set -uo pipefail

bold=$(tput bold 2>/dev/null || true)
dim=$(tput dim 2>/dev/null || true)
green=$(tput setaf 2 2>/dev/null || true)
yellow=$(tput setaf 3 2>/dev/null || true)
red=$(tput setaf 1 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

SUBMIT="https://github.com/shravankb301/willitddc/issues/new?template=report.yml"

# Piped through `curl | bash`, stdin is the script itself -- prompts have to
# read the keyboard directly or they'd silently eat the rest of the script.
TTY=/dev/tty
# `[[ -r /dev/tty ]]` only checks permissions and still passes when there is no
# controlling terminal, so actually try to open it.
have_tty() { { : < "$TTY"; } 2>/dev/null; }

ask() {
  local prompt="$1" ans=""
  have_tty || return 2
  printf '%s' "$prompt" > "$TTY"
  read -r ans < "$TTY" || return 2
  case "$ans" in [yY]*) return 0 ;; [nN]*) return 1 ;; *) return 2 ;; esac
}

echo
echo "${bold}Will It DDC?${reset}  ${dim}checking this Mac and its displays${reset}"
echo

[[ "$(uname -s)" == "Darwin" ]] || { echo "${red}macOS only.${reset}"; exit 1; }

MAC_MODEL="$(sysctl -n hw.model 2>/dev/null || echo unknown)"
# The identifier (Mac16,10) is stable but unreadable; the marketing name is
# what people recognise, and what keeps one machine from being recorded twice.
MAC_NAME="$(system_profiler SPHardwareDataType 2>/dev/null | sed -n 's/ *Model Name: *//p' | head -1)"
MAC_NAME="${MAC_NAME:-$MAC_MODEL}"
CHIP="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
MACOS="$(sw_vers -productVersion 2>/dev/null || echo unknown)"

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "  Mac:   $MAC_MODEL ($CHIP)"
  echo
  echo "${yellow}This check uses m1ddc, which is Apple Silicon only.${reset}"
  echo "Intel Macs can do DDC through other tools (ddcctl), but this script"
  echo "can't test it. Support for that is an open issue."
  exit 1
fi

# --- m1ddc ------------------------------------------------------------------

M1DDC="$(command -v m1ddc || true)"
[[ -z "$M1DDC" && -x /opt/homebrew/bin/m1ddc ]] && M1DDC=/opt/homebrew/bin/m1ddc

if [[ -z "$M1DDC" ]]; then
  command -v brew >/dev/null 2>&1 || {
    echo "${red}Needs Homebrew${reset} to install m1ddc. See https://brew.sh"; exit 1; }
  echo "  ${dim}installing m1ddc (small CLI, ~80KB)…${reset}"
  brew install m1ddc >/dev/null 2>&1 || { echo "${red}m1ddc install failed${reset}"; exit 1; }
  M1DDC="$(command -v m1ddc || echo /opt/homebrew/bin/m1ddc)"
fi

# --- discover ----------------------------------------------------------------

DISPLAYS="$("$M1DDC" display list 2>/dev/null | sed -n 's/^\[[0-9]*\] \(.*\) (.*)$/\1/p')"

echo "  Mac:   $MAC_MODEL ($CHIP)"
echo "  macOS: $MACOS"
echo

emit_report() {
  cat <<EOF
--- will-it-ddc report ---
mac_name:    $MAC_NAME
mac_model:   $MAC_MODEL
chip:        $CHIP
macos:       $MACOS
display:     $1
ddc_visible: $2
reads:       $3
writes:      $4
volume:      $5
--- end report ---
EOF
}

if [[ -z "$DISPLAYS" ]]; then
  echo "${yellow}No DDC-capable display found.${reset}"
  echo
  echo "That usually points at the port rather than the monitor. Macs with"
  echo "built-in HDMI convert DisplayPort with a chip whose I2C channel Apple"
  echo "disables in firmware, so DDC often dies there. Try USB-C or DisplayPort."
  echo
  echo "A confirmed 'no' is still useful data:"
  echo "  ${bold}$SUBMIT${reset}"
  echo
  emit_report "none detected" "no" "n/a" "n/a" "n/a"
  exit 0
fi

echo "${green}DDC-capable display(s) found:${reset}"
echo "$DISPLAYS" | sed 's/^/  • /'
echo

# --- per display -------------------------------------------------------------

idx=0
while IFS= read -r NAME; do
  idx=$((idx + 1))
  [[ -z "$NAME" ]] && continue
  D=("$M1DDC" display "$idx")

  v="$("${D[@]}" get volume 2>/dev/null || echo err)"
  c="$("${D[@]}" get contrast 2>/dev/null || echo err)"
  r="$("${D[@]}" get red 2>/dev/null || echo err)"

  if [[ "$v" == "$c" && "$c" == "$r" ]]; then
    READS="broken"
    read_note="${yellow}unreliable${reset} — normal, and fixable with a write-only tool"
  else
    READS="ok"
    read_note="${green}healthy${reset}"
  fi

  echo "${bold}$NAME${reset}"
  echo "  read channel: $read_note"
  echo "  ${dim}(volume=$v contrast=$c red=$r)${reset}"
  echo

  WRITES="untested"
  VOLUME="untested"

  # --- write test ------------------------------------------------------------
  #
  # Reads tell us nothing about writes, and writes are what decide the answer.
  # Brightness is the honest probe: unambiguous, instant, and doesn't require
  # rerouting your audio.

  if ! have_tty; then
    echo "  ${dim}(no terminal available — skipping the write test)${reset}"
    echo
  else
    echo "  ${bold}Write test.${reset} Reads and writes are separate channels, so the only"
    echo "  way to know is to try. This briefly dims the screen, then puts it back."
    if [[ "$READS" == "broken" ]]; then
      echo "  ${yellow}Your monitor doesn't report its brightness honestly, so it will be${reset}"
      echo "  ${yellow}restored to 75 rather than its exact previous value.${reset}"
      ORIG=75
    else
      ORIG="$("${D[@]}" get luminance 2>/dev/null || echo 75)"
      [[ "$ORIG" =~ ^[0-9]+$ ]] || ORIG=75
    fi
    echo

    if ask "  Run it? [y/N] "; then
      "${D[@]}" set luminance 15 >/dev/null 2>&1
      sleep 1.2
      "${D[@]}" set luminance "$ORIG" >/dev/null 2>&1
      echo
      if ask "  Did the screen dim and come back? [y/n] "; then
        WRITES="works"
        echo "  ${green}Writes work.${reset} Your monitor is controllable."
      else
        WRITES="no"
        echo "  ${yellow}No visible change — DDC writes don't appear to reach this display.${reset}"
      fi
    else
      echo "  ${dim}skipped${reset}"
    fi
    echo

    # Volume rides a different VCP code, so a working brightness write doesn't
    # guarantee it. Only worth asking if writes got through at all.
    if [[ "$WRITES" == "works" ]]; then
      echo "  ${bold}Volume test.${reset} Volume is a separate command, so it can fail even"
      echo "  when brightness works. Set your Mac's sound output to this monitor first."
      echo
      if ask "  Output set to the monitor and ready? [y/N] "; then
        "${D[@]}" set volume 15 >/dev/null 2>&1; sleep 0.5
        afplay /System/Library/Sounds/Ping.aiff 2>/dev/null
        sleep 0.4
        "${D[@]}" set volume 65 >/dev/null 2>&1; sleep 0.5
        afplay /System/Library/Sounds/Ping.aiff 2>/dev/null
        echo
        if ask "  Was the second beep louder? [y/n] "; then
          VOLUME="works"
          echo "  ${green}Volume control works.${reset}"
        else
          VOLUME="no"
          echo "  ${yellow}Volume didn't respond, even though brightness did.${reset}"
        fi
        "${D[@]}" set volume 35 >/dev/null 2>&1
      else
        echo "  ${dim}skipped${reset}"
      fi
      echo
    fi
  fi

  # --- grade -----------------------------------------------------------------
  #
  # Two axes people actually care about: does it tell the truth about itself,
  # and does it do what it's told. Grades come strictly from what we measured,
  # and stay ungraded when we didn't measure enough to be fair.

  if [[ "$WRITES" == "untested" ]]; then
    GRADE="?"; TAG="Not enough tested to grade."
  elif [[ "$WRITES" == "no" ]]; then
    GRADE="D"; TAG="Answers the door, refuses to move."
  elif [[ "$VOLUME" == "no" ]]; then
    GRADE="C"; TAG="Takes orders, except the one you wanted."
  elif [[ "$VOLUME" == "works" && "$READS" == "broken" ]]; then
    GRADE="B"; TAG="Does what it's told, lies about everything."
  elif [[ "$VOLUME" == "works" ]]; then
    GRADE="A"; TAG="Obeys, and tells the truth."
  else
    GRADE="?"; TAG="Volume untested."
  fi

  mark() { [[ "$1" == "$2" ]] && printf '[ok]' || printf '[no]'; }
  honest() { [[ "$READS" == "ok" ]] && printf '[ok]' || printf '[no]'; }

  echo "  ${bold}Grade: $GRADE${reset} — $TAG"
  echo

  # --- the card ---------------------------------------------------------------
  #
  # Plain text on purpose. This is what gets pasted into a Reddit comment or an
  # HN thread, and text survives every one of those. An image would not.

  echo "${bold}Copy this — it's the whole report, and it's how anyone else finds out:${reset}"
  echo
  cat <<EOF
Will It DDC?  —  $NAME
$MAC_MODEL · $CHIP · macOS $MACOS

  Responds    [ok]
  Honest      $(honest)
  Obeys       $(mark "$WRITES" works)
  Volume      $(mark "$VOLUME" works)

  GRADE: $GRADE — $TAG

shravankb301.github.io/willitddc
EOF
  echo

  emit_report "$NAME" "yes" "$READS   (volume=$v contrast=$c red=$r)" "$WRITES" "$VOLUME"
  echo
done < <(echo "$DISPLAYS")

cat <<EOF
${bold}Please post your result:${reset}
  $SUBMIT

It takes a minute, and it's the only way the next person with your monitor
gets an answer instead of an evening.
EOF
echo
