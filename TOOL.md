# The volume tool

The write-only DDC volume control that this project grew out of. Use it if
[your check](README.md) came back showing a controllable monitor — especially if
it reported `reads: broken`, which is the case other tools handle badly.

```sh
curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/install.sh | bash
```

Apple Silicon, macOS 13+.

## What it does

macOS disables its own volume control whenever audio is routed over a display
cable. This writes VCP code `0x62` (audio speaker volume) directly to the
monitor over DDC/CI and intercepts your media keys to drive it.

Crucially it **never reads**. The level is cached locally, per display, and only
ever written — then re-asserted after sleep, input changes and device switches,
since the monitor won't remember it for you and its own buttons will move it
behind your back.

## Usage

| Command | What it does |
| --- | --- |
| `ddcvol up [step]` | Raise volume (default step 6) |
| `ddcvol down [step]` | Lower volume |
| `ddcvol set <0-100>` | Set an absolute level |
| `ddcvol mute` | Toggle mute |
| `ddcvol sync` | Re-push the cached level to the monitor |
| `ddcvol status` | Show the current route and level |
| `ddcvol doctor` | Diagnose DDC support on this machine |
| `ddcvol report` | Print a paste-ready compatibility report |
| `audioout` | Show the current output device |
| `audioout list` | List available outputs |
| `audioout cycle` | Switch to the next output |
| `audioout set <name>` | Switch (a substring works: `audioout set cf`) |

`⌘⌥⌃A` cycles output devices, and a 🔈 menubar item picks one directly.

## How it decides where to send a keypress

On every output-device change it asks whether the current audio device matches a
display `m1ddc` can talk to, and caches the answer — so keypresses never pay for
the lookup.

- **Output is a DDC display** → the key is swallowed and becomes a DDC write.
- **Anything else** → the key passes through to macOS, untouched.

Rapid repeats are coalesced: one `ddcvol` runs at a time, and presses arriving
mid-flight accumulate into a single follow-up write, so holding a key down
doesn't queue up dozens of DDC round-trips.

## Configuration

In `~/.hammerspoon/init.lua`:

```lua
require("fixaudio").start({
  step = 4,                            -- volume change per keypress
  switchHotkey = { { "ctrl" }, "F1" },  -- or false to disable
  menubar = false,                      -- hide the menubar item
  hud = false,                          -- hide the on-screen readout
})
```

The CLI reads `~/.config/fixaudio/config` if present:

```sh
FIXAUDIO_STEP=4
FIXAUDIO_DEFAULT_VOLUME=35
```

## Requirements

Installed for you by `install.sh`:

- [m1ddc](https://github.com/waydabber/m1ddc) — DDC/CI on Apple Silicon
- [switchaudio-osx](https://github.com/deweller/switchaudio-osx) — output switching
- [Hammerspoon](https://www.hammerspoon.org) — media-key interception

Hammerspoon needs **Accessibility** permission to see the volume keys:
System Settings → Privacy & Security → Accessibility.

## Troubleshooting

Start with `ddcvol doctor`.

**Volume keys do nothing.** Check `ddcvol status` shows `route: DDC`. If it says
`macOS`, your audio output isn't the monitor. If the route is right, confirm
Hammerspoon has Accessibility permission.

**`ddcvol doctor` finds no DDC displays.** DDC doesn't work over every port on
Apple Silicon. Try a different cable or port — USB-C and DisplayPort are the
most reliable.

**Volume jumps back on its own.** The monitor's own buttons moved it. Run
`ddcvol sync`, or use the menubar item's *Re-sync monitor volume*.

**It stops working after sleep.** There's a wake handler, but if a display comes
back slowly, `ddcvol sync` fixes it immediately.

## Uninstalling

```sh
./uninstall.sh
```

Leaves Hammerspoon and the Homebrew dependencies in place, in case you use them
for other things.
