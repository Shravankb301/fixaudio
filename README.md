# Will It DDC?

**Does your monitor's volume work on a Mac? Nobody knows. Let's find out.**

macOS greys out the volume slider when sound goes to your monitor over HDMI or
DisplayPort. Whether you can fix that depends on your exact monitor, your exact
Mac, and which port you plugged into — and nobody documents the combination.

Run the check, post your result, and the next person with your monitor gets an
answer instead of an evening.

```sh
curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash
```

Changes no settings. Installs only a small diagnostic CLI.

**[Browse the compatibility list →](https://shravankb301.github.io/willitddc/)**

---

## Why there's no general answer

Three things decide it, and all three vary:

- **Your monitor's firmware.** DDC/CI volume support is optional and
  inconsistently implemented. Some monitors obey, some ignore the command, and
  some accept writes while returning nonsense on reads.
- **Your Mac's port.** Macs with built-in HDMI convert DisplayPort using an
  MCDP2900 chip, and Apple cuts off the I2C channel DDC needs once the display's
  EDID has been read. This is why
  [MonitorControl disables itself](https://github.com/MonitorControl/MonitorControl/discussions/750)
  on the built-in HDMI port of 2018 Intel Mac minis, all M1 Macs, and the
  entry-level M2 Mac mini.
- **What's in between.** Docks, hubs and KVMs routinely drop DDC even when both
  ends support it.

So "does the Dell U2723QE work" is not a well-formed question. "Does it work on
an M4 Mac mini over built-in HDMI" is, and that's what gets recorded here.

## The case every tool gets wrong

Some monitors accept DDC writes perfectly but lie when asked their current
state. The Samsung CF791 reports the same value for *every* setting and claims
its maximum volume is `-128`.

Most control apps read before they write, so on hardware like this they look
broken even though the monitor is completely controllable. If your check comes
back `reads: broken`, that's the bucket you're in — and it's fixable with a tool
that never reads. There's one in this repo.

## Contributing a report

The whole project is the data. One report takes a minute:

1. Run the check command above.
2. Set your sound output to the monitor and run `m1ddc set volume 20`, then
   `m1ddc set volume 70`. Did it change? That's the part that matters.
3. [Open a report](https://github.com/shravankb301/willitddc/issues/new?template=report.yml)
   and paste the output.

Reports that come back "no, nothing works" are just as valuable as successes.
The data lives in [`data/monitors.json`](data/monitors.json) and the site is
regenerated with `python3 build.py`.

## The fix, if your monitor turns out to be controllable

This repo also ships the write-only volume tool the database was born from. It
restores your keyboard volume keys by writing VCP `0x62` over DDC, caching the
level locally rather than reading it back.

```sh
curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/install.sh | bash
```

| Command | What it does |
| --- | --- |
| `ddcvol up` / `down` | Raise or lower the volume |
| `ddcvol set <0-100>` | Set an absolute level |
| `ddcvol mute` | Toggle mute |
| `ddcvol sync` | Re-push the cached level to the monitor |
| `ddcvol status` | Show the current route and level |
| `ddcvol doctor` | Diagnose DDC support |
| `ddcvol report` | Print a paste-ready report |
| `audioout cycle` | Switch to the next output device |

Volume keys pass straight through to macOS whenever output isn't a DDC display,
so your built-in speakers behave exactly as before. `⌘⌥⌃A` cycles output
devices. Full setup and configuration notes are in [`TOOL.md`](TOOL.md).

## Other tools

If your monitor turns out to work, use whatever you like —
[MonitorControl](https://github.com/MonitorControl/MonitorControl) is free and
excellent, [BetterDisplay](https://github.com/waydabber/BetterDisplay) does far
more and handles HDMI ports MonitorControl won't,
[Lunar](https://lunar.fyi/) and [DisplayBuddy](https://displaybuddy.app) are
polished paid options.

This project isn't trying to replace them. It answers the question they all
leave you to discover by trial and error.

## License

MIT
