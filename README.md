# fixaudio

**Volume keys that work when your Mac says they can't.**

Plug a monitor into a Mac over HDMI or DisplayPort, send audio to its speakers,
and macOS greys out the volume slider. The keyboard volume keys do nothing. Your
only control is the joystick on the back of the monitor.

fixaudio gives the keys back.

```sh
curl -fsSL https://raw.githubusercontent.com/shravankb301/fixaudio/main/install.sh | bash
```

Apple Silicon Macs, macOS 13+.

---

## Why macOS does this

When audio travels over the display cable, macOS treats the volume as the
monitor's business rather than its own, so it disables its own control entirely.
The monitor is still listening, though — most of them accept **DDC/CI** commands
over that same cable. fixaudio writes VCP code `0x62` (audio speaker volume)
directly, and intercepts the media keys to drive it.

## What you get

- **The volume keys work.** F11, F12 and mute, with an on-screen level readout.
- **They still work everywhere else.** When output isn't a monitor, keys pass
  straight through and macOS behaves exactly as it always has.
- **Fast output switching.** `⌘⌥⌃A` cycles devices; a 🔈 menubar item picks one.
- **A CLI**, if you'd rather script it.

## It works on monitors that lie

Plenty of monitors accept DDC writes but return garbage on reads. The Samsung
CF791 this was built for reports the same value for *every* setting, and claims
its maximum volume is `-128`.

Tools that read the current volume before changing it get stuck on hardware like
this. fixaudio never reads. It caches the level locally, per display, and only
ever writes — then re-asserts that level after sleep, input changes, and device
switches, since the monitor won't remember it for you.

## Usage

Mostly you just press the volume keys. Beyond that:

| Command | What it does |
| --- | --- |
| `ddcvol up [step]` | Raise volume (default step 6) |
| `ddcvol down [step]` | Lower volume |
| `ddcvol set <0-100>` | Set an absolute level |
| `ddcvol mute` | Toggle mute |
| `ddcvol sync` | Re-push the cached level to the monitor |
| `ddcvol status` | Show the current route and level |
| `ddcvol doctor` | Diagnose DDC support on your machine |
| `audioout` | Show the current output device |
| `audioout list` | List available outputs |
| `audioout cycle` | Switch to the next output |
| `audioout set <name>` | Switch (a substring works: `audioout set cf`) |

## Configuration

Pass options where the module is loaded, in `~/.hammerspoon/init.lua`:

```lua
require("fixaudio").start({
  step = 4,                                  -- volume change per keypress
  switchHotkey = { { "ctrl" }, "F1" },        -- or false to disable
  menubar = false,                            -- hide the menubar item
  hud = false,                                -- hide the on-screen readout
})
```

The CLI reads `~/.config/fixaudio/config` if it exists:

```sh
FIXAUDIO_STEP=4
FIXAUDIO_DEFAULT_VOLUME=35
```

## How it decides where to send a keypress

On every output-device change, fixaudio asks whether the current audio device
matches a display that `m1ddc` can talk to. That answer is cached, so keypresses
themselves never pay for the lookup.

- **Output is a DDC display** → the key is swallowed and becomes a DDC write.
- **Anything else** → the key is passed through to macOS, untouched.

Rapid repeats are coalesced: one `ddcvol` runs at a time, and presses arriving
mid-flight accumulate into a single follow-up write, so holding a key down
doesn't queue up dozens of DDC round-trips.

## Requirements

Installed for you by `install.sh`:

- [m1ddc](https://github.com/waydabber/m1ddc) — DDC/CI on Apple Silicon
- [switchaudio-osx](https://github.com/deweller/switchaudio-osx) — output switching
- [Hammerspoon](https://www.hammerspoon.org) — media-key interception

Hammerspoon needs **Accessibility** permission to see the volume keys:
System Settings → Privacy & Security → Accessibility.

## Troubleshooting

Start with `ddcvol doctor`. It reports which displays support DDC, which audio
device you're on, the route it picked, and whether your monitor's read channel
is broken (harmless — that's the case fixaudio is built for).

**Volume keys do nothing.** Check `ddcvol status` shows `route: DDC`. If it says
`macOS`, your audio output isn't the monitor. If the route is right, confirm
Hammerspoon has Accessibility permission.

**`ddcvol doctor` finds no DDC displays.** DDC doesn't work over every port on
Apple Silicon. Try a different cable or port — USB-C/DisplayPort is the most
reliable, though the built-in HDMI port works on many machines including the M4
Mac mini.

**Volume jumps back on its own.** The monitor's own buttons move the level
behind fixaudio's back. Run `ddcvol sync`, or use the menubar item's *Re-sync
monitor volume*.

**It stops working after sleep.** It shouldn't — there's a wake handler — but if
a display comes back slowly, `ddcvol sync` fixes it immediately.

## Uninstalling

```sh
./uninstall.sh
```

Leaves Hammerspoon and the Homebrew dependencies in place, in case you use them
for other things.

## Prior art

[MonitorControl](https://github.com/MonitorControl/MonitorControl) is the
well-known app in this space and does far more than this, including brightness.
Try it first — if it works for you, use it. fixaudio exists for the narrower
case where it doesn't: monitors whose DDC reads are unreliable, and people who
want a scriptable CLI rather than an app.

## License

MIT
